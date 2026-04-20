# Lesson: lessons/m15/02_raw_http_get.md
# Read the lesson before starting this exercise.

# TASK:
# Implement `http_get_status(host: str, port: int, path: str,
# timeout: float = 5.0) -> int` that opens a raw TCP socket, sends an
# HTTP/1.1 GET request, and returns the numeric status code from the
# response's status line.
#
# You must use only the `socket` module (no `http.client`, `urllib`,
# or `requests`). Parsing the status line is the whole point.
#
# Request format:
#
#   GET {path} HTTP/1.1\r\n
#   Host: {host}\r\n
#   Connection: close\r\n
#   \r\n
#
# The response starts with:
#
#   HTTP/1.1 200 OK\r\n
#   Header: value\r\n
#   ...
#
# Return just the `200` as an int.
#
# TODO: replace the placeholder return below.

import socket


def http_get_status(host: str, port: int, path: str, timeout: float = 5.0) -> int:
    # YOUR CODE BELOW
    return 0  # TODO


if __name__ == "__main__":
    # Demo against a public host. Skip if you're offline.
    try:
        code = http_get_status("example.com", 80, "/")
        print(f"example.com / -> {code}")
    except OSError as e:
        print(f"could not reach example.com: {e}")
