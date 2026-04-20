# Module 08: The TCP/IP Stack

## What You'll Learn

- The OSI model (7 layers) and the TCP/IP model (4 layers) -- and why TCP/IP is the one that matters
- How each TCP/IP layer works: Link, Internet, Transport, Application
- TCP vs UDP: when reliability matters and when speed wins
- The TCP three-way handshake: SYN, SYN-ACK, ACK
- Encapsulation: how an SSH keystroke gets wrapped in headers as it travels down the stack
- De-encapsulation: how those headers get stripped off at the receiving end

---

## Why This Module Exists

You've already done hands-on work with every layer of the network stack. You've SSH'd into machines (Application), traced packets across routers (Internet), watched ARP resolve MAC addresses (Link), and scanned ports where services listen (Transport). You did all of that without a formal model.

This module gives you the model. It's the map after you've already walked the territory.

### Data engineering analogy

The TCP/IP stack is like an **ETL pipeline with transformation stages**. Data enters at the top (raw application data), and each layer adds its own metadata -- like audit columns, timestamps, and lineage tags. By the time the data reaches the wire, it's been wrapped in multiple layers of context. On the receiving end, each layer strips its metadata and passes the core data up to the next stage. Same data, progressively enriched and then un-enriched.

---

## Two Models: OSI vs TCP/IP

There are two models people use to describe network communication. You'll hear both, so you need to know both. But only one actually maps to real-world implementations.

### The OSI Model (7 Layers)

The **OSI (Open Systems Interconnection)** model is a conceptual framework developed in the 1980s. It breaks networking into seven layers:

| Layer | Name         | What It Does                            | Example           |
|-------|--------------|-----------------------------------------|--------------------|
| 7     | Application  | User-facing protocols                   | HTTP, SSH, DNS     |
| 6     | Presentation | Data formatting, encryption, compression| TLS, JPEG, ASCII   |
| 5     | Session      | Managing sessions between applications  | Session tokens     |
| 4     | Transport    | Reliable (or fast) delivery             | TCP, UDP           |
| 3     | Network      | Addressing and routing across networks  | IP, ICMP           |
| 2     | Data Link    | Frames on the local network             | Ethernet, Wi-Fi    |
| 1     | Physical     | Bits on the wire                        | Cables, radio waves|

The OSI model is useful as a **teaching tool** and a **common vocabulary**. When someone says "that's a Layer 3 problem," they mean it's a routing/IP issue. When they say "Layer 7 load balancer," they mean a load balancer that understands HTTP.

But the OSI model was designed by committee and doesn't match how real protocols are built. Layers 5 and 6 (Session, Presentation) are mostly theoretical -- in practice, applications handle those concerns themselves.

### The TCP/IP Model (4 Layers)

The **TCP/IP model** is what the internet actually runs on. It was designed by the people who built the protocols, not by a standards committee trying to describe them after the fact.

| Layer | TCP/IP Name       | OSI Equivalent     | What It Does                    | Protocols              |
|-------|-------------------|--------------------|---------------------------------|------------------------|
| 4     | Application       | Layers 5, 6, 7    | User-facing protocols and data  | SSH, HTTP, DNS, SMTP   |
| 3     | Transport         | Layer 4            | End-to-end delivery             | TCP, UDP               |
| 2     | Internet          | Layer 3            | Addressing and routing          | IP, ICMP               |
| 1     | Link (Network Access) | Layers 1, 2    | Local delivery on the wire      | Ethernet, Wi-Fi, ARP   |

Four layers. Clean. Practical. This is the model that matters for your day-to-day work.

### Which model should you use?

**TCP/IP for understanding how things actually work.** OSI for vocabulary. When a colleague says "Layer 7," translate that to "Application layer" in the TCP/IP model. When they say "Layer 2 switch," that maps to "Link layer" in TCP/IP.

For the rest of this module, we use the TCP/IP model.

---

## TCP/IP Layer 1: Link (Network Access)

The Link layer handles communication on the **local network** -- getting a frame from one device to another on the same physical segment (LAN). You explored this in Module 07.

### What happens at this layer

