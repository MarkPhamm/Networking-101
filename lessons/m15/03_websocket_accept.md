# Exercise: Compute the WebSocket `Sec-WebSocket-Accept` header

A WebSocket connection starts as an HTTP/1.1 GET request with an
upgrade header. The server proves it's WebSocket-aware (not just an
HTTP server that happens to return 101) by computing a specific value
from the client's random `Sec-WebSocket-Key`.

## The algorithm (RFC 6455 §4.2.2)

```
accept = base64( sha1( ascii( client_key + MAGIC_GUID ) ) )
```

where

```
MAGIC_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
```

## The canonical example

From the RFC itself:

| Field | Value |
|---|---|
| `Sec-WebSocket-Key` | `dGhlIHNhbXBsZSBub25jZQ==` |
| `Sec-WebSocket-Accept` | `s3pPLMBiTxaQ9kYGzzhZRbK+xOo=` |

Your implementation must produce that exact accept value for that
exact key.

## What to do

1. Open `exercises/m15/websocket_accept.py`.
2. Implement `ws_accept_key` using `hashlib.sha1` and
   `base64.b64encode`.
3. Press `v`.

## Why a magic GUID?

The RFC authors wanted to prevent an accidentally-WebSocket handshake
— e.g. an HTTP server mindlessly echoing headers back. Only a server
that knows the protocol will append this specific GUID and hash it.
The value has no cryptographic meaning; it's just an arbitrary string
baked into the spec.

## DE analogy

Same pattern as the OAuth `code_verifier` / `code_challenge`
exchange, or AWS Signature V4: "prove you know the protocol by
combining your input with a known constant and hashing." It's a
one-line computation, but it gates the whole handshake.
