# Module 15: Sockets, HTTP, and WebSockets

## What You'll Learn

- What a socket actually is (and why every networked program has one)
- How HTTP is just text over a TCP socket
- How URLs break down into the pieces a client needs to connect
- How an HTTP response is structured, byte-for-byte
- Why WebSockets exist and how the upgrade handshake works
- How to probe an HTTP endpoint with `curl` like a pro

---

## The Stack You've Been Standing On

Modules 00–14 marched up the stack: Ethernet frames → IP packets → TCP
segments → TLS → application protocols like SSH. This module zooms in
on the **application layer** — the layer where your code actually
lives.

```
  ┌──────────────────────────────┐
  │  Your Python / JS / whatever │   ← you write code here
  ├──────────────────────────────┤
  │  HTTP / WebSocket / gRPC …   │   ← this module
  ├──────────────────────────────┤
  │  TLS (optional)              │
  ├──────────────────────────────┤
  │  TCP  (Module 08)            │
  ├──────────────────────────────┤
  │  IP   (Module 03)            │
  ├──────────────────────────────┤
  │  Ethernet / Wi-Fi            │
  └──────────────────────────────┘
```

Everything above TCP is *text or framed bytes over a socket*. That's
it. No magic.

### Data engineering analogy

When your Airflow operator calls a REST API, or your Spark job reads
from a service endpoint, or the `requests` library fetches a file —
under the covers it opens a socket, writes a request, reads a
response, closes the socket. HTTP is just the agreed-upon format for
what to write and what to read.

---

## Sockets: The One API Underneath Everything

A **socket** is the OS-level handle on a network connection. In Python,
`socket.socket()` gives you one. You use it to:

1. **Connect** (as a client) to `(host, port)`.
2. **Send bytes** down the wire.
3. **Receive bytes** back.
4. **Close** when done.

That's the entire API. SSH, HTTP, Postgres, Kafka, Redis, gRPC — every
one of these is just "bytes in a specific format, sent through a
socket." Learn the socket API and every protocol becomes readable.

```python
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4 + TCP
s.connect(("example.com", 80))                          # opens TCP
s.sendall(b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n")
data = s.recv(4096)                                     # reads bytes
s.close()
print(data[:80])
# b'HTTP/1.1 200 OK\r\nContent-Type: text/html...'
```

No library needed. That's a working HTTP client in six lines.

---

## HTTP: Text Over TCP

HTTP (HyperText Transfer Protocol) defines what bytes to send on that
socket to request a resource, and what bytes come back.

### Request shape

```
GET /path HTTP/1.1
Host: example.com
User-Agent: my-client/1.0
\r\n
```

- **Request line**: method, path, HTTP version.
- **Headers**: `Name: Value` pairs, one per line, terminated by `\r\n`.
- **Empty line** (`\r\n` by itself) marks the end of headers.
- **Body** (optional) follows.

### Response shape

```
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 1270

<!doctype html>...
```

- **Status line**: HTTP version, numeric status code, reason phrase.
- **Headers**: same format as request.
- **Empty line** terminates headers.
- **Body** follows, length typically announced by `Content-Length`.

### Status codes — the categories you'll see

| Range | Meaning | Common examples |
|---|---|---|
| 2xx | Success | 200 OK, 201 Created, 204 No Content |
| 3xx | Redirect | 301 Moved Permanently, 302 Found, 304 Not Modified |
| 4xx | Client error | 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 429 Too Many Requests |
| 5xx | Server error | 500 Internal Server Error, 502 Bad Gateway, 503 Unavailable, 504 Gateway Timeout |

**Debugging heuristic**: the first digit tells you *who's at fault*.
4xx → fix your request. 5xx → the server blew up, retry or page the
owner.

---

## URLs: The Address of a Resource

A URL packs scheme, host, port, and path into one string:

```
https://api.example.com:8443/v1/users?id=42
│      │                 │    │          │
│      │                 │    │          └ query string
│      │                 │    └ path
│      │                 └ port (optional; defaults by scheme)
│      └ host (DNS name or IP)
└ scheme (http / https / ws / wss)
```

Default ports by scheme:

