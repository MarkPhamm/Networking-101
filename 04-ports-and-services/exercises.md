# Module 04 Exercises: Ports and Services

Work through these exercises in order. You'll go from observing port usage to creating your own network connections.

---

## Exercise 1: See What's Listening on Your Machine

**Goal:** Discover which processes are using network ports right now.

### Steps

**List all network connections:**

```bash
# Show all listening and established connections
# -i = internet connections, -P = show port numbers, -n = don't resolve hostnames
lsof -i -P -n | head -40
```

Read the output columns:
- **COMMAND** -- the process name
- **PID** -- process ID
- **USER** -- who owns the process
- **TYPE** -- IPv4 or IPv6
- **NAME** -- the address and port (e.g., `*:443 (LISTEN)` or `192.168.1.100:52431->142.250.80.46:443 (ESTABLISHED)`)

**Check specific ports:**

```bash
# Is anything listening on SSH port?
sudo lsof -i :22 -P -n

# Check common service ports
sudo lsof -i :80 -P -n     # HTTP
sudo lsof -i :443 -P -n    # HTTPS
sudo lsof -i :5432 -P -n   # PostgreSQL
sudo lsof -i :3306 -P -n   # MySQL
sudo lsof -i :6379 -P -n   # Redis
```

**Filter for listening ports only:**

```bash
# Show only processes that are LISTENING (servers waiting for connections)
lsof -i -P -n | grep LISTEN

# Using netstat as an alternative
netstat -an | grep LISTEN
```

### Questions to Answer

1. How many processes are listening on your machine right now? List three of them with their ports.
2. Do you see any ESTABLISHED connections? Where are they going? (These are active connections to remote servers.)
3. Is sshd running? What port is it on? If it's not listed, SSH connections to this machine would be refused.
4. Do you see any process listening on port 8080 or other high ports? What are they?

### What You Should See

You'll likely see processes like `mDNSResponder` (DNS), various browser connections (ESTABLISHED to port 443), and possibly development tools. Each listening port represents a service that's ready to accept connections. If you don't see sshd, that's exactly why SSH to your machine would fail.

---

## Exercise 2: Build a Client-Server Connection with Netcat

**Goal:** Create a real TCP connection from scratch and see raw network communication.

### Steps

**Terminal 1 -- Start a server:**

```bash
# Listen on port 8080 (this creates a server)
nc -l 8080
```

This process is now LISTENING on port 8080, just like sshd listens on port 22 or PostgreSQL listens on port 5432.

**Terminal 2 -- Connect as a client:**

```bash
# Connect to the server
nc localhost 8080
```

**Now chat:**

Type a message in Terminal 2 and press Enter. It appears in Terminal 1. Type in Terminal 1 -- it appears in Terminal 2. You've built a bidirectional TCP connection.

**Terminal 3 -- Verify the connection exists:**

```bash
# See the connection
lsof -i :8080 -P -n
```

You should see both the LISTEN state and an ESTABLISHED connection.

**Terminal 3 -- Send a raw HTTP request:**

Kill the client in Terminal 2 (Ctrl+C), restart the server in Terminal 1 (`nc -l 8080`), then:

```bash
# curl will send a real HTTP request to your netcat "server"
curl localhost:8080
```

Look at Terminal 1 -- you'll see the raw HTTP request that curl sent:

```
GET / HTTP/1.1
Host: localhost:8080
User-Agent: curl/7.79.1
Accept: */*
```

This is exactly what a web server like nginx receives on port 80. Netcat just shows you the raw bytes instead of processing them.

### Questions to Answer

1. When you ran `lsof -i :8080` with the connection active, did you see two entries? One LISTEN and one ESTABLISHED?
2. What ephemeral port did the client use? (Look at the source port in the ESTABLISHED connection.)
3. In the raw HTTP request from curl, what does the `Host:` header contain? Why is this important? (Hint: think about virtual hosting -- multiple websites on one IP.)
4. What happens if you try to start a second `nc -l 8080` in another terminal while the first is still running?

### What You Should See

This exercise demonstrates the fundamental client-server model. Every network service works this way -- a process binds to a port, listens for connections, and exchanges data. SSH, HTTP, database protocols -- they all start with this same pattern. The only difference is what happens after the connection is established (the application protocol).

---

## Exercise 3: Port Scanning Your Own Machine

**Goal:** Discover all open ports in the well-known range.

### Steps

**Scan ports 1-1024 on localhost:**

```bash
# Scan well-known port range
# -z = scan mode (don't send data), -v = verbose
nc -zv localhost 1-1024 2>&1 | grep succeeded
```

Note: This may take a minute. It tries to connect to each port and reports which ones accepted the connection.

**If the range scan is slow, try specific ports:**

