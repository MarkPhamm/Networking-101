# Module 05: Subnets and Routing

## Overview

Every network needs a way to organize addresses into groups and a way to move traffic between those groups. Subnets divide IP address space into manageable chunks, and routing is the mechanism that forwards packets from one subnet to another. If you have ever partitioned a Hive table by date or region to keep queries fast and organized, you already understand the core idea behind subnetting.

---

## Subnet Masks

A subnet mask tells a device which portion of an IP address identifies the **network** and which portion identifies the **host** (a specific device on that network).

Take the IP address `192.168.1.100` with subnet mask `255.255.255.0`:

```
IP address:    192.168.1.100
Subnet mask:   255.255.255.0
               |-network--| |host|
```

- The `255` octets lock in the network portion: `192.168.1`
- The `0` octet is free for host addresses: `.0` through `.255`

The mask works through a bitwise AND operation. Anywhere the mask has a `1` bit, that bit belongs to the network portion. Anywhere it has a `0` bit, that bit belongs to the host portion.

### Binary Representation

The subnet mask `255.255.255.0` in binary is:

```
255.255.255.0
= 11111111.11111111.11111111.00000000
  |--- 24 ones ---|--- 8 zeros ---|
```

That is 24 consecutive `1` bits followed by 8 `0` bits. This is why it is written as `/24` in CIDR notation -- there are 24 network bits.

---

## CIDR Notation

CIDR (Classless Inter-Domain Routing) notation is a compact way to express an IP address and its subnet mask. Instead of writing `192.168.1.0` with mask `255.255.255.0`, you write `192.168.1.0/24`.

The number after the slash is the **prefix length** -- how many bits (from the left) belong to the network.

### Common CIDR Prefixes

| CIDR | Subnet Mask       | Network Bits | Host Bits | Total Addresses | Usable Hosts |
|------|-------------------|-------------|-----------|-----------------|-------------|
| /8   | 255.0.0.0         | 8           | 24        | 16,777,216      | 16,777,214  |
| /16  | 255.255.0.0       | 16          | 16        | 65,536          | 65,534      |
| /24  | 255.255.255.0     | 24          | 8         | 256             | 254         |
| /32  | 255.255.255.255   | 32          | 0         | 1               | 1           |

- **/8** -- Huge network. The first octet is fixed. Think `10.x.x.x` (the entire `10.0.0.0/8` private range). This is like a single massive partition with millions of rows.
- **/16** -- Large network. The first two octets are fixed. Think `172.16.x.x`. Commonly used for corporate networks.
- **/24** -- The most common subnet for small networks. The first three octets are fixed. Your home Wi-Fi is likely a `/24`. This gives you 254 usable addresses.
- **/32** -- A single host. No host bits at all. Used in routing tables and firewall rules to refer to exactly one IP address.

---

## Calculating Network Ranges

Given `192.168.1.0/24`:

- **Network address:** `192.168.1.0` (all host bits set to 0). This identifies the subnet itself and cannot be assigned to a device.
- **Broadcast address:** `192.168.1.255` (all host bits set to 1). Packets sent here go to every device on the subnet.
- **Usable host range:** `192.168.1.1` through `192.168.1.254`
- **Number of usable hosts:** 2^(32 - 24) - 2 = 256 - 2 = **254**

The formula for usable hosts:

```
Usable hosts = 2^(32 - prefix_length) - 2
```

You subtract 2 because the network address and broadcast address are reserved.

### Another Example: 10.0.0.0/16

- **Network address:** `10.0.0.0`
- **Broadcast address:** `10.0.255.255`
- **Usable host range:** `10.0.0.1` through `10.0.255.254`
- **Usable hosts:** 2^(32 - 16) - 2 = 65,536 - 2 = **65,534**

---

## Same Subnet vs. Different Subnet

This is one of the most important concepts in networking. When your device wants to send a packet to another IP address, it first asks: **"Is the destination on my subnet?"**

### Same Subnet -- Direct Communication

If both devices are on the same subnet, the sender uses ARP (Address Resolution Protocol) to find the destination's MAC address and sends the frame directly through the local switch. No router is needed.

```
Device A (192.168.1.10/24)  --->  Switch  --->  Device B (192.168.1.20/24)
```

### Different Subnet -- Must Use a Router

If the destination is on a different subnet, the sender cannot reach it directly. Instead, it sends the packet to its **default gateway** (the local router), which forwards it toward the destination.

```
Device A (192.168.1.10/24)  --->  Router  --->  Device B (10.0.0.50/16)
```

### How the Decision Is Made

The device performs a bitwise AND of both IPs with its own subnet mask. If the results match, same subnet. If not, different subnet.

