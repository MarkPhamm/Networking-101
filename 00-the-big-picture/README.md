# Module 00: The Big Picture

## What Actually Happens When You Type `ssh user@host`

Before we dive into individual topics, let's trace the **full journey** of an SSH connection from start to finish. This is the map for everything you'll learn in this guide. Each step maps to a module that covers it in depth.

When you couldn't SSH into your friend's server, the connection broke at one of these steps. By the end of this module, you'll know which step, why it broke, and where to go to fix it.

### Data engineering analogy

This is like tracing what happens when you run `spark.read.jdbc(url, table, properties)`. You don't just "connect to a database." Under the hood, Spark resolves the hostname, opens a TCP connection, negotiates the protocol, authenticates with your credentials, and only then does data start flowing. If any step fails, you get a cryptic error. Understanding the full chain turns cryptic errors into diagnosable problems.

---

## The Seven Steps

Here's what happens, in order, when you type:

```bash
ssh mark@my-server.example.com
```

```text
┌─────────────────────────────────────────────────────────┐
│                     YOUR TERMINAL                       │
│           $ ssh mark@my-server.example.com              │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 1. Shell Parses │
                  │    the Command  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 2. DNS Resolves │
                  │ hostname → IP   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 3. TCP Handshake│
                  │ SYN→SYN-ACK→ACK │
                  │    (port 22)    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 4. SSH Version  │
                  │    Exchange     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 5. Key Exchange │
                  │ (Diffie-Hellman)│
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 6. User Auth    │
                  │ (password/key)  │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ 7. Channel Open │
                  │ You get a shell │
                  └─────────────────┘
```

Let's walk through each one.

---

## Step 1: Shell Parses the Command

**What happens**: Your shell (zsh or bash) receives the command `ssh mark@my-server.example.com` and breaks it apart:

