# Module 06: Firewalls and NAT

## Overview

A firewall decides what traffic is allowed in and out of a network or device. NAT (Network Address Translation) remaps IP addresses as traffic crosses a network boundary, most commonly letting many devices on a private network share a single public IP. Together, they are the gatekeepers that sit between your local network and the rest of the internet.

If you have ever set up `GRANT` and `REVOKE` statements in a database to control who can access which tables, you already understand the core idea behind firewalls. And if you have used a reverse proxy or API gateway that maps external URLs to internal services, you understand NAT.

---

## What a Firewall Does

A firewall inspects network packets and decides whether to **allow** or **deny** them based on rules. Rules typically match on:

- **Source IP address** -- where the packet is coming from
- **Destination IP address** -- where the packet is going
- **Port number** -- which service (e.g., 80 for HTTP, 22 for SSH)
- **Protocol** -- TCP, UDP, ICMP, etc.
- **Direction** -- inbound (incoming) or outbound (outgoing)

A firewall without rules is like a database with no access controls -- everything gets through.

---

## Host-Based vs. Network Firewalls

### Host-Based Firewall

Runs on an individual machine and protects only that machine.

- macOS has a built-in firewall (System Settings > Network > Firewall)
- Linux has `iptables` / `nftables`
- Windows has Windows Defender Firewall

### Network Firewall

Sits at the boundary of a network (typically on a router or dedicated appliance) and protects all devices behind it.

- Your home router has a basic network firewall
- Enterprises use dedicated firewall appliances (Palo Alto, Fortinet, etc.)
- Cloud equivalents: AWS Security Groups, GCP Firewall Rules, Azure NSGs

```
Internet  <-->  [Network Firewall / Router]  <-->  [Switch]  <-->  Devices
                                                                    ^
                                                              Each device may
                                                              also run a host
                                                              firewall
```

---

## macOS Firewall

macOS has two firewall mechanisms:

### 1. Application Firewall (System Settings)

Found in **System Settings > Network > Firewall**. This is an application-level firewall that controls incoming connections per app. It is simple but limited -- it does not give you fine-grained control over ports or IPs.

### 2. PF (Packet Filter) -- `pfctl`

`pf` is a powerful, low-level packet filter inherited from BSD. It operates at the network level and can filter by IP, port, protocol, and direction. It is what you use for serious firewall work on macOS.

```bash
# Check if pf is enabled
sudo pfctl -s info | grep Status

# View current rules
sudo pfctl -s rules

# View NAT rules
sudo pfctl -s nat
```

---

## Firewall Rules: Ordered List, First Match Wins

Firewall rules are evaluated in order, from top to bottom. The **first rule that matches** a packet determines its fate. Subsequent rules are ignored for that packet.

```
Rule 1: ALLOW TCP from any to any port 443       <-- HTTPS traffic allowed
Rule 2: ALLOW TCP from any to any port 80        <-- HTTP traffic allowed
Rule 3: DENY  TCP from any to any port 22        <-- SSH blocked
Rule 4: ALLOW TCP from 10.0.0.0/8 to any port 22 <-- This NEVER fires for SSH
                                                      because Rule 3 already matched
Rule 5: DENY  all                                 <-- Default deny everything else
```

**Order matters.** If you put a broad DENY rule before a specific ALLOW rule, the ALLOW will never be reached. This is a common source of "why can't I connect?" troubleshooting.

Think of it like a series of `if/elif` statements -- once a condition matches, the rest are skipped.

---

## Stateful vs. Stateless Firewalls

### Stateless Firewall

Evaluates each packet in isolation. It has no memory of previous packets. If you allow outbound traffic on port 443, you also need a separate rule to allow the inbound reply packets.

### Stateful Firewall

Tracks active connections. When you initiate an outbound connection (e.g., your browser requests a web page), the firewall remembers this connection and **automatically allows the reply packets** without needing an explicit inbound rule.

```
Stateless:
  Rule: ALLOW outbound TCP port 443    --> Your request goes out
  Rule: ALLOW inbound TCP port 443     --> You NEED this or replies are blocked

Stateful:
  Rule: ALLOW outbound TCP port 443    --> Your request goes out
  (reply automatically allowed)        --> Firewall tracks the connection
```

Most modern firewalls (including pf on macOS, AWS Security Groups) are stateful. This is much easier to manage and more secure, because you do not need to open inbound ports for reply traffic.

---

## NAT (Network Address Translation)

NAT solves a fundamental problem: there are not enough public IPv4 addresses for every device to have one. Instead, your home network uses private IPs (e.g., `192.168.1.x`), and your router translates them to a single public IP when traffic leaves the network.

### How NAT Works

Your router maintains a **translation table** that maps internal connections to external ones:

```
Internal (Private)              External (Public)
192.168.1.10:54321   <--->     203.0.113.5:40001
192.168.1.20:54322   <--->     203.0.113.5:40002
192.168.1.10:54323   <--->     203.0.113.5:40003
```

