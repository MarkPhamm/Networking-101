# Module 03 Cheatsheet: IP Addressing and DNS

## Private IP Address Ranges

| CIDR | Range | Addresses | Typical Use |
|------|-------|----------:|-------------|
| 10.0.0.0/8 | 10.0.0.0 -- 10.255.255.255 | ~16.7M | Cloud VPCs, large orgs |
| 172.16.0.0/12 | 172.16.0.0 -- 172.31.255.255 | ~1M | Medium networks |
| 192.168.0.0/16 | 192.168.0.0 -- 192.168.255.255 | ~65K | Home/small office |
| 127.0.0.0/8 | 127.0.0.0 -- 127.255.255.255 | ~16.7M | Loopback (localhost) |

## Special Addresses

| Address | Meaning |
|---------|---------|
| 127.0.0.1 | Localhost (loopback -- this machine) |
| 0.0.0.0 | "All interfaces" (when binding a service) |
| 255.255.255.255 | Broadcast (send to all devices on LAN) |
| 169.254.x.x | Link-local (DHCP failed, self-assigned) |

## DNS Record Types

| Record | Purpose | Example Query |
|--------|---------|---------------|
| A | Name to IPv4 address | `dig example.com A` |
| AAAA | Name to IPv6 address | `dig example.com AAAA` |
| CNAME | Alias to another name | `dig www.example.com CNAME` |
| MX | Mail server (with priority) | `dig example.com MX` |
| NS | Authoritative nameserver | `dig example.com NS` |
| TXT | Arbitrary text (SPF, verification) | `dig example.com TXT` |
| SOA | Start of authority (zone info) | `dig example.com SOA` |
| PTR | Reverse lookup (IP to name) | `dig -x 8.8.8.8` |

## DNS Commands

### dig (most detailed)

```bash
dig example.com                # Full A record lookup
dig +short example.com         # Just the IP
dig example.com MX             # Specific record type
dig @8.8.8.8 example.com      # Query a specific DNS server
dig +trace example.com         # Show full resolution chain
dig -x 8.8.8.8                # Reverse lookup (IP -> name)
```

### nslookup

```bash
nslookup example.com              # Basic lookup
nslookup example.com 8.8.8.8      # Use specific DNS server
nslookup -type=MX example.com     # Specific record type
```

### host (simplest output)

```bash
host example.com                # Basic lookup
host -t MX example.com         # Specific record type
host 8.8.8.8                   # Reverse lookup
```

## /etc/hosts File

Format: `IP_ADDRESS    HOSTNAME [ALIASES...]`

```
# Default entries
127.0.0.1       localhost
255.255.255.255 broadcasthost
::1             localhost

# Custom entries (add your own)
127.0.0.1       myapp.local
192.168.1.50    devserver db-host
```

Edit with: `sudo nano /etc/hosts`

Flush DNS cache (macOS): `sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder`

## Finding Your IPs

```bash
# Private IP
ifconfig en0 | grep "inet "

# Public IP
curl -s ifconfig.me

# All interfaces
ifconfig | grep "inet "
```

## DNS Resolution Order (simplified)

```
Application
    -> Local DNS cache
    -> /etc/hosts
    -> DNS resolver (from /etc/resolv.conf or system config)
    -> Root servers (.)
    -> TLD servers (.com, .org, etc.)
    -> Authoritative nameserver
    -> Answer returned and cached (for TTL seconds)
```

## Key Concepts

| Concept | One-liner |
|---------|-----------|
| IPv4 | 32-bit address, ~4.3B total, written as dotted decimal |
| IPv6 | 128-bit address, hex notation with colons |
| Private IP | Internal-only, not routable on the internet |
| Public IP | Globally unique, assigned by ISP |
| NAT | Router translates private IPs to one public IP |
| DNS | Translates domain names to IP addresses |
| TTL | Seconds a DNS record should be cached |
| Resolver | Server that does DNS lookups on your behalf |
| Authoritative NS | The final source of truth for a domain's records |
| CNAME | Alias pointing to another domain name |

## Quick Debugging

| Symptom | Likely Cause | Check With |
|---------|-------------|------------|
| "Could not resolve hostname" | DNS failure | `dig hostname` |
| Resolves to wrong IP | Stale cache or /etc/hosts override | `cat /etc/hosts`, flush cache |
| Slow DNS | Slow resolver | `dig hostname \| grep "Query time"` |
| Works with IP, not hostname | DNS issue (not a connectivity issue) | `dig hostname`, `ping IP` |
