# Module 07: Cheatsheet -- LAN, WAN, and Network Segments

---

## LAN vs. WAN

| Feature           | LAN                               | WAN                                  |
|-------------------|-----------------------------------|--------------------------------------|
| Scope             | Home, office, building            | City, country, world (internet)      |
| Speed             | 1-10 Gbps                        | 10 Mbps - 1 Gbps (typical consumer) |
| Latency           | < 1 ms                           | 10-200+ ms                           |
| Addressing        | Private IPs (RFC 1918)            | Public IPs                           |
| Broadcast         | Yes (ARP, mDNS)                  | No (routers block broadcasts)        |
| Hardware          | Switches, Wi-Fi APs              | Routers, modems, ISP infrastructure  |
| Control           | You manage it                    | ISP / carrier manages it             |
| Layer 2 protocol  | Ethernet (wired), Wi-Fi (802.11) | Various (MPLS, fiber, etc.)          |

---

## MAC Address Format

```
AA:BB:CC:DD:EE:FF
|--OUI--| |--NIC--|
```

- **48 bits** (6 bytes), written as hex pairs separated by colons
- **OUI** (first 3 bytes): Organizationally Unique Identifier -- identifies the manufacturer
- **NIC** (last 3 bytes): unique identifier assigned by the manufacturer
- Also written with dashes: `AA-BB-CC-DD-EE-FF`
- Broadcast MAC: `FF:FF:FF:FF:FF:FF` (all devices on the LAN)

---

## ARP Commands

```bash
# View ARP cache (all known IP-to-MAC mappings)
arp -a

# Clear entire ARP cache
sudo arp -d -a

# Delete a specific ARP entry
sudo arp -d 192.168.1.1

# Add a static ARP entry (rarely needed)
sudo arp -s 192.168.1.100 AA:BB:CC:DD:EE:FF
```

### ARP Flow Summary

```
Device A wants to send to 192.168.1.1:

1. Check ARP cache for 192.168.1.1
2. Not found --> send ARP Request (broadcast to FF:FF:FF:FF:FF:FF):
   "Who has 192.168.1.1? Tell 192.168.1.100"
3. Router replies (unicast):
   "192.168.1.1 is at AA:BB:CC:DD:EE:FF"
4. Cache the mapping
5. Send IP packet in Ethernet frame to AA:BB:CC:DD:EE:FF
```

---

## Network Interface Commands (macOS)

```bash
# List all hardware ports, interfaces, and MAC addresses
networksetup -listallhardwareports

# Show IP, mask, and MAC for a specific interface
ifconfig en0

# Show just the IP address
ifconfig en0 | grep "inet "

# Show just the MAC address
ifconfig en0 | grep ether

# List all interfaces
ifconfig -a

# Show active Wi-Fi info (SSID, channel, signal strength)
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I
```

---

## Home Network Topology

```
Internet (WAN)
    |
[Modem] -- Converts ISP signal to Ethernet
    |
[Router] -- NAT, DHCP, firewall, default gateway
    |
[Switch / Wi-Fi AP] -- Often built into the router
    |       |       |       |
 Laptop   Phone  Desktop  Smart TV
```

### Component Roles

| Device          | Function                                              | Layer    |
|-----------------|-------------------------------------------------------|----------|
| Modem           | Signal conversion (fiber/cable/DSL to Ethernet)       | Layer 1  |
| Router          | Connects LAN to WAN, NAT, DHCP, firewall              | Layer 3  |
| Switch          | Connects LAN devices, forwards frames by MAC          | Layer 2  |
| Wi-Fi AP        | Wireless connectivity to the LAN                      | Layer 1-2|
| Firewall        | Filters traffic by rules (may be in router)           | Layer 3-4|

---

## Network Segmentation Terms

| Term               | Definition                                                      |
|--------------------|-----------------------------------------------------------------|
| Broadcast domain   | Set of devices that receive each other's Layer 2 broadcasts     |
| Collision domain   | Set of devices sharing a network segment (mostly historical)    |
| VLAN               | Virtual LAN -- logical segmentation on a physical switch        |
| VLAN ID            | Number (1-4094) identifying a VLAN                              |
| Trunk port         | Switch port that carries traffic for multiple VLANs (tagged)    |
| Access port        | Switch port assigned to a single VLAN (untagged)                |
| 802.1Q             | Standard for VLAN tagging in Ethernet frames                    |
| Inter-VLAN routing | Routing traffic between VLANs via a Layer 3 device              |

---

## VPN Types

| Type            | Connects                         | Example                              |
|-----------------|----------------------------------|--------------------------------------|
| Remote Access   | Single device to a network       | Employee VPN to corporate network    |
| Site-to-Site    | Two networks to each other       | Branch office to HQ                  |
| Cloud VPN       | On-prem network to cloud VPC     | AWS Site-to-Site VPN                 |

### Common VPN Protocols

| Protocol     | Notes                                              |
|--------------|----------------------------------------------------|
| WireGuard    | Modern, fast, simple configuration                 |
| OpenVPN      | Widely supported, open source, SSL/TLS-based       |
| IPsec/IKEv2  | Enterprise standard, site-to-site and remote access|
| SSH tunnel   | Not a full VPN, but can forward specific ports     |

---

## SSH Jump Host Syntax

### Command Line

```bash
# Single jump
ssh -J jump_user@jump_host target_user@target_host

# Multiple jumps (comma-separated)
ssh -J user1@hop1,user2@hop2 target_user@final_host

# Jump with non-standard port
ssh -J user@jump_host:2222 target_user@target_host
```

### SSH Config (~/.ssh/config)

```
Host bastion
    HostName bastion.company.com
    User admin
    IdentityFile ~/.ssh/bastion_key

Host internal-server
    HostName 10.0.1.50
    User ubuntu
    IdentityFile ~/.ssh/key
    ProxyJump bastion
```

Then just:

```bash
ssh internal-server
```

### Port Forwarding Through a Jump Host

```bash
# Forward local port to a remote service through a bastion
ssh -J admin@bastion -L LOCAL_PORT:REMOTE_HOST:REMOTE_PORT user@target -N

# Example: forward PostgreSQL through a bastion
ssh -J admin@bastion.company.com -L 5432:db.internal:5432 ubuntu@10.0.1.50 -N

# Then connect locally:
psql -h localhost -p 5432 -U myuser mydb
```

---

## Quick Diagnostics

```bash
# Find your private IP
ifconfig en0 | grep "inet "

# Find your public IP
curl -s ifconfig.me

# Find your default gateway
route -n get default | grep gateway

# See devices on your LAN
arp -a

# See your interfaces and MACs
networksetup -listallhardwareports

# Trace the path to a destination
traceroute -n 8.8.8.8

# Check connectivity to a host
ping -c 4 192.168.1.1
```