```
My IP:          192.168.1.10
Destination:    192.168.1.20
My mask:        255.255.255.0

192.168.1.10  AND  255.255.255.0  =  192.168.1.0
192.168.1.20  AND  255.255.255.0  =  192.168.1.0
                                      ^^^ SAME -- communicate directly

My IP:          192.168.1.10
Destination:    10.0.0.50
My mask:        255.255.255.0

192.168.1.10  AND  255.255.255.0  =  192.168.1.0
10.0.0.50     AND  255.255.255.0  =  10.0.0.0
                                      ^^^ DIFFERENT -- send to router
```

---

## Default Gateway

The default gateway is the IP address of the router interface on your subnet. It is the "exit door" from your local network to the rest of the world.

When your device determines that a destination IP is not on the local subnet, it sends the packet to the default gateway. The router then takes over, consulting its routing table to decide where to send the packet next.

On a typical home network:
- Your device IP: `192.168.1.100`
- Default gateway: `192.168.1.1` (the router)
- Subnet mask: `255.255.255.0`

You can check your default gateway with:

```bash
# macOS
route -n get default | grep gateway

# or
netstat -rn | grep default
```

---

## Routing Tables

A routing table is a set of rules that tells a router (or your computer) how to forward packets. Each entry says: "To reach network X, send the packet via gateway Y through interface Z."

### Routing Table Columns

| Column      | Meaning                                                      |
|-------------|--------------------------------------------------------------|
| Destination | The target network (e.g., `10.0.0.0/16`)                    |
| Gateway     | The next-hop IP to forward the packet to                     |
| Flags       | Status indicators (U=up, G=gateway, H=host route)           |
| Interface   | The local network interface to send the packet out of (e.g., `en0`) |

### Example Routing Table

```
Destination        Gateway            Flags    Interface
default            192.168.1.1        UGS      en0
192.168.1.0/24     link#6             UCS      en0
10.0.0.0/8         192.168.1.254      UGS      en0
127.0.0.1          127.0.0.1          UH       lo0
```

Reading this table:
- **default** -- Any destination not matched by another rule goes to `192.168.1.1` (the default gateway).
- **192.168.1.0/24** -- Local subnet traffic goes directly out `en0` (no gateway needed, hence `link#6` meaning "directly connected").
- **10.0.0.0/8** -- Traffic for the `10.x.x.x` range goes via `192.168.1.254` (a different router on the local network).
- **127.0.0.1** -- Loopback traffic stays on the machine.

### Longest Prefix Match

When multiple routes match a destination, the routing table picks the **most specific** one (the longest prefix). For example, if there are entries for both `10.0.0.0/8` and `10.0.1.0/24`, a packet to `10.0.1.50` will use the `/24` route because it is more specific.

---

## Hop-by-Hop Forwarding

Routing is not planned end-to-end by a single device. Each router along the path makes an **independent** forwarding decision based on its own routing table. The packet hops from router to router, each one asking "what is the best next hop for this destination?"

```
Your PC  -->  Home Router  -->  ISP Router 1  -->  ISP Router 2  -->  ...  -->  Destination
  hop 1          hop 2              hop 3              hop 4
```

No single router knows the full path. Each one only knows: "To get closer to the destination, I should send this packet to the next router." This is exactly like a relay race -- each runner only needs to know where the next handoff point is.

You can see this hop-by-hop process in action with `traceroute`:

```bash
traceroute -n google.com
```

---

## Data Engineering Analogy

| Networking Concept | Data Engineering Equivalent |
|---|---|
| Subnets | **Hive/Spark partitions** -- dividing a large address space into smaller, organized segments. Just as you partition a table by `date` or `region` to avoid scanning everything, subnets divide a network so devices only broadcast within their segment. |
| Routing tables | **DAG edges / pipeline routing rules** -- rules that determine where data flows next. An Airflow DAG says "after task A, run task B." A routing table says "for network X, send via gateway Y." Both are lookup tables that control flow. |
| Default gateway | **Default sink / catch-all route** -- like a default branch in a pipeline that handles any data not matching a specific rule. |
| Longest prefix match | **Most specific partition pruning** -- the query optimizer picks the most specific partition that matches, just like the router picks the most specific route. |

---

## Key Takeaways

1. A subnet mask splits an IP address into network and host portions.
2. CIDR notation (`/24`) is shorthand for the number of network bits.
3. Usable hosts = 2^(32 - prefix) - 2 (subtract network and broadcast addresses).
4. If two IPs are on the same subnet, they communicate directly. If not, traffic goes through a router.
5. The default gateway is your exit to other networks.
6. Routing tables are ordered rules; the most specific (longest prefix) match wins.
7. Each router makes its own independent forwarding decision -- hop by hop.
