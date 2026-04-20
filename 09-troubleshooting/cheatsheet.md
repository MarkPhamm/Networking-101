# Module 09: Cheatsheet -- Troubleshooting

---

## Debug Flowchart

```
"I can't SSH in" -- what do I check?

[1] DNS Resolution
    |
    +-- dig hostname / nslookup hostname
    |   socket.getaddrinfo('hostname', 22)
    |
    +-- FAIL? --> Bad hostname, DNS down, wrong /etc/resolv.conf
    |
    v
[2] IP Reachability
    |
    +-- ping -c 4 <IP>
    |   traceroute -n <IP>
    |
    +-- FAIL? --> Host down, routing issue, intermediate firewall
    |   (Note: ping may be blocked -- proceed to step 3 anyway)
    |
    v
[3] TCP Port Check
    |
    +-- nc -zv <IP> 22
    |   telnet <IP> 22
    |   python3: socket.connect_ex((<IP>, 22))
    |
    +-- "Connection refused"?  --> Service not running (sshd down)
    +-- "Connection timed out"? --> Firewall dropping packets
    |
    v
[4] Firewall Check
    |
    +-- Can you reach OTHER servers on port 22? (outbound ok?)
    +-- On server: sudo iptables -L -n / sudo pfctl -sr
    +-- Cloud: Check Security Groups, NACLs, Route Tables
    |
    +-- FAIL? --> Open the port in the firewall / security group
    |
    v
[5] NAT / Port Forwarding
    |
    +-- Is the server behind NAT?
    +-- Is port forwarding configured on the router/LB?
    |
    v
[6] Authentication
    |
    +-- ssh -v user@host  (verbose mode)
    +-- Check: correct key? correct user? permissions on ~/.ssh?
    |
    +-- "Permission denied"? --> Key/user issue
    +-- "Host key changed"?  --> Server rebuilt or MITM
    |
    v
[7] SSH Service
    |
    +-- systemctl status sshd
    +-- sudo lsof -i :22
    +-- Check /etc/ssh/sshd_config
    +-- Check sshd logs (journalctl -u sshd)
    |
    +-- FAIL? --> Start sshd, fix config, check disk space
```

---

## Common Error Messages

| Error Message | What It Means | Layer | What to Do |
|---|---|---|---|
| `Could not resolve hostname` | DNS lookup failed | DNS | Check hostname spelling, DNS server, `/etc/resolv.conf` |
| `Network is unreachable` | No route to destination | Routing | Check routing table, default gateway, VPN |
| `No route to host` | Network exists, host unreachable | Routing | Verify host IP, check for ICMP unreachable from firewall |
| `Connection timed out` | Packets silently dropped | Firewall | Check security groups, NACLs, host firewall (both sides) |
| `Connection refused` | Port closed, nothing listening | Service | Verify sshd/service is running: `systemctl status sshd` |
| `Permission denied (publickey)` | Key rejected | Auth | Check key file, `authorized_keys`, file permissions |
| `Host key verification failed` | Server fingerprint changed | Auth | Server rebuilt? Update `~/.ssh/known_hosts`. Unexpected? Investigate. |
| `Connection reset by peer` | Server dropped connection | Service | Check sshd logs, fail2ban, server-side config |
| `Too many auth failures` | Agent tried too many keys | Auth | Use `ssh -i /path/to/key -o IdentitiesOnly=yes` |
| `Broken pipe` | Connection dropped mid-session | Network | Check stability. Add `ServerAliveInterval 60` to ssh config |

---

## Key Diagnostic Commands

### DNS Resolution

```bash
# Standard DNS lookup
dig hostname

# Reverse lookup (IP -> hostname)
dig -x 10.0.0.5

# Query a specific DNS server
dig @8.8.8.8 hostname

# Simple lookup
nslookup hostname

# Python equivalent
python3 -c "import socket; print(socket.getaddrinfo('hostname', 22))"
```

