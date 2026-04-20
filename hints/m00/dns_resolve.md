# Hints — 00_dns_resolve

## Hint 1
`socket.getaddrinfo(host, port, family, type)` returns a list of
5-tuples. For IPv4 only, pass `socket.AF_INET`.

```python
results = socket.getaddrinfo(hostname, None, socket.AF_INET)
```

## Hint 2
Each tuple is `(family, type, proto, canonname, sockaddr)` where
`sockaddr` is `(ip, port)`. Grab index `[0][4][0]` to get the IP
from the first result.

## Hint 3
Full solution:

```python
import socket

def resolve_ipv4(hostname: str) -> str:
    results = socket.getaddrinfo(hostname, None, socket.AF_INET)
    return results[0][4][0]
```
