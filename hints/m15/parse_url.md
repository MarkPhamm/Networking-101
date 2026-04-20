# Hints — 15_parse_url

## Hint 1
`urlparse` gives you almost everything:

```python
from urllib.parse import urlparse
p = urlparse("https://example.com:8443/path")
# p.scheme = "https", p.hostname = "example.com",
# p.port   = 8443,    p.path = "/path"
```

Use `.hostname` (not `.netloc`) — hostname strips the port for you.

## Hint 2
`p.port` is `None` when the URL doesn't specify one. Fall back to the
scheme default:

```python
port = p.port or DEFAULT_PORTS[p.scheme]
```

## Hint 3
Full solution:

```python
def parse_url(url: str) -> tuple[str, str, int, str]:
    p = urlparse(url)
    scheme = p.scheme
    host = p.hostname or ""
    port = p.port or DEFAULT_PORTS[scheme]
    path = p.path or "/"
    return (scheme, host, port, path)
```