- **Program to run**: `ssh` (found at `/usr/bin/ssh`)
- **User**: `mark` (the username on the remote machine)
- **Host**: `my-server.example.com` (where to connect)
- **Port**: `22` (the default, since you didn't specify `-p`)

The shell also checks your `~/.ssh/config` file. If you have a `Host` entry matching `my-server.example.com`, it can override the username, port, identity file, and other options. This is why `~/.ssh/config` is so powerful -- it's the first thing SSH consults.

**What can go wrong**: Almost nothing at this step. If you mistype `shh` instead of `ssh`, the shell just says "command not found."

**Covered in depth**: [Module 02 - Shell and Keys](../02-shell-and-keys/)

---

## Step 2: DNS Resolution (Hostname to IP Address)

**What happens**: Your machine needs to convert `my-server.example.com` into an IP address like `203.0.113.42`. It sends a DNS query, typically to the DNS server your router told it about (often your ISP's server, or `8.8.8.8` if you configured Google's DNS).

The resolution process:

1. Check local cache (have we looked this up recently?)
2. Check `/etc/hosts` (manual overrides)
3. Query DNS server
4. DNS server may query other DNS servers in a hierarchy (root → TLD → authoritative)
5. Answer comes back: `my-server.example.com → 203.0.113.42`

**If you typed an IP address directly** (like `ssh mark@203.0.113.42`), this step is skipped entirely.

**What can go wrong**:

- `Could not resolve hostname` -- DNS can't find the name
- Typo in the hostname
- You're offline (no DNS server reachable)
- The domain doesn't exist

**DE analogy**: This is the same thing that happens when your JDBC URL contains a hostname: `jdbc:postgresql://my-db-host:5432/analytics`. The driver resolves `my-db-host` to an IP before connecting.

**Covered in depth**: [Module 03 - IP Addressing and DNS](../03-ip-addressing-and-dns/)

---

## Step 3: TCP Three-Way Handshake

### First, what is TCP?

**TCP** (Transmission Control Protocol) is how two computers establish a reliable, ordered stream of bytes between each other. It lives one layer below whatever application is talking — SSH, HTTP, Postgres, Kafka, your Spark cluster. They all sit on top of TCP.

Why TCP exists, in four properties:

1. **Connection-oriented** -- both sides shake hands before any data flows, so there's an explicit "the connection is open" state and an explicit "it closed."
2. **Reliable** -- if a packet is dropped in transit, TCP re-sends it. The application never sees the loss.
3. **Ordered** -- bytes arrive in the same order they were sent, even if the underlying packets took different paths across the internet.
4. **Flow- and congestion-controlled** -- TCP slows itself down if the network or the receiver can't keep up.

The trade-off is latency: you pay for a handshake up front, and each byte waits its turn. The alternative, **UDP** (User Datagram Protocol), skips the handshake and the re-sends — "just throw the packet and hope it arrives" — which is why it's used for video calls, DNS queries, and gaming, where speed matters more than perfect delivery.

**Analogy**: TCP is a phone call -- you dial, the other side picks up, and then you speak knowing every word lands in order. UDP is a postcard -- you drop it in the mailbox and move on. Most of what you do as a data engineer is TCP under the covers: SQL queries, SSH, HTTPS, Kafka, gRPC.

**Ports**: TCP also introduces the concept of a **port** — a 16-bit number that lets one machine run many services at once. SSH lives on port 22, HTTPS on 443, Postgres on 5432. We cover ports in detail in Module 04.

Deep dive with the full packet format in [Module 08 — TCP/IP Stack](../08-tcp-ip-stack/).

### Back to the handshake

**What happens**: Now that your machine knows the IP address, it initiates a TCP connection to `203.0.113.42` on port `22`. Before any SSH data flows, the two machines must establish a TCP connection using the three-way handshake:

```text
Your Mac                      Server
   │                             │
   │──── SYN (port 22) ────────> │  "I want to connect"
   │                             │
   │<─── SYN-ACK ─────────────── │  "Acknowledged, I'm ready"
   │                             │
   │──── ACK ──────────────────> │  "Great, let's go"
   │                             │
   │    TCP connection open      │
```

This takes milliseconds on a local network, but can take seconds over the internet. Your machine picks a random **ephemeral port** (something like 52431) as the source port, and targets port 22 on the server.

**What can go wrong**:

- **"Connection refused"** -- The SYN reached the server, but nothing is listening on port 22. The server sends back a RST (reset) packet. This means the server is reachable but `sshd` isn't running or is on a different port.
- **"Connection timed out"** -- The SYN was sent but no response came back. The packets are being dropped by a firewall, the IP is wrong, or the server is down.

**DE analogy**: When your Spark job tries to read from Postgres and gets "Connection refused," this is the exact step that failed -- the TCP handshake to port 5432.

**Covered in depth**: [Module 04 - Ports and Services](../04-ports-and-services/) and [Module 08 - TCP/IP Stack](../08-tcp-ip-stack/)

---

## Step 4: SSH Version Exchange

**What happens**: The TCP connection is open, and now the SSH protocol begins. Both sides immediately exchange version strings:

```bash
Server sends: SSH-2.0-OpenSSH_9.6
Client sends: SSH-2.0-OpenSSH_9.7
```

This is a plain-text exchange -- it's the only part of an SSH session that isn't encrypted. Both sides verify they can speak the same SSH protocol version (SSH-2.0 is the standard; SSH-1.x is obsolete and insecure).

**What can go wrong**: Almost never an issue with modern systems. If you connect to port 22 and get back something that isn't an SSH version string, SSH will tell you the remote side isn't speaking SSH.

**Covered in depth**: [Module 01 - SSH and Remote Access](../01-ssh-and-remote-access/)

---

## Step 5: Key Exchange (Diffie-Hellman)

**What happens**: This is the cryptographic core of SSH. The client and server need to agree on a shared secret to encrypt everything that follows, **without ever sending the secret across the network**. They use a key exchange algorithm, typically a variant of Diffie-Hellman.

Here's the high-level idea:

1. Both sides agree on mathematical parameters (publicly shared, no secret here)
2. Each side generates a private random number and computes a public value from it
3. They exchange their public values
4. Each side combines the other's public value with its own private number
5. Both arrive at the **same shared secret** independently

Even if someone captured every packet, they couldn't compute the shared secret. This is the mathematical magic that makes SSH secure.

After the key exchange, both sides also verify the server's **host key**. This is where your `~/.ssh/known_hosts` file comes in -- your machine checks whether it has seen this server before and whether its identity matches.

**What can go wrong**:

- **"WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!"** -- The server's host key doesn't match what's in your `known_hosts`. Usually means the server was rebuilt or you're connecting to a different machine at the same IP.
- The first time you connect, SSH asks you to confirm the host key fingerprint.

**DE analogy**: This is similar to TLS/SSL setup when connecting to a database over an encrypted connection. The `sslmode=verify-full` parameter in a Postgres connection string does the same kind of server identity verification.

**Covered in depth**: [Module 01 - SSH and Remote Access](../01-ssh-and-remote-access/) and [Module 02 - Shell and Keys](../02-shell-and-keys/)

---

## Step 6: Authentication

**What happens**: The encrypted channel is established. Now the server needs to verify **who you are**. The server sends a list of authentication methods it accepts (typically `publickey,password`).

**Password authentication**:

1. Server prompts for a password
2. You type it (sent encrypted through the tunnel)
3. Server checks it against its user database

**Public key authentication**:

1. Your client offers a public key from `~/.ssh/id_ed25519.pub` (or similar)
2. The server checks if that key is in `~/.ssh/authorized_keys` for the user `mark`
3. If found, the server sends a challenge
4. Your client signs the challenge with the matching private key
5. Server verifies the signature -- proof that you hold the private key

**What can go wrong**:

- **"Permission denied (publickey,password)"** -- All authentication methods failed. Wrong password, wrong username, key not in `authorized_keys`, or wrong key.
- **"Permission denied (publickey)"** -- Server only accepts keys (no password), and your key wasn't accepted.

**Covered in depth**: [Module 02 - Shell and Keys](../02-shell-and-keys/)

---

## Step 7: Channel Opens -- You Get a Shell

**What happens**: Authentication succeeded. The client requests a **session channel**, and within it, requests a **pseudo-terminal** (pty) and a **shell**. The server starts a shell process (bash, zsh, etc.) running as the user `mark`, with its stdin/stdout/stderr connected through the encrypted SSH channel back to your terminal.

```bash
mark@my-server:~$
```

You're in. Every keystroke you type is encrypted, sent to the server, fed to the shell, and the output is encrypted and sent back. It feels like a local terminal, but every character crosses the network.

**What can go wrong**: Rarely fails at this point. If the user's shell is set to something invalid in `/etc/passwd`, or the user's home directory doesn't exist, you might get dropped immediately.

**Covered in depth**: [Module 01 - SSH and Remote Access](../01-ssh-and-remote-access/)

---

## The Full Picture: Module Map

| Step | What Happens | Where to Learn More |
| ------ | ------------- | ------------------- |
| 1. Shell parses command | Username, host, port extracted; `~/.ssh/config` consulted | [Module 02 - Shell and Keys](../02-shell-and-keys/) |
| 2. DNS resolution | Hostname converted to IP address | [Module 03 - IP Addressing and DNS](../03-ip-addressing-and-dns/) |
| 3. TCP handshake | SYN, SYN-ACK, ACK on port 22 | [Module 04 - Ports and Services](../04-ports-and-services/), [Module 08 - TCP/IP Stack](../08-tcp-ip-stack/) |
| 4. SSH version exchange | Both sides agree on SSH-2.0 | [Module 01 - SSH and Remote Access](../01-ssh-and-remote-access/) |
| 5. Key exchange | Diffie-Hellman, host key verification | [Module 01](../01-ssh-and-remote-access/), [Module 02](../02-shell-and-keys/) |
| 6. Authentication | Password or public key | [Module 02 - Shell and Keys](../02-shell-and-keys/) |
| 7. Channel opens | Shell session starts | [Module 01 - SSH and Remote Access](../01-ssh-and-remote-access/) |

---

## How Failures Map to Steps

When your SSH connection fails, the error message tells you which step broke:

| Error Message | Step That Failed | What to Check |
| -------------- | ----------------- | --------------- |
| `command not found: ssh` | Step 1 | Install OpenSSH or fix your PATH |
| `Could not resolve hostname` | Step 2 | DNS, hostname spelling, internet connection |
| `Connection timed out` | Step 3 | IP address, firewall, server is down |
| `Connection refused` | Step 3 | sshd not running, wrong port |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Step 5 | Server was rebuilt, or possible attack |
| `Permission denied` | Step 6 | Wrong password, wrong key, wrong username |

---

## Key Takeaways

1. **An SSH connection is not one thing -- it's seven steps**, each of which can fail independently.
2. **The error message tells you which step failed.** Learning to map errors to steps is the single most useful networking skill.
3. **Each step builds on the one before it.** DNS must succeed before TCP can start. TCP must succeed before SSH can negotiate. Encryption must be set up before authentication.
4. **This guide follows the same order.** Modules 01-08 each deep-dive into the concepts behind one or more of these steps.
5. **Every networked system follows a similar pattern.** Database connections, API calls, Spark cluster communication -- they all do some version of: resolve name, open connection, negotiate protocol, authenticate, exchange data.

---

Next: [Module 01 - SSH and Remote Access](../01-ssh-and-remote-access/) -- Deep-dive into the SSH protocol and common failure modes.

[Back to main guide](../README.md)
