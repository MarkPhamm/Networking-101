# Module 07: LAN, WAN, and Network Segments

## Overview

Networks come in different sizes and scopes. A LAN (Local Area Network) is the network in your home or office -- all the devices connected to the same router. A WAN (Wide Area Network) spans cities, countries, or the entire globe. Understanding the boundary between them, and how devices communicate within a LAN versus across a WAN, is essential for troubleshooting and architecture.

If your LAN is a private data warehouse that only internal users can query, then the WAN is the cross-region replication link that connects data centers around the world. Segmenting a LAN with VLANs is like isolating schemas in a multi-tenant database -- same physical hardware, logically separated.

---

## LAN (Local Area Network)

A LAN is a network that covers a small geographic area -- a home, an office floor, a building. Key characteristics:

- **High speed, low latency** -- typically Gigabit Ethernet (1 Gbps) or Wi-Fi 6
- **Shared broadcast domain** -- devices can discover each other via broadcast (ARP, mDNS)
- **Usually one or a few subnets** -- e.g., `192.168.1.0/24`
- **Connected by switches and Wi-Fi access points** -- not routers (within the LAN)
- **Privately addressed** -- uses RFC 1918 private IP ranges

Your home network is a LAN. Your office network is a LAN (possibly a larger, more segmented one).

---

## WAN (Wide Area Network)

A WAN connects LANs across large distances. The most well-known WAN is the internet itself.

- **Lower speed, higher latency** compared to LAN (your ISP link is typically slower than your local Ethernet)
- **Routed traffic** -- packets traverse multiple routers to reach the destination
- **Uses public IP addresses** -- traffic on the WAN uses globally routable IPs
- **Managed by ISPs** -- your traffic crosses ISP backbones, internet exchange points, and undersea cables

### LAN vs. WAN at a Glance

| Feature        | LAN                             | WAN                                |
|----------------|----------------------------------|------------------------------------|
| Coverage       | Home, office, building          | City, country, world               |
| Speed          | 1-10 Gbps                      | 10 Mbps - 1 Gbps (typical home)   |
| Latency        | <1 ms                           | 10-200+ ms                         |
| Addressing     | Private IPs (192.168.x.x, etc.)| Public IPs                         |
| Hardware       | Switches, Wi-Fi APs             | Routers, modems, ISP infrastructure|
| Administration | You control it                  | ISP/carrier controls it            |

---

## Home Network Topology

Here is what a typical home network looks like, from the internet to your devices:

```
Internet (WAN)
    |
[ISP Infrastructure]
    |
[Modem] -- Converts ISP signal (fiber, cable, DSL) to Ethernet
    |
[Router] -- NAT, firewall, DHCP server, default gateway
    |
[Switch / Wi-Fi Access Point] -- Often built into the router
    |           |           |           |
 [Laptop]   [Phone]    [Desktop]   [Smart TV]
```

In many homes, the modem, router, switch, and Wi-Fi AP are all in a single device provided by the ISP. But conceptually, they are separate functions:

- **Modem** -- Translates the ISP's physical signal into Ethernet frames
- **Router** -- Connects your LAN to the WAN, performs NAT, runs DHCP
- **Switch** -- Connects multiple wired devices on the LAN
- **Wi-Fi Access Point** -- Connects wireless devices to the LAN

---

## MAC Addresses

A MAC (Media Access Control) address is a hardware address burned into every network interface card (NIC). It is a 48-bit value, written as six pairs of hexadecimal digits:

```
AA:BB:CC:DD:EE:FF
```

- The first three octets (`AA:BB:CC`) are the **OUI** (Organizationally Unique Identifier) -- they identify the manufacturer (e.g., Apple, Intel, Realtek)
- The last three octets (`DD:EE:FF`) are a unique identifier assigned by the manufacturer

### MAC vs. IP

| Feature     | MAC Address                    | IP Address                     |
|-------------|--------------------------------|--------------------------------|
| Layer       | Layer 2 (Data Link)           | Layer 3 (Network)              |
| Scope       | Local network only            | Global (can be routed)         |
| Assignment  | Burned into hardware (or set by OS) | Assigned by DHCP or manually |
| Format      | `AA:BB:CC:DD:EE:FF` (48-bit) | `192.168.1.1` (32-bit IPv4)   |
| Changes?    | Usually fixed                 | Changes with network/DHCP      |

