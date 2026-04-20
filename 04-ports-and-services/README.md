# Module 04: Ports and Services

## Why This Matters

Now you know that an IP address identifies a machine on a network. But a single server might be running SSH, a web server, a database, and a dozen other services simultaneously. When a packet arrives at that server, how does the operating system know which service should receive it?

That's what **ports** are for.

When your SSH connection was refused, the error message likely said something like "Connection refused on port 22." Understanding ports tells you exactly what that means and how to diagnose it.

---

## What Is a Port?

A port is a **16-bit number (0--65535)** that identifies a specific service or process on a machine. Think of it this way:

- The **IP address** is the building's street address.
- The **port** is the apartment number inside that building.

A network connection is always defined by a full **socket pair**: `IP:port` on both ends. When you SSH into a server, the full picture looks like:

```
Your machine           Server
192.168.1.100:52431 -> 143.198.67.42:22
   (your IP:random)     (server IP:SSH port)
```

---

## Why Ports Exist

Without ports, each machine could only run **one** network service. You'd need a separate server for SSH, another for your web app, another for your database. Ports let a single IP host thousands of services simultaneously -- each one listens on a different port number.

```
Server 143.198.67.42:
    Port 22   -> sshd (SSH daemon)
    Port 80   -> nginx (web server)
    Port 443  -> nginx (HTTPS)
    Port 5432 -> PostgreSQL
    Port 6379 -> Redis
    Port 8080 -> your application
```

---

## Port Ranges

The 65,536 available ports are divided into three ranges:

### Well-Known Ports: 0--1023

Reserved for standard services. On most operating systems, **only root/admin processes can bind to ports below 1024**. This is a security measure -- it prevents a regular user from impersonating a system service.

### Registered Ports: 1024--49151

Used by applications and services that have registered their port with IANA (Internet Assigned Numbers Authority). Databases, message queues, and application servers typically live here. No special privileges required.

### Ephemeral (Dynamic) Ports: 49152--65535

Used as **temporary source ports** when your machine initiates an outbound connection. The OS picks a random port from this range for each new connection. More on this below.

---

## Well-Known Ports You Should Memorize

| Port | Service | What It Does |
|-----:|---------|--------------|
| 22 | SSH | Secure remote shell access |
| 25 | SMTP | Sending email |
| 53 | DNS | Domain name resolution |
| 80 | HTTP | Unencrypted web traffic |
| 443 | HTTPS | Encrypted web traffic (TLS) |
| 3306 | MySQL | MySQL database |
| 5432 | PostgreSQL | PostgreSQL database |
| 6379 | Redis | Redis in-memory data store |
| 8080 | Alt HTTP | Common alternative HTTP port (dev servers, proxies) |

You'll encounter these constantly. When someone says "check if Postgres is running," they mean "is anything listening on port 5432?"

---

## Listening vs. Established Connections

A service must **listen** on a port before it can accept connections. There are two key connection states to understand:

### LISTEN

A process has bound to a port and is waiting for incoming connections. This is a server waiting for clients.

```
sshd     LISTEN    *:22        # SSH daemon waiting for connections
postgres LISTEN    *:5432      # PostgreSQL waiting for connections
```

### ESTABLISHED

A connection is active between a client and server. Data can flow in both directions.

```
ssh      ESTABLISHED  192.168.1.100:52431 -> 143.198.67.42:22
```

You can see both states using tools like `lsof` and `netstat`, which we'll use in the exercises.

---

## Process-to-Port Binding: One Port, One Process

A critical rule: **only one process can listen on a given port at a time** (per IP address).

If PostgreSQL is already listening on port 5432 and you try to start a second instance on the same port:

```
FATAL: could not bind to port 5432: Address already in use
```

This is one of the most common errors in development. The fix is either:
1. Stop the existing process using that port
2. Configure the new process to use a different port

```bash
# Find what's using port 5432
sudo lsof -i :5432

# Kill it if needed
kill <PID>
```

---

## Ephemeral Ports: The Client Side

When your machine connects to a server, it needs a **source port** for the return traffic. The OS automatically assigns a random **ephemeral port** from the high range (typically 49152--65535).

```
Your SSH connection:
  Source:      192.168.1.100:52431   (ephemeral -- randomly chosen)
  Destination: 143.198.67.42:22     (well-known -- SSH)
```

You don't choose this port -- the OS handles it. Each new connection gets a different ephemeral port, which is how your machine can have multiple simultaneous connections to the same server and port:

```
Terminal 1:  192.168.1.100:52431 -> 143.198.67.42:22
Terminal 2:  192.168.1.100:52432 -> 143.198.67.42:22
Browser:     192.168.1.100:52433 -> 143.198.67.42:443
```

Each connection is uniquely identified by the combination of source IP, source port, destination IP, and destination port.

---

## "Connection Refused" -- What It Really Means

This is probably the error that brought you here. When you see:

```
ssh: connect to host 143.198.67.42 port 22: Connection refused
```

It means your packets **reached the server**, but **nothing is listening on port 22**. The server's OS actively rejected the connection by sending back a TCP RST (reset) packet.

This is different from:

| Error | What It Means | The Packet... |
|-------|---------------|---------------|
| **Connection refused** | Port is closed (nothing listening) | Reached the server, got rejected |
| **Connection timed out** | Port may be blocked by a firewall | Never got a response |
| **No route to host** | Can't reach the machine at all | Couldn't find a path to the IP |

"Connection refused" on port 22 means one of:
1. **sshd is not running** -- the SSH service hasn't been started
2. **sshd is listening on a different port** -- some admins change SSH to a non-standard port for security
3. **sshd is bound to a different IP** -- it might be listening on localhost only, not the public interface

---

## Data Engineering Analogy

If you've managed databases and data pipelines, ports are already familiar:

- **Port 5432 is PostgreSQL's front door.** When your Airflow DAG connects to Postgres, it's sending packets to `db-host:5432`. "Connection refused on 5432" means Postgres isn't running -- the same diagnosis applies to SSH on port 22.

- **Ports are like database listener configurations.** In PostgreSQL, `listen_addresses` and `port` in `postgresql.conf` control which IP and port Postgres binds to. sshd has the same concept with `ListenAddress` and `Port` in `/etc/ssh/sshd_config`.

- **Ephemeral ports are like connection pool source ports.** When your Spark cluster opens 100 connections to a database, each connection has a unique ephemeral source port. The database sees 100 different connections, all going to port 5432 but coming from different source ports.

- **"Address already in use" errors** happen in data engineering too. If you try to start two Jupyter servers on port 8888, the second one fails because the port is already taken. Same principle as any port conflict.

- **Port ranges in security groups** are like database firewall rules. When you configure an AWS security group to allow inbound on port 5432 from your VPC CIDR, you're saying "let database traffic through this numbered door from these addresses."

---

## Key Takeaways

1. **Ports are numbered endpoints (0--65535)** that identify services on a machine. IP gets you to the machine; the port gets you to the service.
2. **Well-known ports (0--1023)** are for standard services: 22 (SSH), 80 (HTTP), 443 (HTTPS), 5432 (PostgreSQL).
3. **Only one process can listen on a port at a time.** "Address already in use" means something else has the port.
4. **Ephemeral ports (49152--65535)** are automatically assigned for outbound connections.
5. **"Connection refused"** = packets reached the server, but nothing is listening on that port. It's a clear signal, not a mystery.
6. **"Connection timed out"** = packets may be blocked by a firewall. This is a different problem (covered in a later module).

---

Next: [Exercises](exercises.md) | [Cheatsheet](cheatsheet.md)
