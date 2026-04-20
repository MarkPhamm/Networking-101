# Module 03: IP Addressing and DNS

## Why This Matters

When you tried to SSH into your friend's server, you typed something like `ssh user@some-address`. But what exactly is that address? How does your computer know where to find it on the internet? This module covers the addressing system that makes networked communication possible.

---

## What Is an IP Address?

An IP address is a **network address for a computer** -- think of it as a street address for a device on a network. Just like the postal system needs a unique address to deliver mail to your house, networks need a unique address to deliver data packets to the right machine.

Every device participating in a network has at least one IP address. When you SSH into a server, your machine needs to know the server's IP address so packets can be routed to it across potentially dozens of intermediate networks.

---

## IPv4: The Address Format You'll See Everywhere

IPv4 addresses are written in **dotted decimal notation** -- four numbers separated by dots:

```
192.168.1.100
```

Each number ranges from 0 to 255, because each is an **8-bit octet**. Four octets = **32 bits total**.

```
192      .  168      .  1        .  100
11000000    10101000    00000001    01100100
[8 bits]   [8 bits]   [8 bits]   [8 bits]  = 32 bits total
```

With 32 bits, there are 2^32 = **~4.3 billion possible addresses**. That sounds like a lot, but with billions of devices on the internet today, we ran out. This shortage shaped much of how networking works in practice.

---

## Private vs. Public IP Addresses

### Private IP Ranges

Because there aren't enough public IPv4 addresses for every device, certain ranges are reserved for **private use** -- they only work within a local network and are not routable on the public internet:

| Range | CIDR Notation | Number of Addresses | Typical Use |
|-------|--------------|--------------------:|-------------|
| 10.0.0.0 -- 10.255.255.255 | 10.0.0.0/8 | ~16.7 million | Large organizations, cloud VPCs |
| 172.16.0.0 -- 172.31.255.255 | 172.16.0.0/12 | ~1 million | Medium networks |
| 192.168.0.0 -- 192.168.255.255 | 192.168.0.0/16 | ~65,000 | Home networks, small offices |

Your home router assigns private IPs (like 192.168.1.100) to every device on your Wi-Fi. These addresses are reused by millions of other home networks -- they only have meaning inside your local network.

**Why do private IPs exist?** Conservation. Instead of giving every laptop, phone, and smart fridge a globally unique public IP, your entire household shares a single public IP. Your router uses **NAT (Network Address Translation)** to map private addresses to the one public IP when traffic leaves your network. We'll cover NAT in detail in a later module.

### Public IP Addresses

Public IPs are **globally unique** and routable on the internet. They're assigned by your **ISP (Internet Service Provider)**, which gets them from regional registries. When you SSH into a server on the internet, you're connecting to its public IP.

```
# Your home network:
Your laptop:  192.168.1.100  (private -- only meaningful on your LAN)
Your router:  73.45.123.89   (public  -- visible to the entire internet)

# Your friend's server:
Server:       143.198.67.42  (public  -- the address you'd SSH to)
```

### Localhost and 127.0.0.1

There's one special address every developer should know:

```
127.0.0.1  =  localhost  =  "this machine"
```

This is the **loopback interface** -- when you send traffic to 127.0.0.1, it never leaves your machine. The entire 127.0.0.0/8 range (127.0.0.1 through 127.255.255.255) is reserved for loopback.

You use localhost constantly in development:

```bash
# Connect to a database running on your own machine
psql -h localhost -p 5432

# Test a web server you're running locally
curl http://localhost:8080

# SSH to your own machine (useful for testing)
ssh localhost
```

---

## IPv6: A Brief Mention

IPv6 was created to solve the address exhaustion problem. Instead of 32 bits, IPv6 uses **128 bits**, written in hexadecimal:

```
IPv4:  192.168.1.100
IPv6:  2001:0db8:85a3:0000:0000:8a2e:0370:7334
```

128 bits = 2^128 = **~340 undecillion addresses** (340 followed by 36 zeros). That's enough to give every grain of sand on Earth its own IP address, many times over.

IPv6 adoption is growing but IPv4 still dominates. For most practical networking tasks today, you'll work with IPv4. When you see an IPv6 address in the wild, you'll recognize it by the colons and hex digits.

---

## Domain Names: Human-Readable Addresses

Nobody wants to memorize `142.250.80.46`. That's why we have **domain names** like `google.com` -- human-readable aliases that map to IP addresses.

The **Domain Name System (DNS)** is the distributed database that translates domain names into IP addresses. It's one of the most critical pieces of internet infrastructure.

---

