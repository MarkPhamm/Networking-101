# Module 03 Exercises: IP Addressing and DNS

Work through these exercises in order. Each builds on concepts from the previous one.

---

## Exercise 1: Find Your IP Addresses

**Goal:** Understand the difference between your private and public IP.

### Steps

**Find your private IP:**

```bash
# macOS
ifconfig en0

# Look for the "inet" line (not "inet6"):
# inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255

# Alternative (works on macOS and Linux):
ifconfig en0 | grep "inet " | awk '{print $2}'
```

**Find your public IP:**

```bash
curl -s ifconfig.me
# Example output: 73.45.123.89

# Alternative services:
curl -s icanhazip.com
curl -s api.ipify.org
```

### Questions to Answer

1. Write down both IPs. Are they the same? Why not?
2. Which IP range does your private IP fall into? (10.x, 172.16-31.x, or 192.168.x?)
3. If you check another device on the same Wi-Fi (phone, another laptop), will it have the same private IP? The same public IP?
4. Try `ifconfig lo0` -- what IP do you see? What interface is this?

### What You Should See

Your private IP is assigned by your router and is only meaningful on your local network. Your public IP is assigned by your ISP and is what the rest of the internet sees. Every device on your home network shares the same public IP (your router handles the translation via NAT).

---

## Exercise 2: DNS Resolution in Action

**Goal:** Watch DNS resolution happen and understand the output.

### Steps

**Basic DNS lookups:**

```bash
# Full dig output (lots of detail)
dig google.com

# Just the IP address
dig +short google.com

# Using nslookup (different tool, same job)
nslookup google.com

# Using host (simplest output)
host google.com
```

**Read the dig output carefully:**

```bash
dig google.com
```

In the output, find:

- **QUESTION SECTION** -- what you asked for
- **ANSWER SECTION** -- the response (IP address, TTL, record type)
- **Query time** -- how long the lookup took in milliseconds
- **SERVER** -- which DNS resolver answered your query

**Trace the full resolution chain:**

```bash
dig +trace google.com
```

This shows every step of the DNS resolution process -- from root servers to TLD servers to the authoritative nameserver.

### Questions to Answer

1. What is the A record IP for `google.com`? Does it change if you run the command multiple times? (Large services often have multiple IPs.)
2. What is the TTL value on the A record? Convert it to minutes.
3. In the `dig` output, what DNS server answered your query? (Look for the `SERVER:` line at the bottom.)
4. In the `dig +trace` output, identify:
   - Which root server was queried?
   - Which TLD server handles `.com`?
   - Which authoritative nameserver has the final answer?
5. Compare the query time of `dig google.com` on the first run vs. a second run right after. Is the second faster? Why?

### What You Should See

The `+trace` output walks you through the exact hierarchy described in the README: root servers point to .com TLD servers, which point to Google's authoritative nameservers, which return the final IP. The second `dig` is usually faster because the result is now cached by your local resolver.

---

## Exercise 3: Local DNS Override with /etc/hosts

**Goal:** Manually map a hostname to an IP address, bypassing DNS entirely.

### Steps

**View the current hosts file:**

```bash
cat /etc/hosts
# You'll see localhost entries already there
```

**Add a custom entry:**

```bash
# Edit /etc/hosts (requires sudo)
sudo nano /etc/hosts

# Add this line at the bottom:
# 127.0.0.1    mytest.local
```

**Verify the mapping works:**

```bash
# Ping the custom hostname
ping -c 3 mytest.local
# Should show: PING mytest.local (127.0.0.1)

# Verify with dscacheutil (macOS)
dscacheutil -q host -a name mytest.local
```

**Try connecting to it:**

```bash
# If SSH is enabled on your machine:
ssh localhost -p 22        # This should work (standard localhost)
ssh mytest.local -p 22     # This should also work (resolves to 127.0.0.1)

# If SSH isn't enabled, try curl instead:
# Start a quick server in another terminal: python3 -m http.server 8080
curl http://mytest.local:8080
```

**Clean up when done:**

```bash
# Remove the line you added
sudo nano /etc/hosts
# Delete the "127.0.0.1    mytest.local" line and save

# Flush DNS cache (macOS)
sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
```

### Questions to Answer

1. When you pinged `mytest.local`, what IP did it resolve to? Did it hit any external DNS server?
2. Why is `/etc/hosts` checked before external DNS resolvers (on most systems)?
3. Can you think of a practical use case for `/etc/hosts` overrides? (Hint: think about testing a new server before updating DNS.)
4. What would happen if you mapped `google.com` to `127.0.0.1` in `/etc/hosts`? Try it briefly, then `curl google.com` -- what happens? (Remove it after!)

### What You Should See

The `/etc/hosts` file lets you override DNS resolution locally. This is incredibly useful for testing -- for example, you can point a production domain at a staging server's IP on your machine only, without affecting anyone else. It's the networking equivalent of mocking a dependency in a unit test.

---

## Exercise 4: Explore DNS Record Types

**Goal:** Discover the different types of information stored in DNS.

### Steps

**Query different record types:**

```bash
# MX records (mail servers)
dig google.com MX

# NS records (nameservers)
dig google.com NS

# AAAA records (IPv6 addresses)
dig google.com AAAA

# TXT records (often used for domain verification, SPF)
dig google.com TXT

# ALL records at once
dig google.com ANY
```

**Try CNAME lookups:**

```bash
# www subdomain is often a CNAME
dig www.github.com
# Look for CNAME in the answer -- it may point to another hostname

dig +short www.github.com
# You might see a chain: www.github.com -> github.github.io -> actual IP
```

**Check a domain's full DNS picture:**

```bash
# Nameservers for the domain
dig +short google.com NS

# Then query a specific nameserver directly
dig @ns1.google.com google.com A
```

### Questions to Answer

1. How many MX records does `google.com` have? What do the priority numbers mean? (Lower = higher priority.)
2. What are the NS records for `google.com`? How many nameservers does it have?
3. Does `google.com` have an AAAA record? What does the IPv6 address look like?
4. What is `www.github.com` a CNAME for? Why would a company use a CNAME instead of an A record?
5. When you query a specific nameserver with `dig @ns1.google.com`, you're skipping your local resolver. Why might this be useful for debugging?

### What You Should See

DNS is much richer than simple name-to-IP mapping. MX records tell email systems where to deliver mail. NS records delegate authority for a domain. CNAMEs create aliases so multiple hostnames can point to the same place (handy when infrastructure changes -- you update one A record instead of dozens). This is the same pattern as having a single source of truth in a data pipeline -- CNAMEs are like views that point to a base table.

---

## Bonus Challenge

**Build a mental model of your DNS path:**

```bash
# 1. What DNS resolver are you using?
cat /etc/resolv.conf 2>/dev/null || scutil --dns | head -20

# 2. How fast is your resolver?
dig google.com | grep "Query time"

# 3. Compare with a public resolver:
dig @8.8.8.8 google.com | grep "Query time"
dig @1.1.1.1 google.com | grep "Query time"

# 4. Measure a full uncached resolution:
dig @8.8.8.8 +trace google.com | tail -10
```

Think about: which resolver is fastest for you? Your ISP's, Google's (8.8.8.8), or Cloudflare's (1.1.1.1)? In data engineering terms, this is like benchmarking which metadata store has the lowest latency for your location.
