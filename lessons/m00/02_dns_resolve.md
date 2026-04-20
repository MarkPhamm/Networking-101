# Exercise: Resolve a hostname to an IPv4 address

Module 00 Step 2: **DNS resolution**. Before SSH can open a TCP
connection, the client has to convert `my-server.example.com` into an
IP address.

Python's `socket` module exposes the same resolver your OS uses, so
this is what `ssh`, `dig`, and every networked Python program do under
the hood.

## The API

```python
socket.getaddrinfo(host, port, family=0, type=0, proto=0, flags=0)
```

Returns a list of tuples. Each tuple looks like:

```
(AddressFamily.AF_INET, SocketKind.SOCK_STREAM, 6, '', ('127.0.0.1', 0))
 └─────── family ─────┘  └───── type ─────┘  proto  canon   sockaddr
```

You want the `sockaddr` — element `[4]` — and inside that, the IP at
index `[0]`. Restrict to IPv4 with `family=socket.AF_INET`.

## What to do

1. Open `exercises/m00/dns_resolve.py`.
2. Implement `resolve_ipv4(hostname)` using `socket.getaddrinfo`.
3. Press `v` to run the tests.

## Why this matters for SSH

If this step fails you see:

```
ssh: Could not resolve hostname foo.example.com: nodename nor servname provided, or not known
```

Translation: `getaddrinfo` raised `socket.gaierror`. The connection
never even got to TCP.
