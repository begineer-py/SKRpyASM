#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys
from functools import partial

PORT = int(os.environ.get("TEST_WEB_PORT", "5000"))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    Handler = partial(http.server.SimpleHTTPRequestHandler, directory=here)

    # ThreadingHTTPServer is available via http.server in 3.7+
    try:
        with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
            print(f"[test_web] Serving {here} at http://127.0.0.1:{PORT}")
            print("[test_web] Press Ctrl+C to stop")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[test_web] Shutting down...")
        try:
            httpd.server_close()
        except Exception:
            pass


if __name__ == "__main__":
    main()