## How DNS Resolution Works

When you type `ssh user@myserver.example.com`, your computer needs to turn `myserver.example.com` into an IP address. Here's the resolution chain:

### The DNS Resolution Chain

```
1. Application asks: "What's the IP for myserver.example.com?"
        |
        v
2. Local DNS cache -- has the OS seen this recently?
        |  (miss)
        v
3. /etc/hosts file -- any manual overrides?
        |  (miss)
        v
4. DNS resolver (your ISP's or 8.8.8.8) -- has it cached?
        |  (miss)
        v
5. Root nameservers -- "Who handles .com?"
        |
        v
6. TLD nameservers -- "Who handles example.com?"
        |
        v
7. Authoritative nameserver for example.com
        |
        v
8. Answer: "myserver.example.com = 143.198.67.42"
```

**Step by step:**

1. **Application** -- Your SSH client calls the OS to resolve the hostname.
2. **Local cache** -- The OS checks if it recently resolved this name. If so, it uses the cached result.
3. **/etc/hosts** -- The OS checks this local file for manual name-to-IP mappings. This is checked before external DNS (on most systems).
4. **DNS resolver** (also called a recursive resolver) -- Usually provided by your ISP, or a public one like Google (8.8.8.8) or Cloudflare (1.1.1.1). The resolver does the heavy lifting.
5. **Root nameservers** -- 13 sets of root servers that know which servers are authoritative for each top-level domain (.com, .org, .net, etc.).
6. **TLD nameservers** -- The servers responsible for a top-level domain. The .com TLD servers know which nameservers handle `example.com`.
7. **Authoritative nameserver** -- The final authority. This server has the actual DNS records for the domain and returns the IP.

### DNS Record Types

DNS doesn't just map names to IPs. There are several record types:

| Record | Purpose | Example |
|--------|---------|---------|
| **A** | Maps name to IPv4 address | `google.com -> 142.250.80.46` |
| **AAAA** | Maps name to IPv6 address | `google.com -> 2607:f8b0:4004:800::200e` |
| **CNAME** | Alias to another domain name | `www.example.com -> example.com` |
| **MX** | Mail server for the domain | `google.com -> smtp.google.com` (priority 10) |
| **NS** | Nameserver for the domain | `google.com -> ns1.google.com` |

### TTL (Time To Live)

Every DNS record has a **TTL** -- the number of seconds a resolver should cache the result before asking again. A TTL of 3600 means "cache this answer for 1 hour."

```
google.com.    300    IN    A    142.250.80.46
                ^
                TTL = 300 seconds (5 minutes)
```

- **Low TTL (60-300s):** The domain can be re-pointed quickly (good for failovers), but generates more DNS queries.
- **High TTL (3600-86400s):** Fewer queries, faster resolution from cache, but changes take longer to propagate.

When you change a DNS record and "wait for propagation," you're waiting for caches worldwide to expire based on the old TTL.

---

## Data Engineering Analogy

If you've worked with microservices or cloud infrastructure, DNS will feel familiar:

- **DNS is like service discovery.** Tools like Consul, Kubernetes DNS, or AWS Service Discovery do exactly what DNS does -- translate a service name (`postgres-primary.internal`) into an IP address. DNS is the internet's original service discovery system.
- **Private IPs are like internal database hosts.** Your RDS instance has a private hostname like `mydb.abc123.us-east-1.rds.amazonaws.com` that only resolves inside your VPC. From the outside internet, that name means nothing. Same concept as private IP ranges -- internal-only addressing.
- **TTL is like cache expiration in Redis or Memcached.** You cache a value for a certain duration to avoid hitting the source of truth on every request. DNS TTL works the same way -- it's a caching strategy with explicit expiration.
- **/etc/hosts is like hardcoded connection strings.** Sometimes you bypass service discovery and point directly at an IP in your config. `/etc/hosts` is the system-level version of that.

---

## Key Takeaways

1. **IP addresses are network addresses** -- they identify devices on a network so packets can be routed to them.
2. **Private IPs** (10.x, 172.16-31.x, 192.168.x) only work within a local network. **Public IPs** are globally unique.
3. **127.0.0.1 (localhost)** is the loopback address -- traffic to it never leaves your machine.
4. **DNS translates domain names to IP addresses** through a hierarchical chain of nameservers.
5. **DNS records have types** (A, AAAA, CNAME, MX, NS) and **TTLs** that control caching.
6. When SSH says "could not resolve hostname," it means DNS failed somewhere in this chain.

---

Next: [Exercises](exercises.md) | [Cheatsheet](cheatsheet.md)
