# Module 08 Cheatsheet: The TCP/IP Stack

Quick reference card. Print this or keep it in a tab.

---

## OSI vs TCP/IP Layer Comparison

```
       OSI Model                    TCP/IP Model
  ┌─────────────────┐
  │ 7. Application  │
  ├─────────────────┤         ┌─────────────────────┐
  │ 6. Presentation │ ──────> │ 4. Application      │  SSH, HTTP, DNS, SMTP
  ├─────────────────┤         └─────────────────────┘
  │ 5. Session      │
  ├─────────────────┤         ┌─────────────────────┐
  │ 4. Transport    │ ──────> │ 3. Transport        │  TCP, UDP
  ├─────────────────┤         └─────────────────────┘
  │ 3. Network      │ ──────> ┌─────────────────────┐
  ├─────────────────┤         │ 2. Internet         │  IP, ICMP
  │ 2. Data Link    │         └─────────────────────┘
  ├─────────────────┤ ──────> ┌─────────────────────┐
  │ 1. Physical     │         │ 1. Link             │  Ethernet, Wi-Fi, ARP
  └─────────────────┘         └─────────────────────┘
```

| OSI Layer | OSI Name      | TCP/IP Layer | TCP/IP Name    | Key Protocols          | Data Unit   |
|-----------|---------------|--------------|----------------|------------------------|-------------|
| 7         | Application   | 4            | Application    | HTTP, SSH, DNS, SMTP   | Data        |
| 6         | Presentation  | 4            | Application    | TLS, JPEG, ASCII       | Data        |
| 5         | Session       | 4            | Application    | Session management     | Data        |
| 4         | Transport     | 3            | Transport      | TCP, UDP               | Segment / Datagram |
| 3         | Network       | 2            | Internet       | IP, ICMP               | Packet      |
| 2         | Data Link     | 1            | Link           | Ethernet, Wi-Fi, ARP   | Frame       |
| 1         | Physical      | 1            | Link           | Cables, radio, fiber   | Bits        |

---

## TCP Flags

