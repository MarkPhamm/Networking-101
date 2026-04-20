# Module 05: Cheatsheet -- Subnets and Routing

---

## CIDR Reference Table

| CIDR | Subnet Mask         | Total Addresses | Usable Hosts   | Notes                           |
|------|---------------------|-----------------|----------------|---------------------------------|
| /8   | 255.0.0.0           | 16,777,216      | 16,777,214     | Class A (e.g., 10.0.0.0/8)     |
| /9   | 255.128.0.0         | 8,388,608       | 8,388,606      |                                 |
| /10  | 255.192.0.0         | 4,194,304       | 4,194,302      |                                 |
| /11  | 255.224.0.0         | 2,097,152       | 2,097,150      |                                 |
| /12  | 255.240.0.0         | 1,048,576       | 1,048,574      | 172.16.0.0/12 private range     |
| /13  | 255.248.0.0         | 524,288         | 524,286        |                                 |
| /14  | 255.252.0.0         | 262,144         | 262,142        |                                 |
| /15  | 255.254.0.0         | 131,072         | 131,070        |                                 |
| /16  | 255.255.0.0         | 65,536          | 65,534         | Class B (e.g., 172.16.0.0/16)  |
| /17  | 255.255.128.0       | 32,768          | 32,766         |                                 |
| /18  | 255.255.192.0       | 16,384          | 16,382         |                                 |
| /19  | 255.255.224.0       | 8,192           | 8,190          |                                 |
| /20  | 255.255.240.0       | 4,096           | 4,094          |                                 |
| /21  | 255.255.248.0       | 2,048           | 2,046          |                                 |
| /22  | 255.255.252.0       | 1,024           | 1,022          |                                 |
| /23  | 255.255.254.0       | 512             | 510            |                                 |
| /24  | 255.255.255.0       | 256             | 254            | Most common LAN subnet          |
| /25  | 255.255.255.128     | 128             | 126            |                                 |
| /26  | 255.255.255.192     | 64              | 62             |                                 |
| /27  | 255.255.255.224     | 32              | 30             |                                 |
| /28  | 255.255.255.240     | 16              | 14             |                                 |
| /29  | 255.255.255.248     | 8               | 6              |                                 |
| /30  | 255.255.255.252     | 4               | 2              | Point-to-point links            |
| /31  | 255.255.255.254     | 2               | 2*             | Point-to-point (RFC 3021)       |
| /32  | 255.255.255.255     | 1               | 1              | Single host route               |

*`/31` is a special case used for point-to-point links where no broadcast address is needed.

---

## Subnet Math Formulas

```
Total addresses    = 2^(32 - prefix_length)
Usable hosts       = 2^(32 - prefix_length) - 2
Network address    = IP AND subnet_mask  (all host bits = 0)
Broadcast address  = Network address OR (NOT subnet_mask)  (all host bits = 1)
```

### Quick Way to Find Network and Broadcast

1. Convert the prefix to a mask.
2. AND the IP with the mask to get the network address.
3. Flip the mask bits (NOT) and OR with the network address to get the broadcast.

---

## Private IP Ranges (RFC 1918)

| Range                   | CIDR          | Typical Use         |
|-------------------------|---------------|---------------------|
| 10.0.0.0 -- 10.255.255.255    | 10.0.0.0/8    | Large enterprises, cloud VPCs |
| 172.16.0.0 -- 172.31.255.255  | 172.16.0.0/12 | Medium networks     |
| 192.168.0.0 -- 192.168.255.255| 192.168.0.0/16| Home and small office |

---

## Routing Table Columns

| Column      | Meaning                                                        |
|-------------|----------------------------------------------------------------|
| Destination | Target network or host (e.g., `10.0.0.0/8` or `default`)     |
| Gateway     | Next-hop IP address (or `link#N` / `*` for directly connected)|
| Flags       | Route attributes (see below)                                   |
| Netif       | Outgoing network interface (e.g., `en0`, `lo0`)               |
| Expire      | Time until route expires (for dynamic routes)                  |

### Common Route Flags

| Flag | Meaning                                    |
|------|--------------------------------------------|
| U    | Route is **up** (active)                   |
| G    | Route uses a **gateway** (not direct)      |
| H    | Route is to a **host** (not a network)     |
| S    | Route is **static** (manually configured)  |
| C    | Route generates new routes on use (cloning)|
| L    | Route involves **link-layer** (L2) address |

---

## Key Commands

### View Routing Table

```bash
# Full routing table
netstat -rn

# Default gateway only
route -n get default

# IPv4 routes only
netstat -rn -f inet
```

### View Your IP and Subnet

```bash
# Show IP and mask for Wi-Fi interface
ifconfig en0 | grep "inet "

# List all interfaces
ifconfig -a

# macOS: list hardware ports and interfaces
networksetup -listallhardwareports
```

### Trace the Route to a Destination

```bash
# Show each hop to a destination (IPs only, no DNS lookups)
traceroute -n google.com

# Limit to N hops
traceroute -n -m 15 google.com
```

### Test Connectivity

```bash
# Ping a host
ping -c 4 192.168.1.1

# Ping with specific packet size
ping -c 4 -s 1400 192.168.1.1
```

---

## Same Subnet Decision Flowchart

```
1. Take your IP and the destination IP
2. AND both with your subnet mask
3. Compare results:
   |
   +--> Results MATCH?
   |      YES --> Same subnet --> Send directly (ARP for MAC, then send)
   |      NO  --> Different subnet --> Send to default gateway
```

---

## Quick Binary-to-Decimal for Subnet Octets

When the subnet boundary falls within an octet:

| Binary      | Decimal |
|-------------|---------|
| 10000000    | 128     |
| 11000000    | 192     |
| 11100000    | 224     |
| 11110000    | 240     |
| 11111000    | 248     |
| 11111100    | 252     |
| 11111110    | 254     |
| 11111111    | 255     |

These are the only valid values for a subnet mask octet (plus `00000000` = 0).
