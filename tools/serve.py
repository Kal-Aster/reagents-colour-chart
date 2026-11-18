#!/usr/bin/env python3
"""Development server for the page.

Serves the repository with caching turned off, so that editing a module is
picked up on reload instead of being served from the browser cache.

    python3 tools/serve.py [port]
"""
from __future__ import annotations

import http.server
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


class Server(socketserver.TCPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    os_chdir = ROOT
    import os
    os.chdir(os_chdir)
    with Server(("", PORT), Handler) as httpd:
        print(f"serving {ROOT} on http://localhost:{PORT}")
        httpd.serve_forever()
