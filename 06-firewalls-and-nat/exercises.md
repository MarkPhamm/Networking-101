# Module 06: Exercises -- Firewalls and NAT

---

## Exercise 1: Check Your macOS Firewall

Let's see what firewall protections are currently active on your Mac.

### Steps

1. **Check the Application Firewall status via GUI:**

   Go to **System Settings > Network > Firewall**. Is it turned on or off?

2. **Check pf (Packet Filter) status from Terminal:**

```bash
sudo pfctl -s info | grep -i status
```

This tells you if the low-level packet filter is enabled.

3. **View current pf rules:**

```bash
sudo pfctl -s rules
```

If pf is active, you will see the currently loaded rules. If there are no rules, you will see an empty output.

4. **Check the pf configuration file:**

```bash
cat /etc/pf.conf
```

This is the default pf configuration. Look at the rules -- you will see macOS ships with a minimal set.

5. **Toggle the Application Firewall and observe:**

   - Turn the Application Firewall ON (if it was off) in System Settings
   - Run a local HTTP server: `python3 -m http.server 8080`
   - From another device on your network (or another terminal), try: `curl http://YOUR_IP:8080`
   - Observe whether the firewall prompts you to allow or deny the connection
   - Turn it off again and retry

### Questions to Answer

- Is your macOS Application Firewall currently enabled?
- Is pf enabled? Are there any active pf rules?
- When you toggled the firewall, did the behavior change for incoming connections?
- What is the difference between the Application Firewall (System Settings) and pf?

### What You Should Learn

macOS has two layers of firewall. The GUI firewall is per-application and simple. `pf` is per-packet and powerful. In practice, most home Macs rely on the router's firewall and NAT for protection, with the host firewall as a second layer. In cloud environments, this maps to Security Groups (network-level) plus host-level `iptables` or `ufw`.

---

## Exercise 2: Observe NAT in Action

You are behind NAT right now. Let's prove it.

### Steps

1. **Find your private (local) IP:**

```bash
ifconfig en0 | grep "inet "
```

You should see something like `192.168.1.x` or `10.0.0.x`.

2. **Find your public IP:**

```bash
curl -s ifconfig.me
```

This contacts an external service that tells you what IP it sees your request coming from -- your router's public IP after NAT.

3. **Compare the two:**

```
Private IP:  192.168.1.42       <-- Your device's actual address
Public IP:   73.162.xxx.xxx     <-- What the internet sees (your router's IP)
```

These are different because your router performed SNAT -- it replaced your private IP with its public IP before sending your request to the internet.

4. **Explore your router's NAT table (optional but educational):**

   - Open a browser and go to your router's admin page (typically `http://192.168.1.1` or `http://192.168.0.1`)
   - Look for a section called "Connected Devices," "DHCP Client List," or "NAT Table"
   - You should see a list of all devices on your network with their private IPs and MAC addresses

5. **See the NAT mapping in action:**

   Open a connection and check:

```bash
# Start a long-running connection
curl -s -o /dev/null --max-time 30 http://httpbin.org/delay/25 &

# View active NAT/network connections
netstat -an | grep httpbin
# or if that shows nothing:
netstat -an | grep ESTABLISHED | head -20
```

### Questions to Answer

- What is your private IP? What is your public IP?
- Are they in the same address range? Why not?
- How many devices on your network share the same public IP?
- Can a server on the internet initiate a connection to your private IP directly? Why or why not?

### What You Should Learn

NAT is invisible to most users, but it is happening on every packet you send. Your private IP is only meaningful within your LAN. The internet only sees your router's public IP. This is why you cannot just tell someone "SSH to 192.168.1.42" -- that address is meaningless outside your network. It is like giving someone a row ID from your local database and expecting it to work in a different database.

---

## Exercise 3: Port Forwarding -- Diagram It Out

This is a design exercise. Grab paper or a text editor.

### Scenario

Your friend has a Linux server at home that they want you to SSH into. Here is the setup:

- Friend's server private IP: `192.168.0.50`
- SSH is running on port `22` on the server
- Friend's router public IP: `203.0.113.5`
- Friend's router private IP: `192.168.0.1`

### Tasks

1. **Draw the network topology:**

```
   [Your laptop]
       |
    Internet
       |
   [Friend's Router: 203.0.113.5]
       |
   [Friend's LAN: 192.168.0.0/24]
       |
   [Friend's Server: 192.168.0.50:22]
```

