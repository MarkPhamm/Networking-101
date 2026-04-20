# Hints — 01_tcp_reachability

## Hint 1
Redirecting **both** stdout and stderr to a file needs `2>&1` *after*
the stdout redirect:

```bash
nc -z -v -w 5 github.com 22 > /tmp/net_probe.txt 2>&1
```

`nc` prints its "succeeded" message to stderr, so without `2>&1` the
file ends up empty.

## Hint 2
If the probe fails with "Connection refused", port 22 is reachable
but nothing on github.com answers. Try port 443 instead:

```bash
nc -z -v -w 5 github.com 443 > /tmp/net_probe.txt 2>&1
```

Both ports reliably accept TCP; either satisfies the verifier.

## Hint 3
Confirm the file contents yourself before pressing `v`:

```bash
cat /tmp/net_probe.txt
```

You should see a line containing `succeeded`, `Connected`, or `open`.