- Data is packaged into **Ethernet frames**
- Devices are identified by **MAC addresses** (e.g., `AA:BB:CC:DD:EE:FF`)
- **ARP** (Address Resolution Protocol) resolves IP addresses to MAC addresses on the local network
- Switches forward frames based on MAC addresses
- VLANs segment the broadcast domain

### Key points

- MAC addresses are only meaningful within a single LAN. They get rewritten at every router hop.
- When your laptop sends a packet to a remote server, the Ethernet frame is addressed to your **default gateway's MAC address** -- not the server's. The router takes it from there.
- ARP is a broadcast protocol: "Who has 192.168.1.1? Tell me your MAC address." This only works within the local broadcast domain.

### What you already know

- Viewing your ARP cache with `arp -a` (Module 07)
- How ARP requests and replies work (Module 07)
- MAC addresses, VLANs, and broadcast domains (Module 07)

---

## TCP/IP Layer 2: Internet (Network)

The Internet layer handles **addressing and routing** -- getting a packet from one network to another, potentially across the entire globe. You explored this in Modules 03 and 05.

### What happens at this layer

- Data is packaged into **IP packets**
- Devices are identified by **IP addresses** (e.g., `192.168.1.50` for IPv4, `2001:db8::1` for IPv6)
- **Routers** forward packets between networks using routing tables
- **TTL** (Time to Live) prevents packets from looping forever
- **ICMP** provides error messages and diagnostics (`ping`, `traceroute`)

### Key points

- IP is **connectionless** and **unreliable** by design. Each packet is routed independently. The Internet layer makes no guarantees about delivery, order, or duplicates. That's the Transport layer's job.
- Subnets and CIDR notation determine which IPs are "local" (same network) vs "remote" (need routing).
- NAT rewrites IP addresses at the boundary between private and public networks (Module 06).

### What you already know

- IPv4 addressing, public vs private IPs (Module 03)
- DNS resolving names to IP addresses (Module 03)
- Subnet masks, CIDR notation, routing tables (Module 05)
- NAT and port forwarding (Module 06)
- `ping` and `traceroute` for testing connectivity (Module 03/05)

---

## TCP/IP Layer 3: Transport

The Transport layer provides **end-to-end communication** between applications on different machines. This is where the two major protocols live: **TCP** and **UDP**.

Ports live at this layer. When you connected to SSH on port 22 or checked listening services with `lsof` (Module 04), you were working at the Transport layer.

### TCP: Reliable, Ordered, Connection-Oriented

**TCP (Transmission Control Protocol)** guarantees that data arrives completely, in order, and without corruption. It does this by establishing a connection before any data flows, numbering every byte, and requiring acknowledgment of receipt.

#### The Three-Way Handshake

Before any data is exchanged, TCP establishes a connection using a three-way handshake:

```
    Client                    Server
      |                         |
      |  1. SYN (seq=100)      |    "I want to connect. My starting
      |------------------------>|     sequence number is 100."
      |                         |
      |  2. SYN-ACK            |    "Got it. I accept. My starting
      |  (seq=300, ack=101)    |     sequence number is 300.
      |<------------------------|     I expect your next byte to be 101."
      |                         |
      |  3. ACK (ack=301)      |    "Confirmed. I expect your next
      |------------------------>|     byte to be 301. Let's go."
      |                         |
      |  Data flows both ways   |
      |<========================|
      |========================>|
```

1. **SYN**: The client picks a random starting sequence number and sends a SYN (synchronize) packet to the server.
2. **SYN-ACK**: The server picks its own sequence number and acknowledges the client's by sending back SYN + ACK.
3. **ACK**: The client acknowledges the server's sequence number. The connection is now established.

This whole exchange typically takes one round-trip time (RTT) -- a few milliseconds on a LAN, 50-200ms across the internet.

#### Data engineering analogy

The TCP handshake is like **connection pool session setup**. When SQLAlchemy opens a new connection to PostgreSQL:
- **SYN** = "I'd like a connection, please" (connect request)
- **SYN-ACK** = "Connection allocated, ready for queries" (server ready)
- **ACK** = "Confirmed, sending queries" (client begins using the connection)