### Reachability

```bash
# Ping with count
ping -c 4 10.0.0.5

# Trace route to destination (numeric, no DNS)
traceroute -n 10.0.0.5

# Trace with limited hops
traceroute -n -m 10 10.0.0.5
```

### Port Testing

```bash
# Test TCP port (quick, clean output)
nc -zv 10.0.0.5 22

# Test with timeout
nc -zv -w 5 10.0.0.5 22

# Scan a range of ports
nc -zv 10.0.0.5 20-25

# Python equivalent
python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5)
r = s.connect_ex(('10.0.0.5', 22))
print('open' if r == 0 else f'closed ({r})')
s.close()
"
```

### SSH Debugging

```bash
# Verbose SSH (shows handshake + auth steps)
ssh -v user@host

# Extra verbose
ssh -vvv user@host

# Force a specific key
ssh -i ~/.ssh/my_key user@host

# Skip agent, use only the specified key
ssh -o IdentitiesOnly=yes -i ~/.ssh/my_key user@host
```

### Local Service Checks (on the server)

```bash
# What is listening on port 22?
sudo lsof -i :22

# All listening TCP ports
sudo lsof -iTCP -sTCP:LISTEN

# Listening ports (Linux)
sudo ss -tlnp

# Listening ports (macOS / older Linux)
sudo netstat -tlnp

# sshd status (Linux systemd)
systemctl status sshd

# sshd config test
sudo sshd -T

# Recent sshd logs (Linux systemd)
sudo journalctl -u sshd -n 50 --no-pager

# Recent sshd logs (macOS)
sudo log show --predicate 'process == "sshd"' --last 10m
```

### Firewall Checks

```bash
# Linux (iptables)
sudo iptables -L -n -v

# Linux (nftables)
sudo nft list ruleset

# macOS (pf)
sudo pfctl -sr

# Check if firewall is enabled (macOS)
sudo pfctl -s info
```

---

## Cloud-Specific Checks (AWS)

When troubleshooting connectivity in AWS, check these in order:

| Component | What to Check | AWS CLI Command |
|---|---|---|
| Security Group | Inbound rules allow your IP on port 22 | `aws ec2 describe-security-groups --group-ids sg-xxx` |
| Network ACL | Inbound AND outbound rules (stateless!) | `aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=subnet-xxx` |
| Route Table | Route to your network exists | `aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-xxx` |
| Internet Gateway | Attached to VPC (for public subnets) | `aws ec2 describe-internet-gateways --filters Name=attachment.vpc-id,Values=vpc-xxx` |
| Public IP / EIP | Instance has a public IP | `aws ec2 describe-instances --instance-ids i-xxx --query 'Reservations[].Instances[].PublicIpAddress'` |
| Instance state | Instance is running | `aws ec2 describe-instance-status --instance-ids i-xxx` |

### Common AWS Gotchas

- **Security Groups are stateful** -- if you allow inbound, the response is automatically allowed outbound.
- **NACLs are stateless** -- you need explicit inbound AND outbound rules (including ephemeral port ranges for return traffic).
- **New subnets** use the VPC's default NACL, which allows all traffic. Custom NACLs start with deny-all.
- **Private subnets** require a NAT Gateway (or bastion host) for outbound internet access.
- **VPC Flow Logs** are your best friend for debugging -- they show accepted and rejected packets at the ENI level.

---

## Quick Decision Tree

```
Can you resolve the name? ----NO----> Fix DNS
         |
        YES
         |
Can you ping the IP? ---------NO----> Maybe firewall (continue anyway)
         |
     YES or MAYBE
         |
Can you reach the port? ------NO----> Is it "refused" or "timed out"?
         |                                |                    |
        YES                          "refused"           "timed out"
         |                                |                    |
Is SSH auth working? ------NO----> Service not running    Firewall blocking
         |                          Start sshd             Open the port
        YES
         |
You're in! Check if the issue is intermittent.
```
