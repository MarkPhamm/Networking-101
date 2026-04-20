# Module 08 Exercises: The TCP/IP Stack

Work through these exercises in order. You'll observe TCP and UDP in action using tools you've already learned, but now with a mental model for what each layer is doing.

**Prerequisites**: Modules 01-07 completed. Remote Login enabled ([Mac Setup Guide](../appendix/mac-setup.md)).

---

## Exercise 1: Capture the TCP Three-Way Handshake with SSH

You're going to watch the SYN, SYN-ACK, ACK handshake happen in real time by capturing packets on the loopback interface while SSH'ing into your own machine.

### Setup

You need **two terminal windows** open side by side.

### Steps

**Terminal 1 (packet capture):**

```bash
# Capture 20 packets on the loopback interface for port 22
sudo tcpdump -i lo0 -n -c 20 port 22
```

Flags explained:
- `-i lo0` -- Listen on the loopback interface (traffic to/from localhost)
- `-n` -- Don't resolve hostnames (show raw IPs)
- `-c 20` -- Stop after capturing 20 packets
- `port 22` -- Only capture SSH traffic

**Terminal 2 (SSH connection):**

```bash
# SSH to yourself
ssh localhost
# Enter your password when prompted
# Type a few commands (ls, whoami)
# Then type: exit
```

### What to look for in Terminal 1

After the SSH session ends, tcpdump will display the captured packets. Look for these phases:

**Phase 1: Three-way handshake (first 3 packets)**

```
# Packet 1 - SYN: Client initiates connection
127.0.0.1.52431 > 127.0.0.1.22: Flags [S], seq 123456789, ...

# Packet 2 - SYN-ACK: Server accepts
127.0.0.1.22 > 127.0.0.1.52431: Flags [S.], seq 987654321, ack 123456790, ...

# Packet 3 - ACK: Client confirms
127.0.0.1.52431 > 127.0.0.1.22: Flags [.], ack 987654322, ...
```

The flags decode as:
- `[S]` = SYN
- `[S.]` = SYN-ACK (the `.` represents ACK)
- `[.]` = ACK only
- `[P.]` = PSH-ACK (data being pushed)
- `[F.]` = FIN-ACK (connection closing)

**Phase 2: Data exchange (middle packets)**

You'll see `[P.]` flags -- these are data packets carrying the SSH protocol exchange, key negotiation, authentication, and your shell commands/output.

Note the source and destination ports:
- The server side always uses port **22**
- The client side uses an **ephemeral port** (a high number like 52431)

**Phase 3: Connection teardown (last few packets)**

After you type `exit`, look for `[F.]` (FIN-ACK) packets:

```
# Client sends FIN
127.0.0.1.52431 > 127.0.0.1.22: Flags [F.], ...

# Server acknowledges and sends its own FIN
127.0.0.1.22 > 127.0.0.1.52431: Flags [F.], ...

# Client acknowledges
127.0.0.1.52431 > 127.0.0.1.22: Flags [.], ...
```

### Questions to answer

1. What ephemeral port did your client use?
2. Can you count the three handshake packets (SYN, SYN-ACK, ACK)?
3. How many data packets (`[P.]`) were exchanged?
4. Can you identify the FIN teardown?
5. How does the sequence number in the SYN-ACK relate to the SYN's sequence number?

---

## Exercise 2: Trace HTTP Layer by Layer

In this exercise, you'll make an HTTP request and observe what happens at each TCP/IP layer. You'll use `curl -v` (verbose mode) to see the application and transport layers, and `tcpdump` to see the network and link layers.

### Setup

Two terminal windows again.

### Steps

**Terminal 1 (packet capture):**

```bash
# Capture packets going to/from example.com
# First, find the IP:
dig +short example.com
# Note the IP (e.g., 93.184.216.34)

# Start the capture (replace with the actual IP you got)
sudo tcpdump -i en0 -n -c 30 host 93.184.216.34
```

**Note:** Use `en0` for wired Ethernet or `en0`/`en1` for Wi-Fi. If unsure, check with `ifconfig` to find your active interface.

**Terminal 2 (HTTP request):**

```bash
curl -v http://example.com
```

### Annotating the curl output

`curl -v` shows you the connection process step by step. Here's what each section maps to in the TCP/IP model:

```
* Host example.com:80 was resolved.
* IPv6: 2606:2800:21f:cb07:6820:80da:af6b:8b2c
* IPv4: 93.184.216.34
```
**This is DNS resolution (Application layer).** Your system resolved the hostname to an IP address. This used UDP port 53 behind the scenes.