MAC addresses are only relevant on the local network (Layer 2). When a packet crosses a router to a different subnet, the MAC addresses are rewritten at each hop, but the IP addresses stay the same end-to-end.

---

## ARP (Address Resolution Protocol)

ARP is how a device on a LAN finds the MAC address for a given IP address. When your laptop wants to send a packet to `192.168.1.1` (the router), it needs to know the router's MAC address so it can build the Ethernet frame.

### ARP Flow

```
1. Your laptop (192.168.1.100) wants to reach 192.168.1.1
2. Laptop checks its ARP cache -- is 192.168.1.1 already known?
3. If not, laptop sends an ARP REQUEST broadcast:
   "Who has 192.168.1.1? Tell 192.168.1.100"
   (sent to MAC address FF:FF:FF:FF:FF:FF -- all devices on the LAN)
4. The router (192.168.1.1) sees the broadcast and replies:
   "192.168.1.1 is at AA:BB:CC:DD:EE:FF"
   (sent directly to the laptop's MAC)
5. Laptop caches the mapping: 192.168.1.1 --> AA:BB:CC:DD:EE:FF
6. Laptop sends the IP packet inside an Ethernet frame addressed to AA:BB:CC:DD:EE:FF
```

ARP only works within a LAN (same broadcast domain). You never ARP for a device on a different subnet -- instead, you ARP for your default gateway's MAC and let the router forward the packet.

### Viewing and Managing the ARP Cache

```bash
# View ARP cache (all known IP-to-MAC mappings)
arp -a

# Clear the ARP cache (requires root)
sudo arp -d -a
```

---

## Network Segmentation

Network segmentation is the practice of dividing a network into isolated zones. Instead of one flat network where every device can talk to every other device, you create boundaries.

### Why Segment?

- **Security** -- If an attacker compromises a device in one segment, they cannot easily reach devices in another. Your IoT devices should not be on the same network as your production database servers.
- **Performance** -- Broadcast traffic is contained within a segment. Fewer broadcasts means less noise.
- **Compliance** -- Regulations (PCI-DSS, HIPAA) often require sensitive systems to be on isolated network segments.
- **Organization** -- Different teams, departments, or functions get their own network space.

### Example: Enterprise Network Segments

```
[Corporate LAN]     -- Employee laptops, printers (192.168.1.0/24)
[Server VLAN]       -- Application servers, databases (10.0.1.0/24)
[Management VLAN]   -- Network switches, routers admin interfaces (10.0.99.0/24)
[Guest Wi-Fi]       -- Visitor devices, isolated from everything (172.16.0.0/24)
[IoT VLAN]          -- Smart devices, cameras (172.16.1.0/24)
```

A router (or Layer 3 switch) with firewall rules controls what traffic can flow between segments.

---

## VLANs (Virtual LANs)

A VLAN is a logical division of a physical network. Without VLANs, all devices plugged into the same switch are in the same broadcast domain. VLANs let you create multiple isolated broadcast domains on the same physical switch.

### How VLANs Work

- Each VLAN is identified by a **VLAN ID** (a number from 1 to 4094)
- Switch ports are assigned to a VLAN -- devices on VLAN 10 cannot communicate directly with devices on VLAN 20
- Traffic between VLANs requires a router (inter-VLAN routing)
- VLAN tags are added to Ethernet frames (802.1Q standard)

```
Physical Switch
|-- Port 1: VLAN 10 (Engineering)
|-- Port 2: VLAN 10 (Engineering)
|-- Port 3: VLAN 20 (Finance)
|-- Port 4: VLAN 20 (Finance)
|-- Port 5: Trunk (carries all VLANs to router)
```

Ports 1-2 can talk to each other (same VLAN). Ports 3-4 can talk to each other. But Port 1 cannot reach Port 3 without going through a router -- even though they are on the same physical switch.

### DE Analogy

VLANs are like **schema isolation in a multi-tenant database**. Multiple tenants share the same physical database server, but each tenant's data is in a separate schema with access controls preventing cross-tenant queries. Same hardware, logically separated.

---

## VPNs (Virtual Private Networks)