| Flag | Name        | Purpose                                       | When You See It          |
|------|-------------|-----------------------------------------------|--------------------------|
| SYN  | Synchronize | Start a new connection                        | First packet of handshake |
| ACK  | Acknowledge | Confirm receipt of data or SYN/FIN            | Almost every packet       |
| FIN  | Finish      | Gracefully close a connection                 | End of session            |
| RST  | Reset       | Forcefully abort a connection                 | "Connection refused"      |
| PSH  | Push        | Deliver data immediately (don't buffer)       | Data packets              |
| URG  | Urgent      | Mark data as high priority                    | Rarely used               |

### tcpdump flag notation

| tcpdump Shows | Meaning      |
|---------------|--------------|
| `[S]`         | SYN          |
| `[S.]`        | SYN-ACK      |
| `[.]`         | ACK only     |
| `[P.]`        | PSH-ACK (data)|
| `[F.]`        | FIN-ACK      |
| `[R]`         | RST (reset)  |
| `[R.]`        | RST-ACK      |

---

## TCP Three-Way Handshake

```
    Client                          Server
      |                               |
      |  ──── SYN (seq=X) ────────>   |   Step 1: "I want to connect"
      |                               |
      |  <── SYN-ACK (seq=Y,ack=X+1)  |   Step 2: "OK, I accept"
      |                               |
      |  ──── ACK (ack=Y+1) ───────>  |   Step 3: "Confirmed, let's go"
      |                               |
      |  <=== Data flows both ways ==> |
      |                               |
```

### Connection teardown (four-way FIN)

```
    Client                          Server
      |                               |
      |  ──── FIN ─────────────────>  |   "I'm done sending"
      |  <──── ACK ────────────────   |   "Got it"
      |  <──── FIN ────────────────   |   "I'm done too"
      |  ──── ACK ─────────────────>  |   "Goodbye"
      |                               |
```

---

## TCP vs UDP Comparison

| Feature           | TCP                        | UDP                        |
|-------------------|----------------------------|----------------------------|
| Connection setup  | Three-way handshake        | None                       |
| Reliability       | Guaranteed delivery        | Best effort                |
| Ordering          | In-order delivery          | No ordering guarantee      |
| Flow control      | Yes (sliding window)       | No                         |
| Error detection   | Checksum + retransmission  | Checksum only              |
| Header size       | 20-60 bytes                | 8 bytes                    |
| Speed             | Slower (overhead)          | Faster (minimal overhead)  |
| State             | Stateful (tracks connection)| Stateless                 |

### Common protocols by transport

| Protocol | Transport | Port | Why This Transport?                              |
|----------|-----------|------|--------------------------------------------------|
| SSH      | TCP       | 22   | Every keystroke must arrive, in order             |
| HTTP     | TCP       | 80   | Web pages must load completely and correctly      |
| HTTPS    | TCP       | 443  | Same as HTTP, plus encryption                     |
| DNS      | UDP       | 53   | Small queries; retries if lost                    |
| DHCP     | UDP       | 67/68| Broadcast-based, clients don't have IPs yet       |
| NTP      | UDP       | 123  | Time sync; losing a packet is fine                |
| PostgreSQL| TCP      | 5432 | Database queries must be reliable                 |
| MySQL    | TCP       | 3306 | Database queries must be reliable                 |
| Redis    | TCP       | 6379 | Commands and responses must be reliable            |

---

## Encapsulation Diagram

```
Application Data:
  ┌──────────────────────────────────────┐
  │            "Hello"                   │
  └──────────────────────────────────────┘
                    │
                    ▼  TCP adds header
  ┌──────────┬──────────────────────────────────────┐
  │TCP Header│            "Hello"                   │
  │src:52431 │                                      │
  │dst:22    │                                      │
  └──────────┴──────────────────────────────────────┘
  = TCP Segment
                    │
                    ▼  IP adds header
  ┌──────────┬──────────┬──────────────────────────────────────┐
  │IP Header │TCP Header│            "Hello"                   │
  │src:10.0. │src:52431 │                                      │
  │dst:203.0.│dst:22    │                                      │
  └──────────┴──────────┴──────────────────────────────────────┘
  = IP Packet
                    │
                    ▼  Ethernet adds header + trailer
  ┌──────────┬──────────┬──────────┬───────────────────────┬─────┐
  │Eth Header│IP Header │TCP Header│       "Hello"         │ FCS │
  │dst MAC   │src IP    │src:52431 │                       │     │
  │src MAC   │dst IP    │dst:22    │                       │     │
  └──────────┴──────────┴──────────┴───────────────────────┴─────┘
  = Ethernet Frame (this goes on the wire)
```

**De-encapsulation** is the reverse: each layer strips its header and passes the payload up.

---

## tcpdump Common Commands

```bash
# Capture on loopback (local traffic)
sudo tcpdump -i lo0 -n -c 20 port 22

# Capture on Wi-Fi/Ethernet interface
sudo tcpdump -i en0 -n -c 30 host 93.184.216.34

# Capture DNS traffic
sudo tcpdump -i en0 -n port 53

# Capture TCP handshakes only (SYN packets)
sudo tcpdump -i en0 -n 'tcp[tcpflags] & (tcp-syn) != 0'

# Capture with timestamps and verbose headers
sudo tcpdump -i en0 -n -tttt -v port 22

# Save capture to file (open in Wireshark later)
sudo tcpdump -i en0 -n -w capture.pcap port 80

# Read a saved capture
tcpdump -r capture.pcap -n

# Show ASCII content of packets
sudo tcpdump -i en0 -n -A port 80

# Show hex and ASCII
sudo tcpdump -i en0 -n -X port 80
```

### tcpdump flag reference

| Flag     | What It Does                                    |
|----------|-------------------------------------------------|
| `-i IF`  | Listen on interface IF (lo0, en0, any)          |
| `-n`     | Don't resolve hostnames (faster, clearer)       |
| `-c N`   | Stop after N packets                            |
| `-v`     | Verbose (show TTL, IP options)                  |
| `-vv`    | More verbose                                    |
| `-tttt`  | Print human-readable timestamps                 |
| `-w FILE`| Write raw packets to file                       |
| `-r FILE`| Read packets from file                          |
| `-A`     | Print packet content as ASCII                   |
| `-X`     | Print packet content as hex + ASCII             |

### Common tcpdump filters

```bash
# By host
host 192.168.1.1
src host 192.168.1.1
dst host 10.0.0.1

# By port
port 22
src port 52431
dst port 443

# By protocol
tcp
udp
icmp

# Combine with and/or/not
tcp and port 22
host 10.0.0.1 and not port 22
port 80 or port 443
```

---

## Quick Reference: What Layer Am I Debugging?

| Symptom                        | Layer       | Tools                         |
|-------------------------------|-------------|-------------------------------|
| Can't resolve hostname         | Application | `dig`, `nslookup`, `host`    |
| Can't reach IP (ping fails)   | Internet    | `ping`, `traceroute`          |
| Port unreachable / refused     | Transport   | `nc -zv`, `lsof`, `netstat`  |
| Connection hangs or drops      | Transport   | `tcpdump`, Wireshark          |
| Wrong MAC / ARP issues         | Link        | `arp -a`, `tcpdump -e`       |
| Protocol error after connecting| Application | `curl -v`, `ssh -v`          |

---

[Back to Module 08 README](README.md) | [Module 08 Exercises](exercises.md)

[Back to main guide](../README.md)