Once established, data flows through the connection like queries through a pool. If a query doesn't get acknowledged, it's retransmitted -- just like TCP retransmits lost segments.

#### How TCP Ensures Reliability

After the handshake, TCP uses several mechanisms to guarantee delivery:

- **Sequence numbers**: Every byte of data is numbered. The receiver knows if bytes are missing or out of order.
- **Acknowledgments (ACKs)**: The receiver tells the sender "I got everything up to byte N." If the sender doesn't get an ACK within a timeout, it retransmits.
- **Flow control**: The receiver advertises how much buffer space it has (receive window). The sender won't overwhelm a slow receiver.
- **Congestion control**: TCP detects network congestion (via packet loss or delay) and slows down to avoid making it worse.
- **Retransmission**: Lost packets are automatically re-sent.
- **Checksums**: Every segment includes a checksum to detect corruption.

#### Connection Teardown (FIN)

When the conversation is done, TCP closes the connection cleanly:

```
    Client                    Server
      |                         |
      |  FIN                    |    "I'm done sending."
      |------------------------>|
      |                         |
      |  ACK                    |    "Got it."
      |<------------------------|
      |                         |
      |  FIN                    |    "I'm done sending too."
      |<------------------------|
      |                         |
      |  ACK                    |    "Got it. Connection closed."
      |------------------------>|
```

This is the four-way FIN teardown. You'll see FIN and ACK packets in tcpdump when an SSH session ends or an HTTP connection closes.

#### TCP Flags Summary

TCP headers contain flag bits that control the connection:

| Flag | Name         | Meaning                                      |
|------|-------------|----------------------------------------------|
| SYN  | Synchronize | Initiate a connection                         |
| ACK  | Acknowledge | Confirm receipt of data or a SYN              |
| FIN  | Finish      | Gracefully close a connection                 |
| RST  | Reset       | Forcefully abort a connection                 |
| PSH  | Push        | Deliver data to the application immediately   |
| URG  | Urgent      | Mark data as urgent (rarely used)             |

When you see "Connection refused," that's the server sending a **RST** packet -- "I don't have anything listening on that port, go away."

### UDP: Fast, Simple, Connectionless

**UDP (User Datagram Protocol)** takes the opposite approach from TCP. No handshake, no sequence numbers, no acknowledgments, no retransmission. You send a datagram and hope it arrives.

| Feature           | TCP                          | UDP                          |
|-------------------|------------------------------|------------------------------|
| Connection        | Connection-oriented (handshake) | Connectionless (fire and forget) |
| Reliability       | Guaranteed delivery          | Best-effort delivery          |
| Ordering          | Bytes arrive in order        | Datagrams may arrive out of order |
| Overhead          | Higher (headers, state, ACKs)| Lower (minimal headers)      |
| Speed             | Slower (waits for ACKs)      | Faster (no waiting)          |
| Use cases         | SSH, HTTP, database queries  | DNS lookups, video streaming, gaming |

#### Why use UDP?

Because sometimes **speed matters more than perfection**:

- **DNS queries**: A single question-and-answer exchange. If the response is lost, the client just asks again. Setting up a full TCP connection for one small query is wasteful overhead.
- **Video streaming / voice calls**: If a video frame is lost, you don't want to pause playback to wait for a retransmission. Just show the next frame. The user won't notice a single dropped frame, but they will notice a buffering delay.
- **Gaming**: Player position updates are sent 60 times per second. If one update is lost, the next one arrives 16ms later with newer data anyway. Retransmitting stale data would actually make things worse.
- **Metrics/logging**: Systems like StatsD send metrics over UDP. If a metric is lost, the next one is coming in a second anyway.

#### Data engineering analogy

TCP is like a **transactional database write** -- every row is acknowledged and committed, with rollback on failure. UDP is like **fire-and-forget event streaming** (think: Kafka producers with `acks=0`) -- you blast messages out and trust that most of them arrive. Losing one metric data point is fine; losing a financial transaction is not.

### Ports: Addressing at the Transport Layer

