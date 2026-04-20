# Module 09: Troubleshooting -- "I Can't SSH In"

## Overview

Something is broken. You cannot SSH into a server, a database connection is timing out, or a data pipeline is failing with a network error. This module gives you a systematic approach to diagnosing network problems -- working through the stack layer by layer, using specific tools at each step, and narrowing down the root cause instead of guessing.

If you have ever debugged a failed Spark job, you already know this process: check the data source, then the network path, then permissions, then the application. Network troubleshooting works the same way -- you work through the layers methodically until you find where things break.

---

## The Debugging Mindset

The most important principle: **be systematic, not random.** Do not start by tweaking SSH configs or rebooting servers. Start by confirming the most basic layer works, then move up.

Two approaches work:

- **Bottom-up (recommended for most issues):** Start at DNS/IP, then check network reachability, then port access, then the application.
- **Top-down:** Start with the error message and work backward to find which layer is failing.

Either way, the goal is the same: isolate which layer is broken and fix only that layer.

---

## The Diagnostic Flowchart

When you cannot connect to a remote server, walk through these steps in order. Each step tests a specific layer. When a step fails, you have found where the problem is.

### Step 1: Can You Resolve the Hostname?

**What you are testing:** DNS (translating a name to an IP address).

**Commands:**

```bash
# Basic DNS lookup
dig remote-server.example.com

# Alternative
nslookup remote-server.example.com

# Python equivalent
python3 -c "import socket; print(socket.getaddrinfo('remote-server.example.com', 22))"
```

**If this fails:**
- The hostname is wrong (typo)
- DNS is misconfigured on your machine (`/etc/resolv.conf`)
- The DNS server is unreachable
- The DNS record does not exist (ask your team if the hostname is correct)

**Cross-reference:** Module 03 (IP Addressing and DNS) covers how DNS resolution works.

### Step 2: Can You Reach the IP?

**What you are testing:** IP-level connectivity (routing, intermediate networks).

**Commands:**

```bash
# Ping the IP directly (bypass DNS)
ping -c 4 93.184.216.34

# Trace the path to see where packets are dropped
traceroute -n 93.184.216.34
```

**If ping fails:**
- The server may be down
- A router between you and the server is dropping traffic
- The server's firewall may be blocking ICMP (ping). This is common -- many servers disable ping responses. Do not stop here; try the next step even if ping fails.

**If traceroute stops at a specific hop:**
- That hop (or the one after it) is where traffic is being blocked or dropped
- If it stops at hop 1, your local network or default gateway is the problem

**Cross-reference:** Module 05 (Subnets and Routing) explains how routing tables and hop-by-hop forwarding work.

### Step 3: Can You Reach the Port?

**What you are testing:** TCP connectivity to the specific service port.

**Commands:**

```bash
# Test if TCP port 22 is open and accepting connections
nc -zv 93.184.216.34 22

# Alternative using telnet
telnet 93.184.216.34 22

# Python equivalent
python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
result = s.connect_ex(('93.184.216.34', 22))
print('Port open' if result == 0 else f'Port closed (error {result})')
s.close()
"
```

**If this fails (connection refused):**
- The service (sshd) is not running on the server
- The service is running but not listening on that port
- A host-based firewall on the server is rejecting the connection

**If this fails (connection timed out):**
- A firewall (network or host) is silently dropping the packets
- The port is not open and no rejection is being sent
- This is the most common scenario in cloud environments (security groups)

**Cross-reference:** Module 04 (Ports and Services) and Module 06 (Firewalls and NAT).

### Step 4: Is a Firewall Blocking?

**What you are testing:** Firewall rules on both sides.

**Check your side (outbound):**

```bash
# Are outbound connections to port 22 allowed?
# If you can reach other servers on port 22, your side is fine
nc -zv known-working-server.example.com 22
```

**Check the server side (inbound):**

```bash
# On the server (if you have other access, e.g., console):
# macOS
sudo pfctl -sr

# Linux
sudo iptables -L -n

# Check if sshd is listening
sudo lsof -i :22
# or
sudo netstat -tlnp | grep :22
```

**In cloud environments (AWS, GCP, Azure):**
- Check Security Groups (AWS) or equivalent
- Check Network ACLs
- Check route tables in the VPC
- Check if the instance has a public IP or if you need a bastion/VPN

**Cross-reference:** Module 06 (Firewalls and NAT).

### Step 5: Is NAT/Port Forwarding Configured?

**What you are testing:** Whether traffic is being correctly translated to reach the server.

If the server is behind NAT (common in home networks and some cloud setups):
- Verify port forwarding rules on the router or load balancer
- Ensure the public-facing port maps to port 22 on the internal server
- Check that the NAT device has the correct internal IP for the server

