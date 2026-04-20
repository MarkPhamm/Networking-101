"""Tests for the raw HTTP GET exercise.

A small localhost HTTP server is spun up per-session so the tests
don't depend on the public internet.
"""

import http.server
import socketserver
import threading

import pytest

import exercises.m15.raw_http_get as ex


class _Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):  # noqa: N802
        if self.path == "/ok":
            body = b"OK"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/gone":
            self.send_response(410)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()

    def log_message(self, *args, **kwargs):  # silence the server
        pass


@pytest.fixture(scope="module")
def server():
    httpd = socketserver.TCPServer(("127.0.0.1", 0), _Handler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    yield port
    httpd.shutdown()
    httpd.server_close()


def test_returns_200_on_ok(server):
    code = ex.http_get_status("127.0.0.1", server, "/ok")
    print(f"OUTPUT: GET /ok -> {code}", flush=True)
    assert code == 200


def test_returns_404_on_missing(server):
    code = ex.http_get_status("127.0.0.1", server, "/does-not-exist")
    assert code == 404


def test_returns_410_on_gone(server):
    code = ex.http_get_status("127.0.0.1", server, "/gone")
    assert code == 410


def test_returns_int(server):
    code = ex.http_get_status("127.0.0.1", server, "/ok")
    assert isinstance(code, int), f"Expected int, got {type(code).__name__}"
