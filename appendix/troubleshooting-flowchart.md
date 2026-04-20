# Troubleshooting Flowchart: "I Can't SSH Into a Server"

A systematic decision tree for diagnosing SSH connection failures. Work through each step in order -- each step tests a different layer of the network stack. Stop when you find the problem.

---

## The Flowchart

```
START: ssh user@host fails
  │
  ▼
┌─────────────────────────────────────────────────────┐
│ STEP 1: Can you resolve the hostname?               │
│                                                     │
│   dig hostname                                      │
│   nslookup hostname                                 │
│                                                     │
│   Look for an IP address in the ANSWER section.     │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─── YES ─┴─ NO ───┐
          │                   │
          ▼                   ▼
     (continue)         ┌──────────────────────────────┐
                        │ DNS PROBLEM (Module 03)      │
                        │                              │
                        │ - Is the hostname spelled    │
                        │   correctly?                 │
                        │ - Try: dig hostname @8.8.8.8 │
                        │   (use a known DNS server)   │
                        │ - Check /etc/resolv.conf     │
                        │ - Try the IP address directly│
                        │   instead of the hostname    │
                        │ - Are you connected to the   │
                        │   internet? ping 8.8.8.8     │
                        └──────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│ STEP 2: Can you ping the IP?                        │
│                                                     │
│   ping -c 3 <IP address>                            │
│                                                     │
│   Look for replies with round-trip times.           │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─── YES ─┴─ NO ───┐
          │                   │
          ▼                   ▼
     (continue)         ┌──────────────────────────────┐
                        │ ROUTING OR HOST DOWN         │
                        │ (Modules 03, 05)             │
                        │                              │
                        │ - Is the IP correct?         │
                        │ - Is the host powered on?    │
                        │ - traceroute <IP> to see     │
                        │   where packets stop         │
                        │ - Are you on the right       │
                        │   network? (Private IPs like │
                        │   10.x or 192.168.x are not  │
                        │   reachable from outside     │
                        │   their LAN)                 │
                        │ - Check your routing table:  │
                        │   netstat -rn                │
                        │ - NOTE: Some hosts block     │
                        │   ICMP (ping). If ping fails │
                        │   but you suspect the host   │
                        │   is up, skip to Step 3.     │
                        └──────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│ STEP 3: Can you reach port 22?                      │
│                                                     │
│   nc -zv <IP> 22                                    │
│   (or: nmap -p 22 <IP>)                             │
│                                                     │
│   "Connection succeeded" = port is open.            │
│   "Connection refused" = host is up but port closed.│
│   Timeout = something is blocking it.               │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─── OPEN ┴─ REFUSED/TIMEOUT ──┐
          │                               │
          ▼                               ▼
     (continue)         ┌──────────────────────────────────────┐
                        │ FIREWALL OR SSHD NOT RUNNING         │
                        │ (Modules 04, 06)                     │
                        │                                      │
                        │ If "Connection refused":             │
                        │ - sshd is not running, OR            │
                        │ - SSH is on a non-standard port      │
                        │ - Check: ssh -p 2222 user@host       │
                        │ - On the server:                     │
                        │   systemctl status sshd (Linux)      │
                        │   sudo launchctl list | grep ssh     │
                        │   (macOS)                            │
                        │                                      │
                        │ If timeout:                          │
                        │ - A firewall is DROPping packets     │
                        │ - Go to Step 4                       │
                        └──────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────┐
│ STEP 4: Is a firewall blocking?                     │
│ (Module 06)                                         │
│                                                     │
│ Check BOTH sides -- your firewall and theirs.       │
│                                                     │
│ Your side (macOS):                                  │
│   sudo pfctl -s rules                               │
│                                                     │
│ Their side (Linux):                                 │
│   sudo iptables -L -n          (if you have access) │
│   sudo ufw status                                   │
│                                                     │
│ Cloud (AWS/GCP/Azure):                              │
│   Check Security Groups / Network ACLs / firewall   │
│   rules in the cloud console.                       │
│   - Is port 22 allowed inbound?                     │
│   - Is your source IP in the allowed range?         │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─ CLEAR ─┴─ BLOCKED ──┐
          │                       │
          ▼                       ▼
     (continue)            Fix the firewall rule.
                           Allow inbound TCP port 22
                           from your IP or CIDR range.
          │
          ▼
┌─────────────────────────────────────────────────────┐
│ STEP 5: Is NAT / port forwarding set up?            │
│ (Module 06)                                         │
│                                                     │
│ Is the server behind a home router or NAT gateway?  │
│                                                     │
│ - If connecting to a public IP that NATs to a       │
│   private server, port forwarding must be           │
│   configured on the router/gateway.                 │
│ - Check the router's admin panel for port 22        │
│   forwarding to the correct internal IP.            │
│ - In AWS: check that the instance has a public IP   │
│   or Elastic IP, and that the route table sends     │
│   internet traffic through an Internet Gateway.     │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─── OK ──┴─ MISSING ──┐
          │                       │
          ▼                       ▼
     (continue)            Configure port forwarding
                           or assign a public IP.
          │
          ▼
┌─────────────────────────────────────────────────────┐
│ STEP 6: Are your credentials correct?               │
│ (Modules 01, 02)                                    │
│                                                     │
│ If you see "Permission denied (publickey,password)" │
│                                                     │
│ Password auth:                                      │
│ - Is the username correct? (remote user, not local) │
│ - Is the password correct?                          │
│ - Does the server allow password auth?              │
│   Check: PasswordAuthentication in sshd_config      │
│                                                     │
│ Key auth:                                           │
│ - Is your public key in ~/.ssh/authorized_keys on   │
│   the server?                                       │
│ - Is the private key loaded? ssh-add -l             │
│ - Are permissions correct?                          │
│   chmod 700 ~/.ssh                                  │
│   chmod 600 ~/.ssh/id_ed25519                       │
│   chmod 600 ~/.ssh/authorized_keys (server side)    │
│ - Try explicitly: ssh -i ~/.ssh/mykey user@host     │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─── OK ──┴─ WRONG ───┐
          │                      │
          ▼                      ▼
     (continue)           Fix credentials.
                          Re-copy public key:
                          ssh-copy-id user@host
          │
          ▼
┌─────────────────────────────────────────────────────┐
│ STEP 7: Is sshd running and configured correctly?   │
│ (Module 04)                                         │
│                                                     │
│ If you can reach the server but SSH still fails:    │
│                                                     │
│ On the server, check sshd_config:                   │
│   cat /etc/ssh/sshd_config                          │
│                                                     │
│ Common issues:                                      │
│ - Port: is sshd listening on the port you expect?   │
│ - PermitRootLogin: is it set to "no" and you're     │
│   trying to log in as root?                         │
│ - AllowUsers / AllowGroups: is your user listed?    │
│ - AuthenticationMethods: are the right methods      │
│   enabled?                                          │
│                                                     │
│ After changing sshd_config, restart sshd:           │
│   sudo systemctl restart sshd (Linux)               │
└───────────────────┬─────────────────────────────────┘
                    │
          ┌─── OK ──┴─ MISCONFIGURED ──┐
          │                             │
          ▼                             ▼
     (continue)                  Fix sshd_config
                                 and restart sshd.
          │
          ▼
┌─────────────────────────────────────────────────────┐
│ STEP 8: Get verbose output                          │
│                                                     │
│   ssh -v user@host                                  │
│   ssh -vv user@host       (more detail)             │
│   ssh -vvv user@host      (maximum detail)          │
│                                                     │
│ The verbose output shows exactly which step fails:  │
│                                                     │
│ - "Connecting to..." -- TCP connection phase        │
│ - "SSH2_MSG_KEXINIT" -- Key exchange started        │
│ - "Host 'x' is known" -- Host key check             │
│ - "Authentications that can continue" -- Auth phase  │
│ - "Authentication succeeded" -- You're in            │
│                                                     │
│ Find the LAST successful line and the FIRST error.  │
│ That tells you exactly which layer broke.           │
└─────────────────────────────────────────────────────┘
```

