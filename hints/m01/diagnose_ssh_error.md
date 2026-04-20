# Hints — 01_diagnose_ssh_error

## Hint 1
`in` checks substring containment on strings:

```python
if "Connection refused" in msg:
    return 3
```

## Hint 2
Check the most specific phrases first and fall through to `return 0`
at the end for anything unrecognized.

## Hint 3
Full solution:

```python
def error_to_step(msg: str) -> int:
    if "Could not resolve hostname" in msg:
        return 2
    if "Connection timed out" in msg or "Connection refused" in msg:
        return 3
    if "REMOTE HOST IDENTIFICATION HAS CHANGED" in msg:
        return 5
    if "Permission denied" in msg:
        return 6
    return 0
```
