"""Loopback-only read-only HTTP adapter; reads a sanitized collector snapshot."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files


def handler(snapshot_path):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, body, content_type):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            authority = self.headers.get('Host', '')
            if authority not in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}:
                self.respond(403, b'Forbidden host', 'text/plain')
                return
            if self.path == '/':
                self.respond(200, files('codex_harness.resources').joinpath('monitor.html').read_bytes(), 'text/html; charset=utf-8')
            elif self.path == '/api/status':
                try:
                    body = snapshot_path.read_bytes()
                    if len(body) > 5_000_000:
                        raise ValueError('Snapshot too large')
                    json.loads(body)
                    self.respond(200, body, 'application/json; charset=utf-8')
                except (OSError, ValueError):
                    self.respond(503, b'{"error":"snapshot_unavailable"}', 'application/json')
            elif self.path == '/health':
                self.respond(200, b'{"service":"harness-monitor"}', 'application/json')
            else:
                self.respond(404, b'Not found', 'text/plain')

        def do_POST(self):
            self.respond(405, b'Read only', 'text/plain')

        def log_message(self, *args):
            pass
    return Handler


def serve(snapshot_path, port=8787):
    ThreadingHTTPServer(('127.0.0.1', port), handler(snapshot_path)).serve_forever()
