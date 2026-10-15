---
date: 2026-10-15
area: deployment
kind: changed
---

# The agent is now named vulnfixer

The repository, Docker service, image, container, network and verify image namespace
are now all named `vulnfixer`, and `compose.yml` pins the project name so the volumes
are `vulnfixer_*` wherever the repo is checked out. Switching an existing deployment
over means copying the old `vuln-fix-agent_*` volumes first, or the agent starts
without its Claude login, state or SSH keys. The steps are in the PR.

- PR: [#1](https://github.com/faizrazadec/vulnfixer/pull/1)
- Docs: [README](../../README.md)
