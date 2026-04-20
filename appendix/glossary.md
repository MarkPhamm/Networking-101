# Glossary

Alphabetical glossary of networking terms introduced across the Networking 101 modules.

---

**ACK (Acknowledge)** -- A TCP flag indicating that data or a connection request has been received. Part of the three-way handshake and used throughout a TCP session. *(Module 08)*

**ARP (Address Resolution Protocol)** -- A protocol that maps IP addresses to MAC addresses on a local network. Works via broadcast: "Who has this IP? Tell me your MAC." *(Module 07)*

**bastion host** -- A hardened server that serves as the single entry point for SSH access into a private network. Also called a jump box or jump server. *(Module 07)*

**broadcast address** -- A special IP address that sends a packet to all hosts on a subnet. For `192.168.1.0/24`, the broadcast address is `192.168.1.255`. *(Module 05)*

**CIDR (Classless Inter-Domain Routing)** -- A notation for specifying IP address ranges using a prefix length, such as `10.0.0.0/16`. The number after the slash indicates how many bits define the network portion. *(Module 05)*

**client** -- A program or device that initiates a connection to a server. Your SSH client connects to an SSH server; your browser connects to a web server. *(Module 01)*

**connection refused** -- A TCP RST (reset) response indicating that a host received your connection attempt but nothing is listening on the requested port. *(Module 01)*

**default gateway** -- The router that a device sends traffic to when the destination is not on the local subnet. It's the exit door from your LAN to the rest of the network. *(Module 05)*

**DHCP (Dynamic Host Configuration Protocol)** -- A protocol that automatically assigns IP addresses, subnet masks, gateways, and DNS servers to devices when they join a network. *(Module 03)*

**DNAT (Destination NAT)** -- A form of NAT that rewrites the destination IP address of incoming packets, typically used in port forwarding to redirect traffic to an internal server. *(Module 06)*

**DNS (Domain Name System)** -- The system that translates human-readable domain names (like `google.com`) into IP addresses (like `142.250.80.46`). Often called the phonebook of the internet. *(Module 03)*

**domain name** -- A human-readable address for a network resource, such as `example.com` or `db.internal.company.com`. Resolved to an IP address by DNS. *(Module 03)*

**encapsulation** -- The process of wrapping data in headers as it moves down the TCP/IP stack. Each layer adds its own header around the previous layer's output. *(Module 08)*

**ephemeral port** -- A temporary, high-numbered port (typically 49152-65535) assigned by the OS to the client side of a connection. It exists only for the duration of that connection. *(Module 04)*

**Ethernet** -- The most common LAN technology. Defines how data is framed and addressed (using MAC addresses) for transmission over wired local networks. *(Module 07)*

**firewall** -- A network security device or software that monitors and controls incoming and outgoing traffic based on predefined rules. Can allow, reject, or silently drop packets. *(Module 06)*

**FIN (Finish)** -- A TCP flag used to gracefully close a connection. Each side sends a FIN when it is done transmitting data. *(Module 08)*

**gateway** -- A device (usually a router) that connects two different networks. See also: default gateway. *(Module 05)*

**hop** -- One step in a packet's journey from source to destination. Each router the packet passes through is one hop. `traceroute` shows every hop. *(Module 05)*

**host** -- Any device with an IP address on a network. Can be a client, a server, a router, or anything else that communicates over IP. *(Module 03)*

**ICMP (Internet Control Message Protocol)** -- A network-layer protocol used for diagnostics and error reporting. `ping` uses ICMP Echo Request/Reply. `traceroute` uses ICMP Time Exceeded. *(Module 03)*

**IP address** -- A numerical label assigned to each device on a network. IPv4 addresses look like `192.168.1.1` (32 bits). Used for routing packets across networks. *(Module 03)*

**IPv4 (Internet Protocol version 4)** -- The fourth version of the Internet Protocol, using 32-bit addresses. Provides approximately 4.3 billion unique addresses. The version used throughout this guide. *(Module 03)*

**IPv6 (Internet Protocol version 6)** -- The successor to IPv4, using 128-bit addresses (e.g., `2001:db8::1`). Designed to solve IPv4 address exhaustion. Adoption is ongoing. *(Module 03)*

**jump host** -- See: bastion host. A server used as an intermediary to access internal systems. SSH's `-J` flag or `ProxyJump` directive enables single-command access through a jump host. *(Module 07)*

**LAN (Local Area Network)** -- A network covering a small area like a home, office, or building. Characterized by high speed, low latency, and private IP addressing. *(Module 07)*

**latency** -- The time it takes for a packet to travel from source to destination. Measured in milliseconds. LAN latency is typically <1ms; cross-internet latency ranges from 10-200+ ms. *(Module 03)*

**loopback** -- A virtual network interface that routes traffic back to the same machine. The IPv4 loopback address is `127.0.0.1`, and the interface is typically named `lo` or `lo0`. *(Module 01)*

**MAC address (Media Access Control address)** -- A 48-bit hardware address (e.g., `AA:BB:CC:DD:EE:FF`) burned into a network interface card. Used for communication within a LAN. Only meaningful on the local network segment. *(Module 07)*

**NAT (Network Address Translation)** -- A technique where a router rewrites IP addresses in packet headers, typically to allow multiple devices with private IPs to share a single public IP. *(Module 06)*

**netmask (subnet mask)** -- A bitmask that divides an IP address into network and host portions. For example, `255.255.255.0` (or `/24`) means the first 24 bits identify the network. *(Module 05)*

**network address** -- The first IP address in a subnet, identifying the network itself (not a host). For `192.168.1.0/24`, the network address is `192.168.1.0`. Not assignable to a device. *(Module 05)*