Ports were covered in Module 04, but they belong to the Transport layer conceptually. While IP addresses identify **which machine** to reach, ports identify **which application** on that machine.

- **Source port**: An ephemeral (temporary) port assigned by the operating system (e.g., 52431). Identifies the client's side of the connection.
- **Destination port**: The well-known port of the service (e.g., 22 for SSH, 443 for HTTPS, 5432 for PostgreSQL).

A full connection is uniquely identified by the tuple: `(source IP, source port, destination IP, destination port, protocol)`.

---

## TCP/IP Layer 4: Application

The Application layer is where the protocols you interact with every day live. This layer defines the format and meaning of the actual data being exchanged.

You've already worked with Application layer protocols throughout this course:

| Protocol | Purpose                    | Transport | Port | Where You Learned It |
|----------|----------------------------|-----------|------|----------------------|
| SSH      | Secure remote shell access | TCP       | 22   | Modules 01, 02       |
| HTTP     | Web requests               | TCP       | 80   | Module 04            |
| HTTPS    | Encrypted web requests     | TCP       | 443  | Module 04            |
| DNS      | Name resolution            | UDP (usually), TCP for large responses | 53 | Module 03 |
| SMTP     | Sending email              | TCP       | 25   | (referenced)         |
| DHCP     | Automatic IP assignment    | UDP       | 67/68| Module 03            |

The Application layer doesn't care how data gets delivered -- that's the Transport layer's job. HTTP just produces a request like `GET /index.html HTTP/1.1` and hands it to TCP. SSH produces encrypted shell data and hands it to TCP. DNS produces a query and hands it to UDP (usually).

---

## Encapsulation: Wrapping Data Layer by Layer

Encapsulation is the core mechanism of the TCP/IP stack. As data moves **down** the stack from application to wire, each layer **wraps** the previous layer's data in a new header. Like a letter going into an envelope, going into a shipping box, going into a delivery truck.

### Example: An SSH Keystroke

You press the letter "a" in an SSH session connected to a remote server. Here's what happens:

```
Layer 4 - Application:
  SSH encrypts the keystroke
  ┌─────────────────────────────┐
  │ SSH encrypted data ("a")    │
  └─────────────────────────────┘
              │
              ▼
Layer 3 - Transport (TCP):
  Adds source port, destination port, sequence number, flags
  ┌──────────────────┬─────────────────────────────┐
  │ TCP Header       │ SSH encrypted data ("a")    │
  │ src:52431 dst:22 │                             │
  │ seq:1001 ack:500 │                             │
  └──────────────────┴─────────────────────────────┘
              │
              ▼
Layer 2 - Internet (IP):
  Adds source IP, destination IP, TTL, protocol
  ┌──────────────────┬──────────────────┬──────────────────────┐
  │ IP Header        │ TCP Header       │ SSH data ("a")       │
  │ src:192.168.1.10 │ src:52431 dst:22 │                      │
  │ dst:203.0.113.50 │ seq:1001 ack:500 │                      │
  │ TTL:64 proto:TCP │                  │                      │
  └──────────────────┴──────────────────┴──────────────────────┘
              │
              ▼
Layer 1 - Link (Ethernet):
  Adds source MAC, destination MAC, frame type
  ┌──────────────────┬──────────────────┬──────────────┬──────────┬──────────┐
  │ Ethernet Header  │ IP Header        │ TCP Header   │ SSH data │ Eth FCS  │
  │ src:AA:BB:CC:... │ src:192.168.1.10 │ src:52431    │  ("a")   │ checksum │
  │ dst:11:22:33:... │ dst:203.0.113.50 │ dst:22       │          │          │
  └──────────────────┴──────────────────┴──────────────┴──────────┴──────────┘
```

This final Ethernet frame is what actually goes out on the wire as electrical signals (or radio waves over Wi-Fi).

### Data engineering analogy

Encapsulation is like **an ETL pipeline where each stage adds metadata columns**:

| TCP/IP Layer  | ETL Stage        | What Gets Added                        |
|---------------|------------------|----------------------------------------|
| Application   | Source system     | Raw data (the business payload)        |
| Transport     | Extraction       | Audit columns: batch_id, sequence_num  |
| Internet      | Transformation   | Routing metadata: source, destination  |
| Link          | Loading          | Physical delivery info: partition, format|

