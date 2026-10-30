---
date: 2026-10-30
area: security
kind: security
---

# Project code no longer runs with the agent's credentials

A project's test suite read the agent's Slack webhook from the environment and posted test
messages to the team channel. Every install, test, build, server and `docker build`/`run`
the agent starts now goes through `project-run`, which removes the agent's Slack, GitHub,
Vanta, Linear and SSH credentials from that process, by name and by value. A guard refuses
project commands that are not wrapped. The agent's own environment is unchanged.

- PR: [#4](https://github.com/faizrazadec/vulnfixer/pull/4)
- Docs: [README](../../README.md)
