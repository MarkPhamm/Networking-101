# Module 07: Exercises -- LAN, WAN, and Network Segments

---

## Exercise 1: Map Your LAN

Discover what devices are on your local network and what interfaces your Mac has.

### Steps

1. **List your network interfaces:**

```bash
networksetup -listallhardwareports
```

This shows each interface name (e.g., Wi-Fi, Ethernet), the device name (e.g., `en0`, `en1`), and the MAC address.

2. **Find your MAC address:**

Look at the output from the command above. The "Ethernet Address" for your Wi-Fi interface is your wireless MAC address.

You can also run:

```bash
ifconfig en0 | grep ether
```

3. **View devices on your LAN using ARP:**

```bash
arp -a
```

This shows all IP-to-MAC mappings your machine currently knows about. Each entry represents a device your Mac has recently communicated with on the local network.

4. **Discover more devices by pinging the broadcast address (optional):**

```bash
# Find your broadcast address
ifconfig en0 | grep broadcast

# Ping the broadcast address to trigger ARP for all responding devices
ping -c 3 192.168.1.255  # Use your actual broadcast address

# Now check ARP again -- you should see more entries
arp -a
```

### Questions to Answer

- What is the MAC address of your Wi-Fi interface?
- How many devices show up in your ARP table?
- Can you identify which entry is your router? (Hint: it should match your default gateway IP.)
- Do any MAC addresses start with the same first three octets? If so, they are likely from the same manufacturer.

### What You Should Learn

Your LAN is populated with devices you may not even be aware of -- phones, smart speakers, TVs, other family members' laptops. The ARP table is a snapshot of who your machine knows about. This is your first step in understanding the Layer 2 (data link) landscape of your network.

---

## Exercise 2: ARP in Action

Watch ARP do its job in real time. We will clear the ARP cache, then observe it getting rebuilt.

### Steps

1. **View the current ARP cache:**

```bash
arp -a
```

Count the entries. Note your router's IP and MAC.

2. **Clear the ARP cache:**

```bash
sudo arp -d -a
```

This removes all cached IP-to-MAC mappings.

3. **Verify the cache is empty (or nearly so):**

```bash
arp -a
```

You should see far fewer entries (some may persist for active connections).

4. **Ping your router to trigger an ARP request:**

```bash
ping -c 1 192.168.1.1   # Use your actual router IP
```

5. **Check the ARP cache again:**

```bash
arp -a
```

You should now see a fresh entry for your router.

6. **Ping another device on your LAN (if you know its IP):**

```bash
ping -c 1 192.168.1.XX   # Replace with another device's IP
```

7. **Check ARP once more:**

```bash
arp -a
```

The new device should appear.

### What Just Happened

When you pinged the router, your Mac could not send the IP packet without knowing the router's MAC address. So it:

1. Sent an ARP broadcast: "Who has 192.168.1.1? Tell 192.168.1.XX" (broadcast to `FF:FF:FF:FF:FF:FF`)
2. The router replied: "192.168.1.1 is at AA:BB:CC:DD:EE:FF" (unicast reply)
3. Your Mac cached the mapping and then sent the ICMP ping inside an Ethernet frame addressed to that MAC

This happens automatically and invisibly for every new IP your machine communicates with on the LAN. It is the glue between Layer 3 (IP) and Layer 2 (Ethernet).

### What You Should Learn

ARP is invisible but essential. Every time you connect to a new device on your LAN, ARP runs behind the scenes. Understanding ARP helps you debug issues like "I can ping IPs outside my network but not a device on my own LAN" -- which often points to an ARP problem.

---

## Exercise 3: Identify Your Network Path

Trace the full path from your device to the internet and draw your home network topology.

### Steps

1. **Identify your device's IP and interface:**

```bash
ifconfig en0 | grep "inet "
```

2. **Identify your router (default gateway):**

```bash
route -n get default | grep gateway
```

