# Module 06: Cheatsheet -- Firewalls and NAT

---

## Firewall Concepts

| Concept               | Description                                                        |
|-----------------------|--------------------------------------------------------------------|
| Firewall              | Filters traffic based on rules (IP, port, protocol, direction)     |
| Host-based firewall   | Runs on a single machine, protects that machine only               |
| Network firewall      | Sits at network boundary, protects all devices behind it           |
| Rule order            | First match wins -- order matters                                  |
| Default deny          | Best practice: deny everything, then explicitly allow what's needed|
| Stateless firewall    | Evaluates each packet independently, no connection tracking        |
| Stateful firewall     | Tracks connections, auto-allows reply packets                      |

---

## macOS Firewall Commands (pfctl)

### Status and Info

```bash
# Check if pf is enabled
sudo pfctl -s info | grep Status

# View all loaded rules
sudo pfctl -s rules

# View NAT rules
sudo pfctl -s nat

# View state table (active connections tracked by pf)
sudo pfctl -s state

# View statistics
sudo pfctl -s info
```

### Enable / Disable

```bash
# Enable pf
sudo pfctl -e

# Disable pf
sudo pfctl -d
```

### Loading Rules

```bash
# Load rules from file
sudo pfctl -f /etc/pf.conf

# Load rules from a custom file
sudo pfctl -f /path/to/rules.conf

# Test rules without loading (syntax check)
sudo pfctl -n -f /path/to/rules.conf
```

### Basic pf Rule Syntax

```
action  direction  [log]  [quick]  on interface  proto protocol \
    from source  to destination  port port_number

# Examples:
block in on en0 proto tcp from any to any port 22
pass out on en0 proto tcp from any to any port 443
pass in quick on en0 proto tcp from 10.0.0.0/8 to any port 22
```

| Keyword   | Meaning                                           |
|-----------|---------------------------------------------------|
| `block`   | Deny the packet                                   |
| `pass`    | Allow the packet                                  |
| `in`      | Inbound traffic                                   |
| `out`     | Outbound traffic                                  |
| `quick`   | Stop processing rules if this one matches         |
| `on en0`  | Apply to specific interface                       |
| `proto`   | Protocol (tcp, udp, icmp)                         |
| `from`    | Source IP/network                                 |
| `to`      | Destination IP/network                            |
| `port`    | Port number or range                              |

---

## NAT Types

| Type            | What It Does                                          | Direction | Example                                           |
|-----------------|-------------------------------------------------------|-----------|---------------------------------------------------|
| SNAT            | Rewrites source IP (private to public)               | Outbound  | Home devices sharing one public IP                |
| DNAT            | Rewrites destination IP (public to private)          | Inbound   | Port forwarding to internal server                |
| PAT / Masquerade| SNAT using port numbers to multiplex connections     | Outbound  | Most home routers (many devices, one IP)          |
| 1:1 NAT         | Maps one public IP to one private IP                 | Both      | Dedicated public IP for a specific server         |

---

## Port Forwarding

### Concept

```
Internet  -->  [Router Public IP:External Port]  -->  [Internal IP:Internal Port]
```

### Router Configuration (typical web interface fields)

| Field          | Example Value    | Meaning                              |
|----------------|------------------|--------------------------------------|
| External Port  | 2222             | Port the internet connects to        |
| Internal IP    | 192.168.1.50     | Private IP of the target device      |
| Internal Port  | 22               | Port the service listens on          |
| Protocol       | TCP              | Usually TCP for SSH, HTTP, etc.      |

### SSH Through a Port Forward

```bash
# If external port 2222 forwards to internal port 22:
ssh -p 2222 user@public_ip_of_router
```

---

## Common Ports and Firewall Considerations

| Port  | Service   | Typically Blocked? | Notes                                  |
|-------|-----------|-------------------|----------------------------------------|
| 22    | SSH       | Often             | Block from public, allow from known IPs|
| 25    | SMTP      | Often             | ISPs frequently block outbound 25      |
| 53    | DNS       | Rarely            | Needed for name resolution             |
| 80    | HTTP      | Rarely            | Standard web traffic                   |
| 443   | HTTPS     | Rarely            | Encrypted web traffic                  |
| 3306  | MySQL     | Should be         | Never expose directly to internet      |
| 5432  | PostgreSQL| Should be         | Never expose directly to internet      |
| 6379  | Redis     | Should be         | Never expose directly to internet      |
| 8080  | Alt HTTP  | Sometimes         | Common for dev servers                 |
| 27017 | MongoDB   | Should be         | Never expose directly to internet      |

---

## Troubleshooting Connection Issues

### Is the port open?

```bash
# Test if a remote port is reachable
nc -zv hostname 22

# Scan a range of ports
nc -zv hostname 20-25
```

### Is something listening on the port?

```bash
# Check what's listening on a specific port
sudo lsof -i :22

# Check all listening ports
sudo lsof -i -P -n | grep LISTEN

# Alternative
netstat -an | grep LISTEN
```

### Is the firewall blocking it?

```bash
# Check macOS application firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# Check pf rules
sudo pfctl -s rules

# Check pf state table for active connections
sudo pfctl -s state | grep "port 22"
```

### Common Causes of Connection Failure

```
1. Service not running          --> Check: sudo lsof -i :PORT
2. Host firewall blocking       --> Check: sudo pfctl -s rules
3. Network firewall blocking    --> Check: Security Group / router rules
4. No port-forward through NAT  --> Check: Router port-forwarding config
5. Wrong port                   --> Check: ssh -p CORRECT_PORT user@host
6. Wrong IP                     --> Check: curl ifconfig.me (for public IP)
```

---

## Quick Reference: Firewall vs. NAT

| Feature          | Firewall                        | NAT                              |
|------------------|---------------------------------|----------------------------------|
| Purpose          | Allow/deny traffic              | Translate addresses              |
| Operates on      | Rules matching packets          | Address translation table        |
| Direction        | Inbound and/or outbound         | Typically at network boundary    |
| Blocks traffic?  | Yes, that's its job             | Not directly, but hides internal IPs |
| Cloud equivalent | Security Groups, NACLs          | NAT Gateway, Load Balancer       |
