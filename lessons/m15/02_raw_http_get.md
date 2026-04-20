# Exercise: HTTP GET with a raw socket

This exercise removes the magic. You'll implement an HTTP client
using nothing but the `socket` module and then see for yourself that
HTTP is literally just text.

## The shape of an HTTP/1.1 request

```
GET /path HTTP/1.1\r\n
Host: example.com\r\n
Connection: close\r\n
\r\n
```

- Lines end with `\r\n` (carriage return + line feed).
- An empty `\r\n` marks the end of headers.
- `Host:` is **required** in HTTP/1.1 — servers hosting multiple
  domains need it to pick the right vhost.
- `Connection: close` tells the server not to keep the connection
  alive, so the server will close the socket once it's finished
  sending the response (makes reading simpler).

## What to do

1. Open `exercises/m15/raw_http_get.py`.
2. Open a TCP socket to `(host, port)` with `socket.create_connection`.
3. Send the request bytes above, substituting the real `path` and `host`.
4. Read enough of the response to see the first line.
5. Parse the status line — `HTTP/1.1 200 OK\r\n` — and return the integer.
6. Press `v`.

The tests spin up a local HTTP server on a random port; no internet required.

## DE analogy

Every REST client you use (`requests`, `httpx`, `aiohttp`, the JVM
`HttpClient`, Spark's cloud connectors) does exactly this. They wrap
socket send/recv with convenience, but the bytes on the wire are
identical.

## Troubleshooting

- **Hangs forever** → missing the `\r\n\r\n` after headers; the server
  is waiting for more.
- **`ConnectionResetError`** → server closed before you finished
  reading; common with `Connection: close`. Catch and parse what you
  have.
- **Empty status line** → wrong port, or TLS server speaking to your
  plaintext socket. Use port 80 (not 443) for this exercise.