3. **Identify your public IP (your router's external IP):**

```bash
curl -s ifconfig.me
```

4. **Trace the path to an internet host:**

```bash
traceroute -n 8.8.8.8
```

Look at the first few hops:
- **Hop 1** is usually your router (private IP like `192.168.1.1`)
- **Hop 2** might be your ISP's gateway (could be another private IP or the first public IP)
- **Subsequent hops** are ISP backbone routers and internet infrastructure

5. **Draw your network topology.**

Use a text editor, paper, or diagramming tool. Include:

```
[Your Device]
  IP: ___________
  MAC: ___________
  Interface: en0
       |
       | (Wi-Fi / Ethernet)
       |
[Home Router]
  LAN IP: ___________
  WAN IP: ___________ (public, from curl ifconfig.me)
  NAT: Yes
  DHCP: Yes
       |
       | (ISP link)
       |
[ISP Gateway]
  IP: ___________ (from traceroute hop 2)
       |
     ... (more hops from traceroute)
       |
[Destination: 8.8.8.8]
```

### Questions to Answer

- At which hop does the IP address change from private to public? That is the NAT boundary.
- How many hops are within private address space?
- What is the approximate round-trip latency to your router vs. to 8.8.8.8?
- Can you identify your ISP from the IPs in the traceroute? (Try looking up one of the public IPs at `https://ipinfo.io/IP_ADDRESS`)

### What You Should Learn

You now have a mental model of your entire network path. Every packet you send traverses this chain. When something breaks -- slow loading, connection timeouts, DNS failures -- knowing this topology helps you pinpoint whether the problem is local (your device, your router), with your ISP, or further out on the internet. This is the networking equivalent of tracing a data pipeline from source to sink to find where a failure occurred.

---

## Exercise 4: SSH Jump Host (Conceptual)

This exercise explains the SSH ProxyJump pattern. You do not need actual remote servers to understand the concept -- but if you have access to any cloud instances, try it for real.

### The Problem

You need to SSH into a server (`10.0.1.50`) that is on a private network. Your laptop is on a different network and cannot reach `10.0.1.50` directly. But there is a bastion host (`bastion.company.com`) that is reachable from the internet AND has access to the private network.

### The Solution: ProxyJump

```bash
ssh -J admin@bastion.company.com ubuntu@10.0.1.50
```

This does the following:
1. Your laptop connects to `bastion.company.com` via SSH
2. From the bastion, an SSH connection is opened to `10.0.1.50`
3. Your terminal session is tunneled through both connections seamlessly

### SSH Config for Persistent Setup

Instead of typing the `-J` flag every time, configure `~/.ssh/config`:

```
# The bastion host (reachable from the internet)
Host bastion
    HostName bastion.company.com
    User admin
    IdentityFile ~/.ssh/bastion_key

# Internal server (only reachable via bastion)
Host internal-db
    HostName 10.0.1.50
    User ubuntu
    IdentityFile ~/.ssh/internal_key
    ProxyJump bastion

# Another internal server
Host internal-app
    HostName 10.0.1.60
    User deploy
    IdentityFile ~/.ssh/internal_key
    ProxyJump bastion
```

Now you can just type:

```bash
ssh internal-db
```

### Multi-Hop Chains

You can chain multiple jumps:

```bash
ssh -J admin@bastion1,admin@bastion2 ubuntu@final_destination
```

Or in SSH config:

```
Host bastion2
    HostName 10.0.0.5
    User admin
    ProxyJump bastion1

Host deep-server
    HostName 10.0.99.10
    User ubuntu
    ProxyJump bastion2
```

### Port Forwarding Through a Jump Host

A common data engineering pattern -- forward a database port through a bastion:

```bash
# Forward local port 5432 to a remote PostgreSQL server through the bastion
ssh -J admin@bastion.company.com -L 5432:db.internal:5432 ubuntu@10.0.1.50 -N
```

Now you can connect to `localhost:5432` from your laptop and it reaches `db.internal:5432` on the private network.

### Questions to Think About

- Why not just expose every server to the internet directly?
- What happens if the bastion host is compromised? How does that affect security?
- How is this similar to connecting to a production database through a jump server in your data engineering work?
- If you use AWS, how does this compare to using AWS Systems Manager Session Manager as an alternative to bastions?

### What You Should Learn

The jump host pattern is ubiquitous in production environments. Almost every data engineer has to tunnel through a bastion to reach a production database at some point. Understanding how ProxyJump works means you can set it up once in your SSH config and forget about it -- and you will understand what is happening when your connection drops or times out.