**Cross-reference:** Module 06 (Firewalls and NAT).

### Step 6: Are the Credentials Correct?

**What you are testing:** SSH authentication (keys, passwords, permissions).

**Commands:**

```bash
# Verbose SSH shows the authentication process step by step
ssh -v user@remote-server.example.com

# Extra verbose for more detail
ssh -vvv user@remote-server.example.com
```

**Look for these lines in verbose output:**
- `Offering public key: /Users/you/.ssh/id_rsa` -- your client is trying this key
- `Server accepts key` -- the key was accepted
- `Permission denied (publickey)` -- the key was rejected
- `Connection closed by remote host` -- something on the server rejected you after auth

**Common key/credential issues:**
- Wrong username
- Wrong key file (specify with `ssh -i /path/to/key`)
- Key not in the server's `~/.ssh/authorized_keys`
- Permissions too open on `~/.ssh` or key files (`chmod 700 ~/.ssh`, `chmod 600 ~/.ssh/id_rsa`)
- Server configured to reject password auth and you do not have the right key

**Cross-reference:** Module 02 (Shell and Keys).

### Step 7: Is the SSH Service Running?

**What you are testing:** The sshd daemon on the server itself.

If you have console access (e.g., cloud provider console, physical access):

```bash
# Check if sshd is running
systemctl status sshd        # Linux (systemd)
sudo launchctl list | grep ssh  # macOS

# Check sshd config for issues
sudo sshd -T | head -30

# Check sshd logs
sudo journalctl -u sshd -n 50   # Linux (systemd)
sudo log show --predicate 'process == "sshd"' --last 10m  # macOS
```

**Common sshd issues:**
- Service not started or crashed
- Listening on a non-standard port (check `Port` in `/etc/ssh/sshd_config`)
- Config file syntax error preventing startup
- Disk full preventing sshd from writing logs or creating session files

---

## Common Error Messages Decoded

| Error Message | Layer | Likely Cause | Fix |
|---|---|---|---|
| `Could not resolve hostname` | DNS (Step 1) | Bad hostname, DNS server down | Check spelling, check `/etc/resolv.conf`, try a different DNS server |
| `Network is unreachable` | Routing (Step 2) | No route to the destination network | Check routing table, default gateway, VPN connection |
| `No route to host` | Routing (Step 2) | The target network exists but the specific host cannot be reached | Check if the server is on the right subnet, check intermediate routers |
| `Connection timed out` | Firewall (Step 3-4) | Packets are being silently dropped | Check security groups, NACLs, host firewalls on both sides |
| `Connection refused` | Service (Step 3) | Port is closed -- nothing is listening | Verify the service is running and listening on the expected port |
| `Permission denied (publickey)` | Auth (Step 6) | SSH key not accepted | Check key file, authorized_keys, file permissions |
| `Host key verification failed` | Auth (Step 6) | Server's host key changed since last connection | The server was rebuilt or there is a MITM. Verify and update `known_hosts`. |
| `Connection reset by peer` | Service (Step 7) | Server actively terminated the connection | Check sshd logs, server-side firewall rules (e.g., fail2ban) |
| `Too many authentication failures` | Auth (Step 6) | SSH agent is trying too many keys before the right one | Use `ssh -i` to specify the correct key, or `ssh -o IdentitiesOnly=yes` |

---

## Data Engineering Analogy

Debugging a network connection failure maps directly to debugging a failed data pipeline:

| Network Debugging Step | Data Pipeline Equivalent |
|---|---|
| Can you resolve the hostname? | Can you resolve the database connection string? Is the hostname in your config correct? |
| Can you reach the IP? | Can you reach the data source? Is the VPN up? Is the staging bucket accessible? |
| Can you reach the port? | Is the database port open? Is the API endpoint responding? |
| Is the firewall blocking? | Are IAM permissions correct? Is the security group allowing your IP? |
| Are credentials correct? | Does your service account have the right database password or API key? |
| Is the service running? | Is the database instance actually running? Did someone stop the RDS instance? |

The approach is identical: start at the lowest layer, verify it works, move up. Do not guess -- test.

---

## Key Takeaways

1. Be systematic. Work through the stack from DNS to application, testing each layer.
2. "Connection timed out" and "Connection refused" mean very different things: timed out means a firewall is dropping packets; refused means nothing is listening.
3. Use `ssh -v` to see exactly where authentication fails.
4. In cloud environments, check security groups and NACLs before touching the server.
5. Traceroute shows you where in the network path things break down.
6. The tools are simple: `dig`, `ping`, `nc`, `traceroute`, `ssh -v`. The skill is knowing which one to use and in what order.
