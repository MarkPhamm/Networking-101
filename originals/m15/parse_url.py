# Lesson: lessons/m15/01_parse_url.md
# Read the lesson before starting this exercise.

# TASK:
# Implement `parse_url(url: str) -> tuple[str, str, int, str]` that
# returns (scheme, host, port, path).
#
# Rules:
#   - Supported schemes: "http", "https", "ws", "wss".
#   - If the URL has no explicit port, use the scheme's default:
#       http  -> 80
#       https -> 443
#       ws    -> 80
#       wss   -> 443
#   - If the URL has no path (e.g. "https://example.com"), return "/".
#   - Ignore query strings and fragments for this exercise.
#
# Examples:
#   parse_url("http://example.com/path")
#     -> ("http", "example.com", 80, "/path")
#   parse_url("https://example.com:8443/")
#     -> ("https", "example.com", 8443, "/")
#   parse_url("wss://chat.example.com/ws")
#     -> ("wss", "chat.example.com", 443, "/ws")
#   parse_url("https://example.com")
#     -> ("https", "example.com", 443, "/")
#
# Hint: `urllib.parse.urlparse` does most of the work. You only need
# to fill in the default port and default path.
#
# TODO: replace the placeholder return below.

from urllib.parse import urlparse

DEFAULT_PORTS = {"http": 80, "https": 443, "ws": 80, "wss": 443}


def parse_url(url: str) -> tuple[str, str, int, str]:
    # YOUR CODE BELOW
    return ("", "", 0, "")  # TODO


if __name__ == "__main__":
    samples = [
        "http://example.com/path",
        "https://example.com:8443/",
        "wss://chat.example.com/ws",
        "https://example.com",
    ]
    for u in samples:
        print(f"{u:40s} -> {parse_url(u)}")
