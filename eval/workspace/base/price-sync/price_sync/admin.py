"""Tiny admin HTTP server (health check). Exposed through the service's load balancer."""
import http.server
import json

from . import config


def healthz():
    return 200, {"status": "ok"}


ROUTES = {("GET", "/healthz"): healthz}


class Handler(http.server.BaseHTTPRequestHandler):
    def _dispatch(self, method):
        route = ROUTES.get((method, self.path))
        status, body = route() if route else (404, {"error": "not found"})
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")


def serve():
    http.server.HTTPServer(("", config.ADMIN_PORT), Handler).serve_forever()