```bash
# Check specific common ports one by one
for port in 22 25 53 80 443 3306 5432 6379 8080; do
    nc -zv localhost $port 2>&1 | grep -E "succeeded|refused"
done
```

**Cross-reference with lsof:**

```bash
# Compare: what lsof shows vs what the port scan found
lsof -i -P -n | grep LISTEN | sort -t: -k2 -n
```

### Questions to Answer

1. How many ports in the 1-1024 range are open? List each one and identify the service.
2. Does the port scan result match what `lsof` shows? Are there any differences?
3. For each open port, can you identify the process that's listening? Use `sudo lsof -i :<port> -P -n`.
4. Try scanning a few ports you know are closed: `nc -zv localhost 9999`. What does the output say? How does "Connection refused" differ from how it would look if a firewall was blocking (you'd see a timeout instead)?

### What You Should See

This is essentially what network security tools do -- they probe ports to see what's running. Each open port is a potential entry point. In a data engineering context, this is like checking which services are up in your cluster. If you expected PostgreSQL on 5432 and it's not in the scan results, the service is down.

---

## Exercise 4: Watch a Live SSH Connection

**Goal:** See both sides of an SSH connection -- client and server -- and identify ephemeral vs. well-known ports.

### Prerequisites

SSH must be enabled on your machine. On macOS:
- System Settings -> General -> Sharing -> Remote Login (toggle on)

### Steps

**Terminal 1 -- Check the baseline:**

```bash
# See sshd listening
sudo lsof -i :22 -P -n
```

You should see sshd in LISTEN state.

**Terminal 2 -- Create an SSH connection to yourself:**

```bash
ssh localhost
# Accept the host key if prompted, enter your password
# You're now SSH'd into your own machine
```

**Terminal 1 -- Observe the connection:**

```bash
# Now see the full picture
sudo lsof -i :22 -P -n
```

### Reading the Output

You should see something like:

```
COMMAND   PID   USER   TYPE  NAME
sshd      123   root   IPv4  *:22 (LISTEN)              # Server waiting
sshd      456   root   IPv4  127.0.0.1:22->127.0.0.1:52431 (ESTABLISHED)  # Server side
ssh       789   you    IPv4  127.0.0.1:52431->127.0.0.1:22 (ESTABLISHED)  # Client side
```

Three entries:
1. **sshd LISTEN** -- the server process, still waiting for more connections
2. **sshd ESTABLISHED** -- the server-side of your connection (spawned a child process)
3. **ssh ESTABLISHED** -- the client-side of your connection

**Open a second SSH session:**

```bash
# Terminal 3
ssh localhost
```

```bash
# Terminal 1 -- check again
sudo lsof -i :22 -P -n
```

Now you'll see five entries -- the original LISTEN, plus two ESTABLISHED pairs (one per SSH session), each with a different ephemeral port.

**Clean up:**

```bash
# Exit SSH sessions in Terminals 2 and 3
exit  # in each terminal

# Optionally disable Remote Login in System Settings
```

### Questions to Answer

1. What ephemeral port did your first SSH session use? What about the second?
2. Why does the sshd LISTEN entry persist even after connections are established? (What would happen if it disappeared?)
3. How does the OS distinguish between the two SSH sessions, given that both go to port 22?
4. If you run `who` inside your SSH session, what do you see? How does the system know you logged in via SSH vs. locally?
5. What happens to the ESTABLISHED entries when you type `exit` in the SSH session?

### What You Should See

This exercise reveals the full lifecycle of a connection. The server process (sshd) never stops listening -- it forks a child process for each new connection. The combination of source IP, source port, destination IP, and destination port is what makes each connection unique. This is the same model used by database connection pools -- PostgreSQL forks a backend process for each new client connection, each identified by a unique source port.

---

## Bonus Challenge

**Test "Connection Refused" vs. "Connection Timed Out":**

```bash
# Connection Refused -- port is closed, machine responds immediately
nc -zv localhost 9999 2>&1
# Expected: Connection refused (instant response)

# Connection to a real service -- succeeds
nc -zv localhost 22 2>&1
# Expected: Connection to localhost port 22 [tcp/ssh] succeeded!

# Timeout -- try a non-routable IP (packets go nowhere)
nc -zv -w 3 10.255.255.1 22 2>&1
# Expected: Connection timed out (waits 3 seconds, then gives up)
```

The difference matters for debugging:
- **Refused** = machine is reachable, service is not running. Fix: start the service.
- **Timed out** = something is blocking the packets (firewall, routing issue). Fix: check firewalls and network path.

This distinction will save you hours of debugging. In data engineering, "connection refused on 5432" means restart Postgres. "Connection timed out on 5432" means check security groups and network ACLs.