```
*   Trying 93.184.216.34:80...
* Connected to example.com (93.184.216.34) port 80
```
**This is the TCP three-way handshake (Transport layer).** `curl` established a TCP connection to port 80. The SYN/SYN-ACK/ACK just happened, but curl only shows the result.

```
> GET / HTTP/1.1
> Host: example.com
> User-Agent: curl/8.7.1
> Accept: */*
```
**This is the HTTP request (Application layer).** The actual data your browser sends over the established TCP connection. The `>` prefix means "data sent."

```
< HTTP/1.1 200 OK
< Content-Type: text/html; charset=UTF-8
< Content-Length: 1256
< ...
```
**This is the HTTP response (Application layer).** The `<` prefix means "data received." You see headers followed by the HTML body.

### What tcpdump shows (Terminal 1)

In your tcpdump output, you'll see the same conversation but at the packet level:

1. **SYN** -- Your machine to `93.184.216.34:80` with `Flags [S]`
2. **SYN-ACK** -- Server responds with `Flags [S.]`
3. **ACK** -- Handshake complete with `Flags [.]`
4. **PSH-ACK** -- The HTTP GET request sent as data with `Flags [P.]`
5. **PSH-ACK** -- The HTTP 200 response with HTML body
6. **FIN** -- Connection closing

### Questions to answer

1. What IP address did DNS return for `example.com`?
2. Can you match the three handshake packets in tcpdump to curl's "Connected to" line?
3. How many TCP packets did the entire HTTP request/response take?
4. What is the total roundtrip time from SYN to the first data packet? (Look at the timestamps in tcpdump.)
5. What layer does each line of `curl -v` output correspond to?

---

## Exercise 3: TCP vs UDP -- DNS Both Ways

DNS normally uses **UDP** because queries are small and a single request-response exchange doesn't need the overhead of a TCP connection. But DNS can also run over **TCP** -- and you can force it to, so you can compare.

### Steps

**UDP (default):**

```bash
dig @8.8.8.8 google.com
```

Look for this line near the bottom of the output:

```
;; MSG SIZE  rcvd: 55
```

And this line tells you the transport:

```
;; SERVER: 8.8.8.8#53(8.8.8.8) (UDP)
```

**TCP (forced):**

```bash
dig @8.8.8.8 google.com +tcp
```

Look for the same lines. You should now see:

```
;; SERVER: 8.8.8.8#53(8.8.8.8) (TCP)
```

### Compare the two

```bash
# Time the UDP query
time dig @8.8.8.8 google.com +short

# Time the TCP query
time dig @8.8.8.8 google.com +tcp +short
```

### Questions to answer

1. Did both queries return the same answer?
2. Which was faster -- UDP or TCP? By how much?
3. Why is TCP slower for a DNS query? (Hint: how many round-trips does TCP need before data can flow?)
4. When does DNS actually use TCP? (Hint: what happens when a DNS response exceeds 512 bytes, or when doing zone transfers?)

### Why DNS defaults to UDP

DNS defaults to UDP because:
- A typical DNS query and response fit in a single packet (well under the 512-byte traditional limit)
- UDP needs zero round-trips to set up -- just send the question, get the answer
- TCP would require a three-way handshake (1.5 round-trips) *before* the query can even be sent -- that triples the latency for a simple lookup
- DNS clients already handle reliability themselves: if no response comes back in a few seconds, they retry

DNS switches to TCP when:
- The response is too large for a single UDP packet (the server sets a "truncated" flag and the client retries over TCP)
- Zone transfers between DNS servers (`AXFR` / `IXFR`) use TCP because they transfer large amounts of data
- DNSSEC responses, which include cryptographic signatures, can exceed UDP limits

### Bonus: See the difference with tcpdump

```bash
# Terminal 1: Capture DNS traffic
sudo tcpdump -i en0 -n port 53 -c 10

# Terminal 2: UDP query
dig @8.8.8.8 google.com
```

You'll see exactly **two packets**: one query, one response.

Now repeat with `+tcp`:

```bash
# Terminal 1: Capture again
sudo tcpdump -i en0 -n port 53 -c 15

# Terminal 2: TCP query
dig @8.8.8.8 google.com +tcp
```

You'll see **seven or more packets**: SYN, SYN-ACK, ACK, query, response, FIN, FIN-ACK. All that overhead for the same 55 bytes of DNS data.

---

[Back to Module 08 README](README.md) | [Module 08 Cheatsheet](cheatsheet.md)

[Back to main guide](../README.md)
