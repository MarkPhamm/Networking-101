# Module 05: Exercises -- Subnets and Routing

---

## Exercise 1: Read Your Routing Table

Your computer already has a routing table. Let's look at it.

### Steps

1. Open Terminal and run:

```bash
netstat -rn
```

2. Look at the output. You will see columns like `Destination`, `Gateway`, `Flags`, and `Netif` (network interface).

3. Find the **default** route. This is your default gateway -- the router your machine sends traffic to when it does not have a more specific route.

4. Now run this for a cleaner view of just the default route:

```bash
route -n get default
```

5. Note the `gateway` value in the output.

### Questions to Answer

- What is your default gateway IP address?
- What interface is the default route using (e.g., `en0` for Wi-Fi)?
- Do you see any routes for `127.0.0.1` or `::1`? What are those? (Hint: loopback/localhost.)
- Are there any routes to specific subnets (not just `default`)? What networks do they point to?

### What You Should Learn

Your machine is already making routing decisions every time it sends a packet. The routing table is the rulebook. The `default` route is the catch-all -- just like a `default` branch in a `CASE` statement or a catch-all route in an API gateway.

---

## Exercise 2: Trace a Route

The `traceroute` command shows you every hop a packet takes on its way to a destination.

### Steps

1. Run:

```bash
traceroute -n google.com
```

The `-n` flag tells traceroute to show IP addresses instead of trying to resolve hostnames (which is faster and clearer).

2. Count the number of hops (lines) before reaching the final destination.

3. Look at the IP addresses at each hop.

### Questions to Answer

- How many hops does it take to reach Google?
- Which hops show private IP addresses (e.g., `192.168.x.x`, `10.x.x.x`, `172.16-31.x.x`)? These are within your local network or your ISP's internal network.
- Which hops show public IP addresses? That is where your traffic enters the public internet.
- Do any hops show `* * *`? That means the router at that hop is not responding to traceroute probes (common -- many routers are configured to ignore them).
- What is the approximate round-trip time (in ms) to each hop? Does it increase as you go further?

### What You Should Learn

Each line is a router making an independent forwarding decision. This is hop-by-hop routing in action. The transition from private to public IPs shows exactly where your traffic leaves your local network and enters the wider internet -- analogous to data leaving a staging area and entering a production pipeline.

---

## Exercise 3: Subnet Math by Hand

Grab a piece of paper (or a text editor). Do these calculations without a subnet calculator.

### Problem A: 192.168.1.137/24

1. What is the subnet mask in dotted decimal? (Hint: /24 means 24 network bits.)
2. What is the network address? (Hint: set all host bits to 0.)
3. What is the broadcast address? (Hint: set all host bits to 1.)
4. What is the range of usable host addresses?
5. How many usable hosts are there?

### Problem B: 10.0.0.0/16

1. What is the subnet mask in dotted decimal?
2. What is the network address?
3. What is the broadcast address?
4. What is the range of usable host addresses?
5. How many usable hosts are there?

### Problem C (Bonus): 172.16.5.0/20

This one is trickier because the subnet boundary falls in the middle of the second octet.

1. What is the subnet mask in dotted decimal? (Hint: 20 bits = 255.255.?.0 -- what is the third octet?)
2. What is the network address?
3. What is the broadcast address?
4. What is the usable host range?
5. How many usable hosts?

### Answers

<details>
<summary>Click to reveal answers</summary>

**Problem A: 192.168.1.137/24**
1. Subnet mask: `255.255.255.0`
2. Network address: `192.168.1.0`
3. Broadcast address: `192.168.1.255`
4. Usable range: `192.168.1.1` -- `192.168.1.254`
5. Usable hosts: 2^8 - 2 = **254**

**Problem B: 10.0.0.0/16**
1. Subnet mask: `255.255.0.0`
2. Network address: `10.0.0.0`
3. Broadcast address: `10.0.255.255`
4. Usable range: `10.0.0.1` -- `10.0.255.254`
5. Usable hosts: 2^16 - 2 = **65,534**

**Problem C: 172.16.5.0/20**
1. Subnet mask: `255.255.240.0` (20 bits = 11111111.11111111.11110000.00000000, so the third octet is 11110000 = 240)
2. Network address: `172.16.0.0` (172.16.5.0 AND 255.255.240.0 = 172.16.0.0, because 5 AND 240 = 0)
3. Broadcast address: `172.16.15.255` (host bits all 1s: third octet = 0 OR 00001111 = 15)
4. Usable range: `172.16.0.1` -- `172.16.15.254`
5. Usable hosts: 2^12 - 2 = **4,094**

</details>

### What You Should Learn

Subnet math is a fundamental skill. Understanding binary is the key -- once you see that a `/20` means "20 bits for network, 12 bits for hosts," the rest follows. This is like understanding how partition keys work in a distributed database: the key determines which bucket data lands in.

---

## Exercise 4: Am I on the Same Subnet?

This exercise ties subnetting to real routing decisions.

### Setup

Find your current IP address and subnet mask:

```bash
ifconfig en0 | grep "inet "
```

You will see something like:

```
inet 192.168.1.42 netmask 0xffffff00 broadcast 192.168.1.255
```

The `0xffffff00` is hexadecimal for `255.255.255.0` which is `/24`.

### Questions

For each of the following destination IPs, determine: **Is it on the same subnet as you, or does it need to be routed through the gateway?**

Assume your IP is `192.168.1.42/24` (adjust to your actual IP and mask):

1. `192.168.1.1` (your router)
2. `192.168.1.200` (another device on the network)
3. `192.168.2.10` (note the different third octet)
4. `10.0.0.1` (a completely different private network)
5. `8.8.8.8` (Google's public DNS)

### How to Check

For each IP, apply the subnet mask to both your IP and the destination:

```
Your IP AND mask = your network address
Destination AND mask = destination's network address

If they match --> same subnet --> communicate directly via ARP
If they differ --> different subnet --> send to default gateway
```

### Answers

<details>
<summary>Click to reveal answers</summary>

With your IP `192.168.1.42` and mask `255.255.255.0`:

Your network = `192.168.1.0`

1. `192.168.1.1` AND `255.255.255.0` = `192.168.1.0` --> **Same subnet** (direct)
2. `192.168.1.200` AND `255.255.255.0` = `192.168.1.0` --> **Same subnet** (direct)
3. `192.168.2.10` AND `255.255.255.0` = `192.168.2.0` --> **Different subnet** (routed)
4. `10.0.0.1` AND `255.255.255.0` = `10.0.0.0` --> **Different subnet** (routed)
5. `8.8.8.8` AND `255.255.255.0` = `8.8.8.0` --> **Different subnet** (routed)

</details>

### What You Should Learn

Every time your computer sends a packet, it performs this exact check. This is the most fundamental routing decision in networking: local delivery or forward to the gateway. It is analogous to deciding whether a query can be answered by the local cache or needs to go to the remote database.
