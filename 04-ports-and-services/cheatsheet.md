# Module 04 Cheatsheet: Ports and Services

## Port Ranges

| Range | Name | Description |
|-------|------|-------------|
| 0--1023 | Well-Known | Standard services (requires root to bind) |
| 1024--49151 | Registered | Application services (no special privileges) |
| 49152--65535 | Ephemeral | Temporary source ports for outbound connections |

## Well-Known Ports

| Port | Service | Protocol | Description |
|-----:|---------|----------|-------------|
| 22 | SSH | TCP | Secure shell remote access |
| 25 | SMTP | TCP | Email sending |
| 53 | DNS | TCP/UDP | Domain name resolution |
| 80 | HTTP | TCP | Unencrypted web traffic |
| 110 | POP3 | TCP | Email retrieval |
| 143 | IMAP | TCP | Email retrieval |
| 443 | HTTPS | TCP | Encrypted web traffic (TLS) |
| 3306 | MySQL | TCP | MySQL database |
| 5432 | PostgreSQL | TCP | PostgreSQL database |
| 6379 | Redis | TCP | Redis key-value store |
| 8080 | Alt HTTP | TCP | Alternative HTTP (dev, proxies) |
| 8443 | Alt HTTPS | TCP | Alternative HTTPS |
| 9092 | Kafka | TCP | Apache Kafka broker |
| 27017 | MongoDB | TCP | MongoDB database |

## lsof Commands

```bash
# All network connections
lsof -i -P -n

# Listening ports only
lsof -i -P -n | grep LISTEN

# Check a specific port
sudo lsof -i :22 -P -n
sudo lsof -i :5432 -P -n

# Check a specific protocol (TCP only)
lsof -i TCP -P -n

# Check a specific process by PID
lsof -i -P -n -p 1234

# All connections to a specific remote host
lsof -i @192.168.1.50 -P -n
```

### lsof Flags

| Flag | Meaning |
|------|---------|
| -i | Internet connections |
| -P | Show port numbers (not service names) |
| -n | Don't resolve hostnames (faster) |
| -p PID | Filter by process ID |
| :PORT | Filter by port number |

## Netcat (nc) Commands

```bash
# Start a TCP server (listen on a port)
nc -l 8080

# Connect to a server
nc localhost 8080
nc 192.168.1.50 22

# Port scan (check if port is open)
nc -zv localhost 22

# Scan a range of ports
nc -zv localhost 1-1024 2>&1 | grep succeeded

# Connect with a timeout
nc -zv -w 3 hostname 22

# Send data through a connection
echo "Hello" | nc localhost 8080

# Simple file transfer (receiver)
nc -l 9090 > received_file.txt

# Simple file transfer (sender)
nc localhost 9090 < file_to_send.txt
```

### Netcat Flags

| Flag | Meaning |
|------|---------|
| -l | Listen mode (server) |
| -z | Scan mode (don't send data) |
| -v | Verbose output |
| -w N | Timeout after N seconds |
| -u | Use UDP instead of TCP |

## netstat Commands

```bash
# All listening ports
netstat -an | grep LISTEN

# All connections with port numbers
netstat -an

# Listening TCP ports
netstat -an -p tcp | grep LISTEN

# Statistics by protocol
netstat -s
```

## Connection States

| State | Meaning |
|-------|---------|
| LISTEN | Server waiting for incoming connections |
| ESTABLISHED | Active connection, data can flow |
| SYN_SENT | Client has sent connection request, waiting for response |
| SYN_RECEIVED | Server received request, sent acknowledgment |
| TIME_WAIT | Connection closed, waiting for lingering packets to expire |
| CLOSE_WAIT | Remote side closed, local side hasn't closed yet |
| FIN_WAIT_1 | Local side initiated close, waiting for acknowledgment |
| FIN_WAIT_2 | Local close acknowledged, waiting for remote close |
| CLOSED | Connection fully terminated |

## Quick Debugging

| Symptom | Likely Cause | Check With |
|---------|-------------|------------|
| Connection refused | Nothing listening on that port | `sudo lsof -i :PORT -P -n` |
| Connection timed out | Firewall blocking, or host unreachable | `nc -zv -w 3 host port` |
| Address already in use | Another process has the port | `sudo lsof -i :PORT -P -n`, then kill it |
| Can connect locally, not remotely | Service bound to 127.0.0.1, not 0.0.0.0 | Check service config for listen address |
| Intermittent connection issues | Too many TIME_WAIT connections | `netstat -an \| grep TIME_WAIT \| wc -l` |

## Common Fixes

```bash
# Find and kill process on a specific port
sudo lsof -i :8080 -P -n    # Find PID
kill <PID>                    # Graceful stop
kill -9 <PID>                 # Force kill (last resort)

# Check what a service is bound to
# Look for 0.0.0.0:PORT (all interfaces) vs 127.0.0.1:PORT (localhost only)
sudo lsof -i :5432 -P -n

# Enable SSH on macOS
# System Settings -> General -> Sharing -> Remote Login

# Check if sshd is running (Linux)
systemctl status sshd

# Restart a service (Linux)
sudo systemctl restart sshd
sudo systemctl restart postgresql
```

## Connection Error Decision Tree

```
Can't connect to host:port
    |
    +--> Connection refused?
    |       -> Nothing listening. Start the service.
    |       -> Check: sudo lsof -i :PORT
    |
    +--> Connection timed out?
    |       -> Firewall or routing issue.
    |       -> Check: firewall rules, security groups
    |
    +--> No route to host?
    |       -> Network path broken.
    |       -> Check: IP address, routing, network connectivity
    |
    +--> Connection reset?
            -> Service crashed or rejected you after connecting.
            -> Check: service logs
```