**packet** -- A unit of data transmitted over a network. At the IP layer, it includes a header (source/destination IP, TTL, protocol) and a payload (the data from the layer above). *(Module 05)*

**ping** -- A command-line tool that sends ICMP Echo Request packets to a host and measures the round-trip time. Used to test basic reachability. *(Module 03)*

**port** -- A 16-bit number (0-65535) that identifies a specific service or application on a host. SSH uses port 22, HTTP uses 80, HTTPS uses 443, PostgreSQL uses 5432. *(Module 04)*

**port forwarding** -- A NAT technique that redirects traffic arriving on a specific port of a public IP to a different host and/or port on a private network. *(Module 06)*

**private IP** -- An IP address from a reserved range (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) that is not routable on the public internet. Used within LANs and cloud VPCs. *(Module 03)*

**protocol** -- A set of rules defining how data is formatted, transmitted, and received. TCP, UDP, HTTP, SSH, DNS, and ICMP are all protocols operating at different layers. *(Module 01)*

**PSH (Push)** -- A TCP flag that tells the receiver to deliver data to the application immediately rather than buffering it. Common in interactive protocols like SSH. *(Module 08)*

**public IP** -- An IP address that is globally routable on the internet. Assigned by ISPs and registries. Any device on the internet can attempt to reach a public IP. *(Module 03)*

**resolver** -- A DNS client or server that performs DNS lookups. Your system's stub resolver sends queries to a recursive resolver (like 8.8.8.8), which does the actual work of walking the DNS hierarchy. *(Module 03)*

**routing** -- The process of forwarding packets from one network to another based on the destination IP address. Routers use routing tables to determine the next hop. *(Module 05)*

**routing table** -- A data structure in a router (or host) that maps destination network prefixes to next-hop addresses or interfaces. Checked for every outgoing packet. *(Module 05)*

**RST (Reset)** -- A TCP flag that forcefully terminates a connection without the graceful FIN exchange. Sent when a port has no listener ("Connection refused") or when an error occurs. *(Module 08)*

**server** -- A program or device that listens for and responds to incoming connections. An SSH server (`sshd`) listens on port 22; a web server listens on port 80/443. *(Module 01)*

**SNAT (Source NAT)** -- A form of NAT that rewrites the source IP address of outgoing packets, typically used when private IP hosts communicate with the internet through a router's public IP. *(Module 06)*

**SSH (Secure Shell)** -- A protocol for encrypted remote access to a machine. Operates over TCP port 22. Provides authentication (password or key-based) and an encrypted channel for commands and data. *(Module 01)*

**SSH agent** -- A background program (`ssh-agent`) that holds decrypted private keys in memory, allowing you to use SSH keys without re-entering the passphrase for each connection. *(Module 02)*

**SSH key** -- A cryptographic key pair (public + private) used for SSH authentication. The public key is placed on the server; the private key stays on your machine. More secure than passwords. *(Module 02)*

**stateful firewall** -- A firewall that tracks the state of network connections (e.g., TCP handshake, established sessions) and makes decisions based on connection state, not just individual packets. *(Module 06)*

**subnet** -- A logical subdivision of an IP network. Defined by a network address and a netmask (e.g., `10.0.1.0/24`). Devices on the same subnet can communicate directly; devices on different subnets need a router. *(Module 05)*

**SYN (Synchronize)** -- A TCP flag used to initiate a new connection. The first step of the three-way handshake. A SYN packet contains the client's initial sequence number. *(Module 08)*

**TCP (Transmission Control Protocol)** -- A transport-layer protocol that provides reliable, ordered, connection-oriented communication. Uses a three-way handshake, sequence numbers, and acknowledgments. *(Module 08)*

**TCP/IP** -- The suite of protocols that powers the internet. Named after its two most important protocols (TCP and IP), but includes many others (UDP, ICMP, ARP, DNS, HTTP, etc.). Also refers to the four-layer networking model. *(Module 08)*

**three-way handshake** -- The TCP connection establishment process: SYN (client to server), SYN-ACK (server to client), ACK (client to server). Must complete before any data is exchanged. *(Module 08)*

**timeout** -- A condition where a connection attempt or data transfer fails because no response was received within the expected time. Usually indicates a firewall DROP rule, wrong IP, or unreachable host. *(Module 01)*

**TLS (Transport Layer Security)** -- A cryptographic protocol that provides encryption and authentication over TCP. HTTPS is HTTP over TLS. The successor to SSL. *(Module 04)*

**traceroute** -- A command-line tool that shows the path (sequence of router hops) a packet takes to reach a destination. Uses TTL manipulation and ICMP to discover each hop. *(Module 05)*

**TTL (Time to Live)** -- A field in the IP header that limits a packet's lifetime. Decremented by 1 at each router hop. When it reaches 0, the packet is discarded and an ICMP Time Exceeded message is sent back. Prevents routing loops. *(Module 05)*

**UDP (User Datagram Protocol)** -- A transport-layer protocol that provides fast, connectionless, unreliable communication. No handshake, no sequence numbers, no retransmission. Used for DNS, streaming, and gaming. *(Module 08)*

**VLAN (Virtual LAN)** -- A logical partition of a physical network switch, creating isolated broadcast domains. Devices on different VLANs cannot communicate without a router, even if they share the same physical switch. *(Module 07)*

**VPN (Virtual Private Network)** -- An encrypted tunnel that connects a device or network to a remote network, making it appear as if the device is physically on the remote LAN. Used for remote access and site-to-site connectivity. *(Module 07)*

**WAN (Wide Area Network)** -- A network spanning a large geographic area, connecting multiple LANs. The internet is the largest WAN. Characterized by higher latency and lower speed compared to LANs. *(Module 07)*

---

[Back to main guide](../README.md)