---

## Quick Reference: Error to Step Mapping

| Error Message | Go To Step |
|---|---|
| `Could not resolve hostname` | Step 1 (DNS) |
| `Network is unreachable` | Step 2 (Routing) |
| `No route to host` | Step 2 (Routing) |
| `Operation timed out` | Step 2 or 4 (Routing or Firewall) |
| `Connection refused` | Step 3 (sshd/Port) |
| `Connection reset by peer` | Step 4 or 7 (Firewall or sshd config) |
| `Permission denied (publickey)` | Step 6 (Key auth) |
| `Permission denied (publickey,password)` | Step 6 (Credentials) |
| `Host key verification failed` | Not in this flowchart -- run `ssh-keygen -R host` |

---

## The Mental Model

Each step tests a different layer of the TCP/IP stack, from bottom to top:

```
Step 1: DNS          → Application layer (name resolution)
Step 2: Ping         → Internet layer (IP reachability)
Step 3: Port check   → Transport layer (TCP port open?)
Step 4: Firewall     → Internet/Transport layers (traffic filtering)
Step 5: NAT          → Internet layer (address translation)
Step 6: Credentials  → Application layer (SSH authentication)
Step 7: sshd config  → Application layer (SSH server settings)
Step 8: Verbose SSH  → All layers (detailed diagnosis)
```

When in doubt, start from the bottom (can I even reach the machine?) and work your way up (is the right service running? are my credentials correct?). Don't debug authentication if you can't even ping the IP.

---

[Back to main guide](../README.md)
