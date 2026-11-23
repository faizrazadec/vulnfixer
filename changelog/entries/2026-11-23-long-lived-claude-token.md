---
date: 2026-11-23
area: operations
kind: changed
---

# The agent authenticates with a long-lived Claude token

Scheduled runs used the browser login stored in the `claude-auth` volume. That login
expires and cannot renew itself unattended, so a run would fail on every project within
seconds until someone logged in by hand. The agent now reads `CLAUDE_CODE_OAUTH_TOKEN`
from `.env`, a subscription token made once with `claude setup-token` that lasts about a
year. The browser login stays as a fallback. Renew the token before it expires.

- Docs: [README](../../README.md)