A VPN creates an encrypted tunnel between your device and a remote network, making your device behave as if it were physically on that remote LAN -- even if you are in a coffee shop across the world.

### Types of VPN

| Type          | Use Case                                          | Example                        |
|---------------|---------------------------------------------------|--------------------------------|
| Remote Access | Connect one device to a corporate network         | Employee working from home     |
| Site-to-Site  | Connect two entire networks                       | Branch office to headquarters  |
| Cloud VPN     | Connect on-premises network to cloud VPC          | AWS Site-to-Site VPN           |

### How a VPN Works (Simplified)

```
[Your Laptop]  --encrypted tunnel-->  [VPN Server on Corporate LAN]
     |                                        |
  Coffee shop                         Corporate network
  Wi-Fi (untrusted)                   (10.0.0.0/16)

After connecting, your laptop gets an IP like 10.0.0.200
and can reach internal resources as if physically on the LAN.
```

### DE Analogy

A VPN is like **VPC Peering** in AWS or GCP. Two isolated networks establish a secure connection so resources in one can reach resources in the other. Without peering, the VPCs cannot communicate -- just like without a VPN, your laptop cannot reach the corporate LAN from home.

---

## Bastion Hosts / Jump Boxes

A bastion host (also called a jump box or jump server) is a hardened server that sits at the edge of a network and serves as the single entry point for SSH access to internal servers.

### Why Use a Bastion?

Instead of exposing every internal server to the internet (dangerous), you expose only the bastion. You SSH into the bastion first, then hop to the internal server.

```
Internet  -->  [Bastion Host]  -->  [Internal Server 1]
                                -->  [Internal Server 2]
                                -->  [Database Server]
```

Only the bastion's SSH port (22) is exposed to the internet. Internal servers only accept SSH from the bastion's IP.

### SSH Jump Host Syntax

```bash
# Direct jump (OpenSSH 7.3+)
ssh -J bastion_user@bastion_host target_user@internal_server

# Example
ssh -J admin@bastion.company.com ubuntu@10.0.1.50
```

This connects to the bastion first, then tunnels through to the internal server -- all in one command.

### SSH Config for Jump Hosts

You can configure this permanently in `~/.ssh/config`:

```
Host bastion
    HostName bastion.company.com
    User admin
    IdentityFile ~/.ssh/bastion_key

Host internal-db
    HostName 10.0.1.50
    User ubuntu
    IdentityFile ~/.ssh/internal_key
    ProxyJump bastion
```

Now you just type:

```bash
ssh internal-db
```

And SSH automatically routes through the bastion.

### DE Analogy

A bastion host is exactly a **jump server for accessing production databases**. In many data engineering environments, you cannot connect directly to the production PostgreSQL or Redshift instance from your laptop. Instead, you SSH into a bastion in the same VPC, and from there connect to the database. This is standard security practice in AWS, GCP, and Azure environments.

---

## Data Engineering Analogy Summary

| Networking Concept  | Data Engineering Equivalent                                            |
|---------------------|------------------------------------------------------------------------|
| LAN                 | **Private data warehouse** -- fast, local, internally accessible       |
| WAN                 | **Cross-region replication** -- connects distant systems, higher latency|
| VLANs               | **Schema isolation** in multi-tenant databases -- same hardware, logically separated |
| VPN                 | **VPC peering** -- secure connection between isolated networks         |
| Bastion host        | **Jump server** for production database access                         |
| MAC addresses       | **Hardware serial numbers** -- fixed identifiers for physical devices  |
| ARP                 | **Service discovery** (like DNS but for Layer 2) -- resolving a logical name to a physical address |
| Network segmentation| **Data lake zones** (raw/staging/curated) -- isolation for security and organization |

---

## Key Takeaways

1. A LAN is your local, high-speed network. A WAN connects LANs across distances.
2. Home networks follow the pattern: ISP > modem > router > switch/Wi-Fi > devices.
3. MAC addresses are hardware-level identifiers used only on the local network.
4. ARP resolves IP addresses to MAC addresses within a LAN via broadcast.
5. Network segmentation improves security and performance by isolating groups of devices.
6. VLANs create logical network divisions on physical switches.
7. VPNs create encrypted tunnels to make remote devices appear local.
8. Bastion hosts are hardened entry points -- SSH in, then hop to internal servers.
