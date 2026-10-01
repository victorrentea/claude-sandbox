#!/usr/bin/env python3
"""The "tool": uses $DEMO_API_KEY to call the remote server.

Inside the sandbox it only ever holds the sentinel; the sandbox proxy swaps in
the real key on the way out. urllib would bypass the proxy for localhost
(NO_PROXY lists it by default), so the request is sent to the proxy by hand.
Prints "<status> via <route>: <body>" so a failure shows where it happened.
"""
import base64, http.client, os, urllib.parse

URL = "http://localhost:8777/whoami"
headers = {"Authorization": f"Bearer {os.environ.get('DEMO_API_KEY', '')}"}

proxy = os.environ.get("http_proxy") or os.environ.get("HTTP_PROXY")
if proxy:
    p = urllib.parse.urlsplit(proxy)
    conn, target, route = http.client.HTTPConnection(p.hostname, p.port, timeout=10), URL, f"proxy {p.hostname}:{p.port}"
    if p.username:  # the sandbox proxy wants the user:pass embedded in its URL; curl sends it on its own
        creds = f"{urllib.parse.unquote(p.username)}:{urllib.parse.unquote(p.password or '')}"
        headers["Proxy-Authorization"] = "Basic " + base64.b64encode(creds.encode()).decode()
else:
    conn, target, route = http.client.HTTPConnection("localhost", 8777, timeout=10), "/whoami", "direct (no http_proxy set)"

try:
    conn.request("GET", target, headers=headers)
    r = conn.getresponse()
    print(f"{r.status} via {route}: {r.read().decode() or '(empty body)'}")
except OSError as e:
    print(f"FAILED via {route}: {e}")