Each stage enriches the data with context needed by that stage. The core payload stays the same; the wrapping grows.

---

## De-encapsulation: Unwrapping at the Other End

When the frame arrives at the destination, the process reverses. Each layer **strips its header**, reads the information it needs, and passes the remaining data up:

```
Wire → Ethernet frame arrives at server's NIC

Layer 1 - Link:
  NIC checks destination MAC (is it for me?). Strips Ethernet header.
  Passes IP packet up.

Layer 2 - Internet:
  Checks destination IP (is it for me?). Strips IP header.
  Notes protocol field says TCP. Passes TCP segment up.

Layer 3 - Transport:
  Checks destination port (22 = SSH). Strips TCP header.
  Passes data to the SSH process listening on port 22.

Layer 4 - Application:
  SSH decrypts the data. The letter "a" appears on the remote terminal.
```

The server then sends back a response (the terminal echo of "a"), and the whole process happens in reverse: the response travels down the stack on the server, across the network, and up the stack on the client.

---

## Putting It All Together: A Packet's Life

Let's trace a complete SSH connection from your Mac to a remote server, referencing every module:

1. **You type `ssh mark@remote-server.com`** (Module 01)

2. **DNS resolution** (Module 03): Your Mac asks a DNS resolver to translate `remote-server.com` into an IP address. The query goes over **UDP port 53**. Answer: `203.0.113.50`.

3. **Routing decision** (Module 05): Your Mac checks its routing table. `203.0.113.50` is not on the local subnet, so the packet must go to the **default gateway** (your router).

4. **ARP** (Module 07): Your Mac needs the gateway's MAC address. It checks the ARP cache or sends an ARP broadcast on the LAN.

5. **TCP three-way handshake** (this module): Your Mac sends SYN to `203.0.113.50:22`. The SYN packet is encapsulated in IP (with TTL, src/dst IP) and then in an Ethernet frame (addressed to the gateway's MAC).

6. **Routing across the internet** (Module 05): The packet hops through multiple routers. Each router decrements the TTL, rewrites the Ethernet header (new src/dst MAC for each hop), but leaves the IP addresses and TCP ports unchanged.

7. **NAT** (Module 06): If the server is behind a NAT/firewall, the router at the destination network translates the public IP to a private one and forwards the packet.

8. **SYN-ACK comes back**, traversing the same path in reverse. Then your Mac sends ACK. Connection established.

9. **SSH key exchange and authentication** (Module 02): Encrypted application data flows over the TCP connection.

10. **Port 22** (Module 04): The server's operating system delivers the TCP segments to the `sshd` process listening on port 22.

11. **You type commands, they execute, output comes back** -- all flowing through the same TCP connection, encapsulated and de-encapsulated at every hop.

---

## Key Takeaways

1. **The TCP/IP model has four layers**: Link, Internet, Transport, Application. This is what the internet actually uses.
2. **The OSI model has seven layers** and is useful for vocabulary ("Layer 7 firewall"), but TCP/IP is what you implement against.
3. **TCP is reliable**: three-way handshake, sequence numbers, ACKs, retransmission. Use it when every byte matters (SSH, HTTP, databases).
4. **UDP is fast**: no connection setup, no guarantees. Use it when speed beats completeness (DNS, video, metrics).
5. **Encapsulation wraps data in headers** as it moves down the stack. De-encapsulation strips them going up.
6. **Each layer has a job**: Application provides meaning, Transport provides delivery, Internet provides addressing, Link provides local transmission.
7. **Everything connects**: DNS (Module 03) feeds IP addresses to the Internet layer. Ports (Module 04) live at the Transport layer. Firewalls (Module 06) operate at multiple layers. ARP (Module 07) bridges the Internet and Link layers.

---

Next: You've completed all eight modules. Check the [Appendix](../appendix/) for a complete glossary, troubleshooting guide, and data engineering analogy reference.

[Back to main guide](../README.md)