When your laptop (`192.168.1.10`) makes a request to a web server:

1. Your laptop sends a packet: source `192.168.1.10:54321`, destination `93.184.216.34:443`
2. The router rewrites the source to: `203.0.113.5:40001` (public IP, mapped port)
3. The web server sees the request coming from `203.0.113.5:40001` and replies to that address
4. The router receives the reply, looks up `40001` in its translation table, and forwards the packet to `192.168.1.10:54321`

Your laptop never sees the public IP. The web server never sees the private IP. The router is the translator in the middle.

---

## SNAT vs. DNAT

### SNAT (Source NAT)

Rewrites the **source** address of outgoing packets. This is what your home router does -- it replaces your private IP with its public IP.

Use case: Many internal devices sharing one public IP to access the internet.

### DNAT (Destination NAT)

Rewrites the **destination** address of incoming packets. This is used for port forwarding -- directing incoming traffic on a specific port to a specific internal machine.

Use case: Hosting a web server on an internal machine but making it accessible from the internet.

```
SNAT (outbound):
  192.168.1.10 --> [Router rewrites source to 203.0.113.5] --> Internet

DNAT (inbound / port forwarding):
  Internet --> 203.0.113.5:8080 --> [Router rewrites dest to 192.168.1.50:80] --> Internal server
```

---

## Port Forwarding

Port forwarding is a specific type of DNAT. You configure your router to say: "Any incoming traffic on port X should be forwarded to internal IP Y on port Z."

### Example

You run a Minecraft server on `192.168.1.50:25565` at home. Your public IP is `203.0.113.5`. Without port forwarding, nobody on the internet can reach your server because your router does not know which internal device should receive the traffic.

With a port-forward rule:

```
External port 25565  -->  Forward to 192.168.1.50:25565
```

Now anyone can connect to `203.0.113.5:25565` and reach your server.

### Port Forwarding for SSH

A common scenario: your friend runs a server at `192.168.0.50:22` behind a router with public IP `203.0.113.5`. To make SSH accessible:

1. On the router, create a port-forward rule: external port `2222` to `192.168.0.50:22`
2. You SSH in with: `ssh -p 2222 user@203.0.113.5`
3. The router receives the connection on port `2222`, rewrites the destination to `192.168.0.50:22`, and forwards it

---

## Why SSH Fails in Practice

When SSH connections fail, the cause is almost always one of these:

1. **Firewall blocking port 22** -- A host-based or network firewall is denying inbound connections on port 22. Check both the target machine's firewall and any network firewalls in between.

2. **No port-forward rule through NAT** -- The target machine is behind a NAT router, and no rule tells the router to forward SSH traffic to the right internal IP.

3. **Wrong port** -- The SSH server is listening on a non-standard port (e.g., 2222 instead of 22), but you are connecting to port 22.

4. **SSH service not running** -- The `sshd` daemon is not started on the target machine.

### Troubleshooting Steps

```bash
# Test if the port is reachable
nc -zv target_ip 22

# Check if SSH is listening locally on the target
sudo lsof -i :22

# Check macOS firewall status
sudo pfctl -s info | grep Status

# Check if the service is running
sudo launchctl list | grep ssh
```

---

## Data Engineering Analogy

| Networking Concept | Data Engineering Equivalent |
|---|---|
| Firewall rules | **Database GRANT/REVOKE** -- explicit rules about who can access what. AWS Security Groups are firewalls for cloud resources, and you configure them the same way: allow port 5432 from this CIDR block. |
| First-match-wins | **If/elif logic in pipeline routing** -- the first matching condition determines the action. |
| Stateful firewall | **Connection pooling** -- the system tracks active connections so it does not need to re-authenticate every packet/query. |
| NAT | **Reverse proxy / API gateway** -- maps external addresses to internal services. Nginx forwarding `api.company.com/v1` to `internal-service:8080` is conceptually the same as NAT forwarding `public_ip:8080` to `192.168.1.50:80`. |
| Port forwarding | **Port mapping in Docker** -- `-p 8080:80` maps external port 8080 to container port 80. Same concept as router port forwarding. |
| SNAT | **Egress gateway** -- all outbound traffic from a VPC appears to come from a single NAT gateway IP, just like all home devices share one public IP. |

---

## Key Takeaways

1. Firewalls filter traffic based on IP, port, protocol, and direction. Rules are ordered -- first match wins.
2. Host-based firewalls protect individual machines. Network firewalls protect entire networks.
3. Stateful firewalls track connections and automatically allow reply traffic. This is the modern default.
4. NAT lets multiple private devices share one public IP by maintaining a translation table.
5. SNAT rewrites source addresses (outbound). DNAT rewrites destination addresses (inbound/port forwarding).
6. Port forwarding is how you make internal services reachable from the internet.
7. Most SSH failures come down to firewalls blocking the port or missing NAT/port-forward rules.
