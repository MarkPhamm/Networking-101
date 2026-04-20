# Exercise: Break a URL into its pieces

Before any HTTP client can open a socket it has to extract four things
from a URL:

- **scheme** — decides whether to wrap the connection in TLS
- **host** — passed to DNS
- **port** — passed to `socket.connect()`
- **path** — goes in the HTTP request line

You'll often see this broken out implicitly inside libraries like
`requests` or `aiohttp`. Doing it yourself once makes their behavior
obvious.

## What to do

1. Open `exercises/m15/parse_url.py`.
2. Use `urllib.parse.urlparse` and the `DEFAULT_PORTS` dict to return
   `(scheme, host, port, path)`.
3. Press `v`.

## Watch out for

- **No port in URL** — `urlparse(...).port` returns `None`. Fall back
  to the scheme default.
- **No path** — `urlparse("https://example.com").path` is `""`. You
  must return `"/"` so the HTTP request line is valid.
- Use `.hostname`, not `.netloc`. `.netloc` includes the port.

## DE analogy

The same parsing happens inside every database driver when you hand
it a connection string like `postgresql://user@db:5432/analytics`.
Scheme → driver, host → DNS, port → socket, path → database name.
