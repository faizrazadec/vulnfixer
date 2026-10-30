"""Project code must never run with the agent's credentials in its environment.

A repo's test suite once found SLACK_WEBHOOK_URL in the agent's environment and posted
test messages to the team channel. Two pieces stop that, and both are tested here:
bin/project-run strips the credentials, and main._guard_project_env refuses project
commands that are not run through it.

Run: uv run python tests/test_guard.py
"""

import asyncio
import os
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "app"))
import main  # noqa: E402

BIN = pathlib.Path(__file__).resolve().parent.parent / "app" / "bin"

BLOCK = [
    "pytest -q", "cd /w/x && pytest", "python -m pytest tests -n 2", "python3 manage.py test",
    "uv run pytest", "uv sync --frozen", "uv lock", "pip install -r requirements.txt",
    "pnpm install --frozen-lockfile", "npm ci", "npm test", "npm run build", "yarn test",
    "NODE_OPTIONS=--max-old-space-size=2048 pnpm --filter @x/web exec vitest run",
    "nohup pytest > run.log 2>&1 &", "timeout 900 make test", "bash -c 'cd web && yarn test'",
    "docker build -t vulnfixer-verify/p:fixed .", "DOCKER_BUILDKIT=0 docker build .",
    "docker buildx build .", "docker run --rm img pytest", "docker compose up -d",
    "go test ./...", "cargo test", "./gradlew test", "uvicorn app:app",
]
ALLOW = [
    "project-run pytest -q", "project-run --with-package-token pnpm install",
    "cd /w && project-run sh -c 'pnpm test'", "nohup project-run pytest > run.log 2>&1 &",
    "git status && git log -1", "gh api repos/a/b/pulls", "slack-notify done",
    "vanta-findings p --json | python3 -c 'import json,sys;print(1)'",
    "linear-ticket create p --kind fix", "vuln-ledger p tickets --open",
    "trivy fs --exit-code 1 .", "docker images", "docker rmi -f x", "docker buildx version",
    "npm view next versions", "pnpm why katex", "uv export --frozen", "grep -rn pytest .",
    "cat package.json", "python3 /tmp/helper.py", "ls; echo ok",
]


def test_guard_blocks_unwrapped_project_code():
    wrong = [c for c in BLOCK if not main._project_command_violation(c)]
    assert not wrong, f"should be blocked: {wrong}"
    wrong = [(c, main._project_command_violation(c)) for c in ALLOW
             if main._project_command_violation(c)]
    assert not wrong, f"should be allowed: {wrong}"
    print(f"guard: {len(BLOCK)} unwrapped project commands blocked, {len(ALLOW)} others allowed")


def test_hook_denies_with_a_retry_hint():
    out = asyncio.run(main._guard_project_env({"tool_input": {"command": "pnpm test"}}, "t", None))
    h = out["hookSpecificOutput"]
    assert h["permissionDecision"] == "deny" and "project-run" in h["permissionDecisionReason"], out
    assert asyncio.run(main._guard_project_env({"tool_input": {"command": "git status"}}, "t", None)) == {}
    print("hook denies with a project-run hint, passes everything else through")


def test_project_run_strips_secrets_by_name_and_value():
    env = {
        "PATH": os.environ["PATH"], "HOME": "/tmp", "VULN_FIX_RUN": "task123",
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/T0/B0/secretsecret",
        "GH_TOKEN": "ghp_agenttoken_1234567890", "LINEAR_API_KEY": "lin_api_abcdefghijkl",
        "VANTA_CLIENT_SECRET": "vcs_abcdefghijklmn", "SSH_AUTH_SOCK": "/tmp/ssh-x/agent.1",
        "NODE_AUTH_TOKEN": "ghp_pkgtoken_1234567890", "MY_APP_TOKEN": "ghp_agenttoken_1234567890",
        "DATABASE_URL": "postgres://local",
    }
    r = subprocess.run([sys.executable, str(BIN / "project-run"), "env"],
                       capture_output=True, text=True, env=env)
    seen = dict(line.split("=", 1) for line in r.stdout.splitlines() if "=" in line)
    for k in ("SLACK_WEBHOOK_URL", "GH_TOKEN", "LINEAR_API_KEY", "VANTA_CLIENT_SECRET",
              "SSH_AUTH_SOCK", "NODE_AUTH_TOKEN", "MY_APP_TOKEN"):
        assert k not in seen, (k, seen)
    assert seen.get("DATABASE_URL") == "postgres://local" and seen.get("VULN_FIX_RUN") == "task123", seen

    r = subprocess.run([sys.executable, str(BIN / "project-run"), "--with-package-token", "env"],
                       capture_output=True, text=True, env=env)
    seen = dict(line.split("=", 1) for line in r.stdout.splitlines() if "=" in line)
    assert seen.get("NODE_AUTH_TOKEN") == "ghp_pkgtoken_1234567890" and "GH_TOKEN" not in seen, seen
    print("project-run strips secrets by name and by value; package token only on request")


def test_project_run_usage():
    for args, code in ((["--help"], 0), ([], 2), (["--nope", "ls"], 2), (["no-such-cmd-xyz"], 127)):
        r = subprocess.run([sys.executable, str(BIN / "project-run"), *args],
                           capture_output=True, text=True)
        assert r.returncode == code, (args, r)
    print("project-run usage: --help 0, no command 2, unknown option 2, missing command 127")


if __name__ == "__main__":
    test_guard_blocks_unwrapped_project_code()
    test_hook_denies_with_a_retry_hint()
    test_project_run_strips_secrets_by_name_and_value()
    test_project_run_usage()
    print("ok")
