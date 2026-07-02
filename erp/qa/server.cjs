#!/usr/bin/env node
/*
 * Standalone local web UI for the QA bug-detection tool.
 *
 * Runs entirely separately from the Compliance ERP app (which uses ports
 * 3000/8000/5432/6379) so the two never collide on the same machine.
 * Default port is 4400, override with QA_PORT.
 *
 * Setup (once): cd erp/qa && npm install
 * Run:          node erp/qa/server.cjs
 * Then open:    http://localhost:4400
 */

const http = require('http');
const path = require('path');
const fs = require('fs');
const crypto = require('crypto');
const { spawn } = require('child_process');

const PORT = process.env.QA_PORT || 4400;
const RUNS_DIR = path.join(__dirname, '.qa-runs');
fs.mkdirSync(RUNS_DIR, { recursive: true });

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function layout(body) {
  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>QA Bug Detection</title>
<style>
  body { font-family: -apple-system, system-ui, sans-serif; max-width: 860px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; background: #fafafa; }
  h1 { font-size: 1.4rem; }
  form { display: flex; gap: 8px; margin: 20px 0; }
  input[type=url] { flex: 1; padding: 10px 12px; font-size: 1rem; border: 1px solid #ccc; border-radius: 6px; }
  button { padding: 10px 18px; font-size: 1rem; border: none; border-radius: 6px; background: #2563eb; color: white; cursor: pointer; }
  button:hover { background: #1d4ed8; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
  .ok { background: #dcfce7; color: #166534; }
  .bad { background: #fee2e2; color: #991b1b; }
  .warn { background: #fef9c3; color: #854d0e; }
  section { background: white; border: 1px solid #e5e5e5; border-radius: 8px; padding: 16px; margin: 16px 0; }
  ul { margin: 6px 0; padding-left: 20px; }
  code { background: #f1f1f1; padding: 1px 5px; border-radius: 4px; font-size: 0.85em; }
  .shots { display: flex; flex-wrap: wrap; gap: 10px; }
  .shots img { max-width: 220px; border: 1px solid #ddd; border-radius: 4px; }
  .err { color: #991b1b; }
  footer { color: #888; font-size: 0.8rem; margin-top: 30px; }
</style>
</head>
<body>
<h1>QA Bug Detection</h1>
<p>Paste a URL and I'll drive a headless browser against it: page load errors, broken same-origin links, and interactive elements found on the page.</p>
<form method="POST" action="/run">
  <input type="url" name="url" placeholder="https://example.com" required>
  <button type="submit">Run</button>
</form>
${body}
<footer>Runs on its own port (${PORT}), independent of the Compliance ERP app.</footer>
</body>
</html>`;
}

function renderResult(runId, result, code, stderr) {
  if (code !== 0 || !result) {
    return `<section><p class="err"><strong>Scan failed</strong> (exit code ${code})</p><pre>${escapeHtml(stderr || 'no output')}</pre></section>`;
  }

  const list = (title, items, cls) =>
    items && items.length
      ? `<section><h3>${title} <span class="badge ${cls}">${items.length}</span></h3><ul>${items
          .map((i) => `<li><code>${escapeHtml(typeof i === 'string' ? i : JSON.stringify(i))}</code></li>`)
          .join('')}</ul></section>`
      : `<section><h3>${title} <span class="badge ok">0</span></h3></section>`;

  const shots = (result.screenshots || [])
    .map((p) => `/shots/${runId}/${encodeURIComponent(path.basename(p))}`)
    .map((src) => `<img src="${src}">`)
    .join('');

  return `
${result.navigationError ? `<section><p class="err"><strong>Navigation error:</strong> ${escapeHtml(result.navigationError)}</p></section>` : ''}
<section><p><strong>Page:</strong> ${escapeHtml(result.title || '(no title)')} &mdash; <code>${escapeHtml(result.url)}</code></p></section>
${list('Console errors', result.consoleErrors, 'bad')}
${list('Uncaught JS errors', result.pageErrors, 'bad')}
${list('Failed network requests', (result.failedRequests || []).map((r) => `${r.method} ${r.url} — ${r.error}`), 'bad')}
${list('HTTP error responses', (result.httpErrors || []).map((r) => `${r.status} ${r.url}`), 'warn')}
${list('Broken same-origin links', (result.brokenLinks || []).map((l) => `${l.status ?? 'ERR'} ${l.url}`), 'bad')}
${shots ? `<section><h3>Screenshots</h3><div class="shots">${shots}</div></section>` : ''}
`;
}

function runInspect(targetUrl) {
  return new Promise((resolve) => {
    const runId = crypto.randomUUID();
    const dir = path.join(RUNS_DIR, runId);
    fs.mkdirSync(dir, { recursive: true });
    const outFile = path.join(dir, 'result.json');
    const args = [
      path.join(__dirname, 'inspect.cjs'),
      '--url', targetUrl,
      '--out', outFile,
      '--screenshot-dir', dir,
      '--dump-elements',
      '--check-links',
    ];
    const child = spawn(process.execPath, args, { cwd: __dirname });
    let stderr = '';
    child.stderr.on('data', (d) => { stderr += d; });
    child.on('error', (err) => resolve({ runId, code: -1, stderr: err.message, result: null }));
    child.on('close', (code) => {
      let result = null;
      try { result = JSON.parse(fs.readFileSync(outFile, 'utf8')); } catch { /* left null */ }
      resolve({ runId, code, stderr, result });
    });
    setTimeout(() => child.kill('SIGKILL'), 45000);
  });
}

const server = http.createServer(async (req, res) => {
  const reqUrl = new URL(req.url, `http://localhost:${PORT}`);

  if (req.method === 'GET' && reqUrl.pathname === '/') {
    res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    res.end(layout(''));
    return;
  }

  if (req.method === 'POST' && reqUrl.pathname === '/run') {
    let body = '';
    req.on('data', (c) => { body += c; });
    req.on('end', async () => {
      const target = new URLSearchParams(body).get('url') || '';
      try {
        const parsed = new URL(target);
        if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('unsupported protocol');
      } catch {
        res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
        res.end(layout(`<section><p class="err">Invalid URL: ${escapeHtml(target)}</p></section>`));
        return;
      }
      const { runId, result, code, stderr } = await runInspect(target);
      res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
      res.end(layout(renderResult(runId, result, code, stderr)));
    });
    return;
  }

  if (req.method === 'GET' && reqUrl.pathname.startsWith('/shots/')) {
    const parts = reqUrl.pathname.split('/').filter(Boolean); // ['shots', runId, file]
    const runsRoot = path.resolve(RUNS_DIR) + path.sep;
    const filePath = parts.length === 3 ? path.resolve(RUNS_DIR, parts[1], parts[2]) : null;
    if (!filePath || !filePath.startsWith(runsRoot) || !fs.existsSync(filePath)) {
      res.writeHead(404); res.end('not found');
      return;
    }
    res.writeHead(200, { 'content-type': 'image/png' });
    fs.createReadStream(filePath).pipe(res);
    return;
  }

  res.writeHead(404, { 'content-type': 'text/plain' });
  res.end('not found');
});

server.listen(PORT, () => {
  console.log(`QA bug-detection UI running at http://localhost:${PORT}`);
  console.log(`(independent of the Compliance ERP app's ports 3000/8000/5432/6379)`);
});
