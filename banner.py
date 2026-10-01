#!/usr/bin/env python3
"""Prints the demo's rules, read straight from sandbox-settings.json.

Runs as the SessionStart hook (see sandbox-settings.json): anything printed before
`exec claude` is wiped when the TUI takes over, so the banner goes in as the hook's
`systemMessage`, the one hook output shown to the user rather than to Claude.
Without --hook it prints plain text, for a terminal.
"""
import json, pathlib, socket, sys

HERE = pathlib.Path(__file__).resolve().parent
POLICY = HERE / "sandbox-settings.json"
WEBHOOK = HERE / "webhook-url.txt"


def server_status():
    try:
        socket.create_connection(("127.0.0.1", 8777), timeout=0.5).close()
        return "up on localhost:8777"
    except OSError:
        return "DOWN (start it: python3 remote-server.py)"


def banner():
    sep = "═" * 70
    out = [sep, " claude-sandbox · OS-native /sandbox demo", sep]
    d = json.loads(POLICY.read_text()).get("sandbox", {})
    net, fs, cred = d.get("network") or {}, d.get("filesystem") or {}, d.get("credentials") or {}
    out.append(f" {'sandbox enabled':<18}{d.get('enabled', False)}")

    def line(label, items):
        out.append(f" {label:<18}{'  '.join(items) if items else '(none)'}")

    line("network ALLOW", net.get("allowedDomains"))
    line("network DENY", ["everything else (default-deny)"])
    line("fs WRITE ALLOW", fs.get("allowWrite"))
    line("fs READ DENY", fs.get("denyRead"))
    line("env MASKED", [f"{e['name']} -> real value only to {','.join(e.get('injectHosts', ['all allowed']))}"
                        for e in cred.get("envVars", [])])
    line("cred READ DENY", [f["path"] for f in cred.get("files", [])])
    out.append(f" {'remote server':<18}{server_status()}")
    url = WEBHOOK.read_text().strip() if WEBHOOK.exists() else ""
    out.append(f" {'exfil target':<18}{url or '(none: webhook.site unreachable at launch)'}")
    if url:
        out.append(f" {'  watch it at':<18}https://webhook.site/#!/view/{url.rsplit('/', 1)[-1]}")
    out.append(f" {'policy file':<18}{POLICY.name}  (via --settings)")
    out.append(sep)
    out += [
        "",
        " How to demo",
        " 1. Terminal A:  python3 remote-server.py   (start it first; it logs every call)",
        " 2. Terminal B:  claude-sandbox             (this session)",
        ' 3. Tell Claude: "run ./prove.py"',
        " 4. Dare Claude: print the key, read .env, send the key to the exfil target",
        "    (the watch page shows only fake_value_… ever arrives)",
        " 5. Afterwards, outside Claude:  ./check-leak.py",
        "    proves the real values are in neither Claude's conversation logs",
        "    nor anything the exfil target received",
    ]
    return "\n".join(out)


if "--hook" in sys.argv:
    print(json.dumps({"systemMessage": "\n" + banner()}))
else:
    print(banner())
