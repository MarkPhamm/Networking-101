# Hints — 00_parse_ssh_command

## Hint 1
Check whether `"@"` is in the string first. If it isn't, return `("", s)`.

```python
if "@" not in s:
    return ("", s)
```

## Hint 2
`str.split("@", 1)` splits on the *first* `@` only. That gives you exactly two pieces: user on the left, host on the right.

```python
user, host = s.split("@", 1)
return (user, host)
```

## Hint 3
Full solution:

```python
def parse_user_host(s: str) -> tuple[str, str]:
    if "@" not in s:
        return ("", s)
    user, host = s.split("@", 1)
    return (user, host)
```
