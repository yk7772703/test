---
name: qa-review
description: Run the two-agent QA workflow (qa-bug-hunter then qa-bug-fixer) against a URL the user provides — tests the live page and its functionality, then fixes what's found. Use when the user gives a link and asks to check/test/QA the web page, find bugs, or fix issues on it.
---

# QA review workflow

Argument: a URL (and optionally which flows/pages to focus on).

1. If no URL was given in the invocation, ask the user for the link to test
   (and, if useful, what functionality matters most — login, checkout,
   settings, etc.).
2. Spawn the `qa-bug-hunter` agent (Agent tool, subagent_type: qa-bug-hunter)
   with the URL and any focus areas. It will drive a real browser against
   the page and return a Markdown bug report. It makes no code changes.
3. Show the user a short summary of what was found (or that nothing was
   found) before fixing anything, in case they want to redirect scope.
4. If there are bugs and the user wants them fixed, spawn the `qa-bug-fixer`
   agent (subagent_type: qa-bug-fixer) with the full bug report. It will
   locate root causes and apply minimal fixes, verifying with the project's
   build/lint/tests.
5. Report back: what was found, what was fixed (with files changed), and
   anything left unfixed and why. Do not commit or push unless the user
   asks.

Note: the target URL must actually be reachable from this environment's
network policy. If navigation fails with a network/proxy error rather than
an HTTP error, that's an environment limitation, not a bug — say so instead
of treating it as a defect.