| Scheme | Default port | Encrypted? |
|---|---|---|
| `http`  | 80   | no  |
| `https` | 443  | yes (TLS) |
| `ws`    | 80   | no  |
| `wss`   | 443  | yes (TLS) |

The client's job is to pull out the pieces and open a TCP socket to
`(host, port)`. Everything you type in a browser URL bar maps to a
socket connection to one of those four port defaults.

---

## WebSockets: Upgrading from HTTP to Bidirectional

HTTP is **request/response**: client asks, server answers, done.
That's great for fetching a page, terrible for a live chat or a
trading dashboard where the server needs to push data to the client.

**WebSockets** solve this by starting life as an HTTP request and
*upgrading* the same TCP connection into a bidirectional
message-framed channel.

### The handshake

Client sends a specially-formed HTTP request:

```
GET /chat HTTP/1.1
Host: example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
```

Server proves it understood the WebSocket protocol by computing a
response key:

1. Concatenate the client's `Sec-WebSocket-Key` with the magic GUID
   `258EAFA5-E914-47DA-95CA-C5AB0DC85B11`.
2. Take the SHA-1 hash of the resulting ASCII string.
3. Base64-encode the 20-byte hash.

That goes back in the response:

```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

After `101 Switching Protocols`, both sides stop speaking HTTP and
start sending WebSocket frames on the same socket. That's why the RFC
calls it an *upgrade*: it's still the same TCP connection, the payload
format just changed.

### Why the magic GUID?

It stops an attacker from tricking a non-WebSocket server into
returning the right bytes by accident. The GUID is from RFC 6455 and
has no cryptographic meaning — it's just arbitrary content that only
WebSocket-aware servers will append.

---

## `curl`: Your Pocket HTTP Client

Every engineer should know these five `curl` invocations cold:

```bash
# 1. Just the status code (no body printed)
curl -s -o /dev/null -w "%{http_code}\n" https://example.com

# 2. Headers only (HEAD request)
curl -I https://example.com

# 3. See request + response on the wire
curl -v https://example.com

# 4. POST JSON
curl -X POST -H "Content-Type: application/json" \
     -d '{"foo": "bar"}' https://api.example.com/things

# 5. Follow redirects
curl -L https://bit.ly/anything
```

`curl` is the Swiss Army knife for debugging any HTTP service — your
own app, a vendor API, a misbehaving load balancer. When a client
library is misbehaving, drop to `curl` and see whether the bug is
yours or theirs.

---

## Common Failures and What They Mean

| Symptom | Layer | Likely cause |
|---|---|---|
| `Could not resolve host` | DNS (Module 03) | Bad hostname |
| `Connection refused` | TCP (Module 08) | Nothing listening on that port |
| `Connection timed out` | TCP | Firewall dropping packets |
| `SSL: CERTIFICATE_VERIFY_FAILED` | TLS | Self-signed cert, expired cert, or wrong host |
| `400 Bad Request` | HTTP | Malformed request (headers, body, method) |
| `401 Unauthorized` | HTTP | Missing or bad credentials |
| `403 Forbidden` | HTTP | Authenticated, but not allowed |
| `404 Not Found` | HTTP | Wrong path |
| `502 Bad Gateway` | HTTP | The server's upstream is down |
| `Upgrade required` on WebSocket | HTTP | Missing `Upgrade: websocket` header |

Notice the layering: DNS fails before TCP, TCP fails before TLS, TLS
fails before HTTP. Reading the error tells you which layer to debug.

---

## Key Takeaways

1. **A socket is just a file handle for a network connection.** Every
   protocol is built on it.
2. **HTTP is plain text over TCP** — you can speak it with six lines
   of Python.
3. **URLs map to `(host, port, path)`** with default ports by scheme.
4. **Status codes cluster by cause** — 4xx is on you, 5xx is on them.
5. **WebSockets upgrade the HTTP connection in place** with a
   SHA-1/base64 handshake proof.
6. **`curl -v` is the fastest way to see what's really on the wire.**

---

Next: the exercises for this module — you'll write a URL parser, make
an HTTP GET with nothing but the `socket` module, compute a WebSocket
handshake, and probe a live endpoint with `curl`.

[Back to main guide](../README.md)
