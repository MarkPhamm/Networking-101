# Lesson: lessons/m00/02_dns_resolve.md
# Read the lesson before starting this exercise.

# TASK:
# Implement `resolve_ipv4(hostname: str) -> str` that returns the first
# IPv4 address for `hostname` using the standard-library `socket` module.
#
# Requirements:
#   - Restrict the lookup to IPv4 (AF_INET).
#   - Return just the IP as a plain string, e.g. "127.0.0.1".
#   - Leave exceptions (like socket.gaierror) unhandled — let them bubble up.
#
# Example:
#   resolve_ipv4("localhost") -> "127.0.0.1"
#
# TODO: replace the placeholder below.

import socket


def resolve_ipv4(hostname: str) -> str:
    # YOUR CODE BELOW
    return ""  # TODO


if __name__ == "__main__":
    for h in ["localhost", "one.one.one.one"]:
        try:
            print(f"{h:30s} -> {resolve_ipv4(h)}")
        except socket.gaierror as e:
            print(f"{h:30s} -> could not resolve ({e})")
