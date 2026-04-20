# Hints — 15_raw_http_get

## Hint 1
Build the request as bytes with `\r\n` line endings, **not** just `\n`:

```python
request = (
    f"GET {path} HTTP/1.1\r\n"
    f"Host: {host}\r\n"
    "Connection: close\r\n"
    "\r\n"
).encode("ascii")
```

Forgetting the trailing blank line is the #1 reason HTTP servers hang
waiting for more headers.

## Hint 2
Use a `with` block so the socket closes even if parsing raises:

```python
with socket.create_connection((host, port), timeout=timeout) as s:
    s.sendall(request)
    data = b""
    while b"\r\n" not in data:
        chunk = s.recv(4096)
        if not chunk:
            break
        data += chunk
```

You only need to read until the end of the first line for this
exercise; you can ignore the rest of the response.

## Hint 3
The status line looks like `HTTP/1.1 200 OK\r\n`. Split on spaces and
take the second token:

```python
status_line = data.split(b"\r\n", 1)[0].decode("ascii")
parts = status_line.split(" ", 2)  # ["HTTP/1.1", "200", "OK"]
return int(parts[1])
```

## Full solution

```python
def http_get_status(host, port, path, timeout=5.0):
    req = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii")
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall(req)
        data = b""
        while b"\r\n" not in data:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    status_line = data.split(b"\r\n", 1)[0].decode("ascii")
    return int(status_line.split(" ", 2)[1])
```
