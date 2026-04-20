# Lesson: lessons/m15/03_websocket_accept.md
# Read the lesson before starting this exercise.

# TASK:
# Implement `ws_accept_key(key: str) -> str` that computes the value a
# WebSocket server must return in the `Sec-WebSocket-Accept` header
# given the client's `Sec-WebSocket-Key`.
#
# Algorithm (RFC 6455 §4.2.2):
#   1. Concatenate `key` with the magic GUID
#      "258EAFA5-E914-47DA-95CA-C5AB0DC85B11".
#   2. SHA-1 hash the resulting ASCII string.
#   3. Base64-encode the 20-byte hash.
#   4. Return the base64 string.
#
# Canonical example from the RFC:
#   ws_accept_key("dGhlIHNhbXBsZSBub25jZQ==")
#     -> "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="
#
# TODO: replace the placeholder below.

import base64
import hashlib

MAGIC_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def ws_accept_key(key: str) -> str:
    # YOUR CODE BELOW
    return ""  # TODO


if __name__ == "__main__":
    print(ws_accept_key("dGhlIHNhbXBsZSBub25jZQ=="))
    # Expected: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
