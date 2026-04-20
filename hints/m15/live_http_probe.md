# Hints — 15_live_http_probe

## Hint 1
Make sure you're redirecting to the right file:

```bash
curl -s -o /dev/null -w "%{http_code}" https://example.com > /tmp/http_probe.txt
```

Check the result:

```bash
cat /tmp/http_probe.txt
# 200
```

## Hint 2
No trailing newline is fine — `%{http_code}` prints just the three
digits. If you want a newline for readability, use `%{http_code}\n`;
the verifier's regex works either way.

## Hint 3
If you get `000` (curl's "no response" placeholder), the request
failed before HTTP. Check:

- DNS: `dig example.com`
- Connectivity: `nc -z -w 5 example.com 443`
- TLS: `curl -v https://example.com 2>&1 | grep -i SSL`

Switch to a different host to prove the `curl` invocation itself is
fine:

```bash
curl -s -o /dev/null -w "%{http_code}" https://www.google.com > /tmp/http_probe.txt
```
