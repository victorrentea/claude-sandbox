#!/usr/bin/env python3
"""The remote server: stand-in for a real API that accepts the demo key, never echoes it back.

Runs OUTSIDE the sandbox, in its own terminal (you start it), on 127.0.0.1:8777.
Port 8777, not 8765: Victor Addons already listens on 8765.
GET /whoami with "Authorization: Bearer <key>" -> 200 if the key is right, else 401.
"""
import hmac, json, pathlib
from http.server import BaseHTTPRequestHandler, HTTPServer

ENV = pathlib.Path(__file__).resolve().parent / ".env"
KEY = dict(line.split("=", 1) for line in ENV.read_text().splitlines() if "=" in line)["DEMO_API_KEY"]

def describe(auth):
    """What a rejected caller sent, without ever echoing something that could be the real key."""
    token = auth.removeprefix("Bearer ")
    if not auth:
        return "no Authorization header"
    if token.startswith("sk-demo-"):
        return "a different sk-demo- key"
    return f"{token[:16]!r}{'…' if len(token) > 16 else ''} (the placeholder, not swapped by the proxy)"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        auth = self.headers.get("Authorization", "")
        ok = hmac.compare_digest(auth, f"Bearer {KEY}")
        body = {"ok": True, "user": "demo"} if ok else {"ok": False, "error": "bad key"}
        self.send_response(200 if ok else 401)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())
        print(f"{self.path} -> {'200 key accepted' if ok else '401 rejected, got ' + describe(auth)}", flush=True)

    def log_message(self, *args):
        pass

print("remote server listening on http://localhost:8777/whoami", flush=True)
HTTPServer(("127.0.0.1", 8777), Handler).serve_forever()
