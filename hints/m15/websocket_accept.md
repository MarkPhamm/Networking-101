# Hints — 15_websocket_accept

## Hint 1
Concatenate the **ASCII strings**, not raw bytes, then encode once at
the end:

```python
combined = (key + MAGIC_GUID).encode("ascii")
```

## Hint 2
`hashlib.sha1(...).digest()` returns the 20 raw bytes (not hex).
That's what you want to feed to base64.

```python
sha = hashlib.sha1(combined).digest()
```

## Hint 3
`base64.b64encode` returns `bytes`, so decode back to `str`:

```python
return base64.b64encode(sha).decode("ascii")
```

## Full solution

```python
def ws_accept_key(key: str) -> str:
    combined = (key + MAGIC_GUID).encode("ascii")
    sha = hashlib.sha1(combined).digest()
    return base64.b64encode(sha).decode("ascii")
```
