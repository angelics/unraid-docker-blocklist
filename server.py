#!/usr/bin/env python3
import os
import threading
import time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import fetch

PORT = int(os.environ.get("PORT", "8080"))
DIRECTORY = "/data"
REFRESH_HOURS = int(os.environ.get("REFRESH_HOURS", "24"))
_refresh_lock = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == "/refresh":
            try:
                with _refresh_lock:
                    fetch.main()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok\n")
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"error: {e}\n".encode())
            return
        super().do_GET()


def refresh_loop():
    while True:
        time.sleep(REFRESH_HOURS * 3600)
        try:
            with _refresh_lock:
                fetch.main()
        except Exception as e:
            print(f"Refresh failed: {e}")


def run():
    with _refresh_lock:
        fetch.main()
    t = threading.Thread(target=refresh_loop, daemon=True)
    t.start()
    with ThreadingHTTPServer(("", PORT), Handler) as httpd:
        print(f"Serve at port {PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    run()
