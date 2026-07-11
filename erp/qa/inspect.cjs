#!/usr/bin/env node
/*
 * Playwright-driven page inspector used by the qa-bug-hunter agent.
 *
 * Setup: run `npm install` in this directory once (installs the `playwright`
 * package; also run `npx playwright install chromium` if no browser is
 * present on the machine). Then:
 *
 *   node erp/qa/inspect.cjs --url <url>
 *
 * If playwright is already installed globally instead of locally, point
 * Node at it with NODE_PATH, e.g.:
 *
 *   NODE_PATH=$(npm root -g) node erp/qa/inspect.cjs --url <url>
 *
 * Usage:
 *   node inspect.cjs --url <url>
 *     [--out <result.json>]          default: ./qa-result.json
 *     [--screenshot-dir <dir>]       default: ./qa-screenshots
 *     [--steps <steps.json>]         array of interaction steps, see below
 *     [--dump-elements]              list interactive elements on the page
 *     [--check-links]                probe same-origin links for HTTP errors
 *     [--max-links <n>]              default: 25
 *     [--timeout <ms>]               default: 20000
 *
 * steps.json format:
 *   [
 *     { "action": "click", "selector": "#submit", "description": "submit form" },
 *     { "action": "fill", "selector": "input[name=email]", "value": "a@b.com" },
 *     { "action": "expectText", "selector": ".toast", "value": "Saved" }
 *   ]
 *   Supported actions: goto, click, fill, check, uncheck, selectOption, press,
 *   hover, waitForSelector, expectText, expectVisible, expectURL.
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

function parseArgs(argv) {
  const args = { screenshotDir: 'qa-screenshots', out: 'qa-result.json', maxLinks: 25, timeout: 20000 };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    const next = () => argv[++i];
    switch (a) {
      case '--url': args.url = next(); break;
      case '--out': args.out = next(); break;
      case '--screenshot-dir': args.screenshotDir = next(); break;
      case '--steps': args.steps = next(); break;
      case '--dump-elements': args.dumpElements = true; break;
      case '--check-links': args.checkLinks = true; break;
      case '--max-links': args.maxLinks = parseInt(next(), 10); break;
      case '--timeout': args.timeout = parseInt(next(), 10); break;
      default:
        console.error(`Unknown argument: ${a}`);
        process.exit(2);
    }
  }
  if (!args.url) {
    console.error('Usage: node inspect.cjs --url <url> [options]');
    process.exit(2);
  }
  return args;
}

async function dumpElements(page) {
  return page.evaluate(() => {
    const describe = (el) => ({
      tag: el.tagName.toLowerCase(),
      text: (el.innerText || el.value || '').trim().slice(0, 80),
      id: el.id || null,
      name: el.getAttribute('name'),
      href: el.getAttribute('href'),
      type: el.getAttribute('type'),
      selector: el.id
        ? `#${el.id}`
        : el.getAttribute('data-testid')
        ? `[data-testid="${el.getAttribute('data-testid')}"]`
        : null,
      disabled: !!el.disabled,
    });
    const sel = 'button, a[href], input, select, textarea, form, [role="button"]';
    return Array.from(document.querySelectorAll(sel)).map(describe);
  });
}

async function runStep(page, step, result) {
  const timeout = step.timeout || 5000;
  try {
    switch (step.action) {
      case 'goto':
        await page.goto(step.value, { waitUntil: 'load', timeout });
        break;
      case 'click':
        await page.click(step.selector, { timeout });
        break;
      case 'fill':
        await page.fill(step.selector, step.value ?? '', { timeout });
        break;
      case 'check':
        await page.check(step.selector, { timeout });
        break;
      case 'uncheck':
        await page.uncheck(step.selector, { timeout });
        break;
      case 'selectOption':
        await page.selectOption(step.selector, step.value, { timeout });
        break;
      case 'press':
        await page.press(step.selector, step.value, { timeout });
        break;
      case 'hover':
        await page.hover(step.selector, { timeout });
        break;
      case 'waitForSelector':
        await page.waitForSelector(step.selector, { timeout });
        break;
      case 'expectText': {
        const text = await page.textContent(step.selector, { timeout });
        if (!text || !text.includes(step.value)) {
          throw new Error(`expected text "${step.value}" in ${step.selector}, got "${text}"`);
        }
        break;
      }
      case 'expectVisible':
        await page.waitForSelector(step.selector, { state: 'visible', timeout });
        break;
      case 'expectURL':
        await page.waitForURL(step.value, { timeout });
        break;
      default:
        throw new Error(`unknown action: ${step.action}`);
    }
    return { ...step, ok: true };
  } catch (err) {
    return { ...step, ok: false, error: err.message };
  } finally {
    await page.waitForTimeout(150);
  }
}

async function checkLinks(page, baseUrl, maxLinks) {
  const origin = new URL(baseUrl).origin;
  const hrefs = await page.evaluate(() =>
    Array.from(document.querySelectorAll('a[href]')).map((a) => a.href)
  );
  const sameOrigin = [...new Set(hrefs.filter((h) => {
    try { return new URL(h).origin === origin; } catch { return false; }
  }))].slice(0, maxLinks);

  const results = [];
  for (const link of sameOrigin) {
    try {
      const resp = await page.request.get(link, { timeout: 8000 });
      results.push({ url: link, status: resp.status(), ok: resp.status() < 400 });
    } catch (err) {
      results.push({ url: link, status: null, ok: false, error: err.message });
    }
  }
  return results;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  fs.mkdirSync(args.screenshotDir, { recursive: true });

  const browser = await chromium.launch({ channel: 'chromium' });
  const page = await browser.newPage();

  const consoleErrors = [];
  const consoleWarnings = [];
  const pageErrors = [];
  const failedRequests = [];
  const httpErrors = [];

  page.on('console', (m) => {
    if (m.type() === 'error') consoleErrors.push(m.text());
    if (m.type() === 'warning') consoleWarnings.push(m.text());
  });
  page.on('pageerror', (err) => pageErrors.push(err.message));
  page.on('requestfailed', (req) => {
    failedRequests.push({ url: req.url(), method: req.method(), error: req.failure()?.errorText });
  });
  page.on('response', (resp) => {
    if (resp.status() >= 400) {
      httpErrors.push({ url: resp.url(), status: resp.status() });
    }
  });

  const result = { url: args.url, timestamp: new Date().toISOString() };
  const screenshots = [];

  try {
    await page.goto(args.url, { waitUntil: 'load', timeout: args.timeout });
    result.title = await page.title();
  } catch (err) {
    result.navigationError = err.message;
  }

  const initialShot = path.join(args.screenshotDir, '00-initial.png');
  await page.screenshot({ path: initialShot, fullPage: true }).catch(() => {});
  screenshots.push(initialShot);

  if (args.dumpElements) {
    result.elements = await dumpElements(page).catch((err) => ({ error: err.message }));
  }

  if (args.steps) {
    const steps = JSON.parse(fs.readFileSync(args.steps, 'utf8'));
    const stepResults = [];
    for (let i = 0; i < steps.length; i++) {
      const stepResult = await runStep(page, steps[i], result);
      stepResults.push(stepResult);
      const shot = path.join(args.screenshotDir, `${String(i + 1).padStart(2, '0')}-${steps[i].action}.png`);
      await page.screenshot({ path: shot, fullPage: true }).catch(() => {});
      screenshots.push(shot);
    }
    result.steps = stepResults;
  }

  if (args.checkLinks) {
    result.brokenLinks = (await checkLinks(page, args.url, args.maxLinks)).filter((l) => !l.ok);
    result.linksChecked = args.maxLinks;
  }

  await browser.close();

  result.consoleErrors = consoleErrors;
  result.consoleWarnings = consoleWarnings;
  result.pageErrors = pageErrors;
  result.failedRequests = failedRequests;
  result.httpErrors = httpErrors;
  result.screenshots = screenshots;

  fs.writeFileSync(args.out, JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
}

main().catch((err) => {
  console.error('FATAL', err);
  process.exit(1);
});
