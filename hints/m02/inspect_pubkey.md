# Hints — 02_inspect_pubkey

## Hint 1
`str.split(" ", 2)` splits on the first **two** spaces, giving at most
three pieces:

```python
parts = line.strip().split(" ", 2)
# ["ssh-ed25519", "AAAAkey", "mark on work laptop"]
```

## Hint 2
If the line has no comment, `split(" ", 2)` returns only two pieces.
Handle both cases:

```python
if len(parts) == 2:
    return (parts[0], parts[1], "")
```

## Hint 3
Full solution:

```python
def parse_pubkey(line: str) -> tuple[str, str, str]:
    parts = line.strip().split(" ", 2)
    if len(parts) == 2:
        return (parts[0], parts[1], "")
    return (parts[0], parts[1], parts[2])
```