2. **What port-forward rule needs to be configured on the friend's router?**

   Write it in the format:
   ```
   External Port: ____  -->  Internal IP: ____  Internal Port: ____
   ```

3. **What SSH command would you type from your laptop?**

   Write the full `ssh` command.

4. **Trace the packet flow step by step:**
   - What source and destination IP/port does your SSH packet have when it leaves your laptop?
   - What happens when it hits the friend's router?
   - What source and destination does it have when it reaches the server?

### Answers

<details>
<summary>Click to reveal answers</summary>

**Port-forward rule on friend's router:**
```
External Port: 2222  -->  Internal IP: 192.168.0.50  Internal Port: 22
```
(Using 2222 externally is common to avoid exposing port 22 directly, but 22 would also work.)

**SSH command:**
```bash
ssh -p 2222 username@203.0.113.5
```

**Packet flow:**
1. Your laptop sends: src=`YOUR_PUBLIC_IP:random_port`, dst=`203.0.113.5:2222`
2. Friend's router receives on port 2222, DNAT rewrites destination: dst=`192.168.0.50:22`
3. Server receives: src=`YOUR_PUBLIC_IP:random_port`, dst=`192.168.0.50:22`
4. Server replies: src=`192.168.0.50:22`, dst=`YOUR_PUBLIC_IP:random_port`
5. Router SNAT rewrites source: src=`203.0.113.5:2222`, dst=`YOUR_PUBLIC_IP:random_port`
6. Your laptop receives the reply

</details>

### What You Should Learn

Port forwarding is DNAT in action. Without it, incoming connections from the internet have no way to reach a specific device on a private network. This is exactly like Docker port mapping (`-p 2222:22`) or Kubernetes service port configuration -- you are mapping an external-facing port to an internal one.

---

## Exercise 4: Simulate a Blocked Port (Conceptual/Guided)

This exercise walks through how a firewall blocks a port. **Be careful with pf rules -- always have a way to undo them.** We will add a rule, test it, and immediately remove it.

### Scenario

You want to understand what happens when a firewall blocks a port. We will block port 8080 on your machine, test it, then unblock it.

### Steps

1. **Start a simple HTTP server:**

```bash
python3 -m http.server 8080 &
```

2. **Verify it works:**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080
# Should return: 200
```

3. **Create a pf rule to block port 8080:**

   First, save the current rules:
```bash
sudo pfctl -s rules > /tmp/pf_backup.conf
```

   Create a rule file:
```bash
echo "block in proto tcp from any to any port 8080" | sudo tee /tmp/block8080.conf
```

4. **Load the blocking rule:**

```bash
# Enable pf if not already enabled
sudo pfctl -e

# Load the rule
sudo pfctl -f /tmp/block8080.conf
```

5. **Test again:**

```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8080
# Should timeout or fail
```

Note: blocking on localhost may behave differently than blocking on your LAN IP. Try with your actual IP too:
```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://YOUR_IP:8080
```

6. **IMMEDIATELY unblock -- restore the original rules:**

```bash
# Restore original rules (or disable pf if it was not enabled before)
sudo pfctl -f /etc/pf.conf

# Or disable pf entirely if it was disabled before
sudo pfctl -d
```

7. **Verify the server works again:**

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080
# Should return: 200
```

8. **Clean up:**

```bash
# Stop the HTTP server
kill %1
rm /tmp/block8080.conf /tmp/pf_backup.conf
```

### Questions to Answer

- What happened when you tried to curl with the block rule active? Did the connection timeout or get refused?
- Is there a difference between blocking on `localhost` vs. your LAN IP?
- How does this relate to real-world SSH troubleshooting? (Hint: the same thing happens when a cloud Security Group blocks port 22.)

### What You Should Learn

Firewalls are invisible until they block something you need. When a connection times out with no error message, a firewall is often the culprit. In data engineering, this is one of the most common reasons a Spark job cannot connect to a database, or why an Airflow worker cannot reach an API -- a Security Group or firewall rule is silently dropping the packets.

### Important Safety Note

Always keep a backup of your firewall rules and know how to disable pf (`sudo pfctl -d`) before experimenting. Locking yourself out of your own machine with a firewall rule is a rite of passage, but it is best to learn from this warning rather than from experience.
