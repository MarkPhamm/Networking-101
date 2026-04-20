# Exercise: Probe TCP reachability with `nc`

`ssh user@host` can fail at Step 3 (TCP) for two different reasons:

- **Connection refused** — the host is up but nothing is listening on port 22.
- **Connection timed out** — packets are being dropped (firewall, wrong IP).

Before fighting with SSH config, verify the TCP layer works. `nc`
(netcat) does exactly that without involving SSH at all:

```bash
nc -z -v -w 5 <host> <port>
```

- `-z` — "just probe, don't send data"
- `-v` — verbose (print the result)
- `-w 5` — 5-second timeout

If the TCP handshake completes, you'll see something like:

```
Connection to github.com port 22 [tcp/ssh] succeeded!
```

If it doesn't, `nc` exits with a non-zero status and the message tells
you which failure mode it was — the same two from above.

## What to do

Run this **in your terminal** (not inside `net-learn`):

```bash
nc -z -v -w 5 github.com 22 > /tmp/net_probe.txt 2>&1
```

That writes both stdout and stderr to `/tmp/net_probe.txt`.

Then come back to `net-learn` and press `v`. The verifier checks:

1. `/tmp/net_probe.txt` exists.
2. It contains evidence of a successful TCP connection (`succeeded`,
   `Connected`, `open`, or an `SSH-` banner).

## DE analogy

This is the same thing you do when a Spark job can't reach Postgres:
before poking at JDBC URLs and drivers, you prove the host:port is
reachable from the machine running the job. `nc -z -v -w 5 db 5432`.
