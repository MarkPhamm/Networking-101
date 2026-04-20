# Mac Setup Guide

One-time setup to prepare your Mac for the exercises in this guide. Run through this before starting Module 01.

---

## 1. Enable Remote Login (SSH Server)

Several exercises require SSHing into your own machine. macOS has a built-in SSH server, but it's disabled by default.

### macOS Ventura and later (System Settings)

1. Open **System Settings**
2. Go to **General > Sharing**
3. Toggle **Remote Login** to **On**
4. Under "Allow access for," choose **All users** (for learning purposes; tighten this later)
5. Note the connection command shown, something like: `ssh your-username@your-Macs-name.local`

### macOS Monterey and earlier (System Preferences)

1. Open **System Preferences**
2. Go to **Sharing**
3. Check the box next to **Remote Login**
4. Set "Allow access for" to **All users**

### Verify it works

```bash
# Check that sshd is running
sudo launchctl list | grep ssh

# You should see something like:
# -    0    com.openssh.sshd

# Test the connection
ssh localhost
# Type 'yes' at the host key prompt, enter your password, then type 'exit'
```

If `ssh localhost` hangs or says "Connection refused," Remote Login is not enabled. Go back and check.

---

## 2. Verify Built-in Tools

macOS ships with most of the networking tools we need. Open Terminal and verify each one exists by checking its version or help output.

```bash
# Core connectivity tools
ping -c 1 127.0.0.1          # Send one ping to yourself
traceroute --version 2>&1 | head -1  # Check traceroute exists

# DNS tools
dig -v 2>&1 | head -1        # DNS lookup utility
nslookup -version 2>&1 | head -1  # Older DNS lookup tool
host localhost                # Simple DNS lookup

# Network inspection
ifconfig lo0                  # Show loopback interface config
netstat -an | head -5         # Show active connections
lsof -v 2>&1 | head -1       # List open files/sockets

# Utility tools
nc -h 2>&1 | head -1         # Netcat
ssh -V                        # SSH client version
ssh-keygen -h 2>&1 | head -3 # Key generation tool
curl --version | head -1      # HTTP client

# ARP and packet capture
arp -a | head -3              # Show ARP table
which tcpdump                 # Should print /usr/sbin/tcpdump
```

All of these should produce output without "command not found" errors. If any are missing, you may need to install Xcode Command Line Tools:

```bash
xcode-select --install
```

---

## 3. Install Wireshark

Wireshark is a GUI-based packet analyzer. It lets you visually inspect network traffic at every layer. We use it in later modules.

```bash
# Install via Homebrew
brew install --cask wireshark
```

If you don't have Homebrew installed:

```bash
# Install Homebrew first
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install Wireshark
brew install --cask wireshark
```

After installation, open Wireshark once from Applications to complete its setup. It may ask for permission to install a helper tool for capturing packets -- allow it.

### Verify Wireshark

```bash
# Check that the command-line capture tool is available
which tshark
# Should output something like /usr/local/bin/tshark or /opt/homebrew/bin/tshark
```

---

## 4. sudo Considerations

Some networking tools require root privileges to function. On macOS, you use `sudo` to run commands as root.

### tcpdump

`tcpdump` captures raw network packets, which requires elevated privileges:

```bash
# This will fail without sudo
tcpdump -i en0

# This works
sudo tcpdump -i en0 -c 5
# Captures 5 packets on your primary network interface
# Press Ctrl+C to stop early
```

### pfctl (Packet Filter)

macOS uses `pf` (Packet Filter) as its built-in firewall. Managing firewall rules requires sudo:

```bash
# Check if pf is enabled
sudo pfctl -s info | head -5

# View current rules
sudo pfctl -s rules
```

### Best practices with sudo

- **Only use sudo when the exercise explicitly says to.** Don't form a habit of running everything as root.
- **Read the command before running it with sudo.** Understand what it does.
- `tcpdump` will capture ALL traffic on an interface, including potentially sensitive data. Only run it on your own machine for learning.
- If a command asks for your password after `sudo`, it's your Mac login password.

---

## 5. Optional: Install nmap

`nmap` is a powerful network scanner. It's useful for discovering what hosts and ports are available on a network.

```bash
brew install nmap
```

### Verify nmap

```bash
nmap --version
# Should show something like "Nmap version 7.94"
```

### Important note about nmap

**Only scan networks you own or have explicit permission to scan.** Scanning other people's networks without permission is, at best, rude and, at worst, illegal. For this guide, you'll only scan your own machine (`localhost` / `127.0.0.1`) and your local network.

---

## 6. Summary Checklist

Run this to confirm everything is ready:

```bash
echo "=== Mac Networking Setup Check ==="
echo ""

echo "1. Remote Login (SSH server):"
sudo launchctl list 2>/dev/null | grep -q ssh && echo "   PASS: sshd is running" || echo "   FAIL: sshd not found - enable Remote Login in System Settings"
echo ""

echo "2. Built-in tools:"
for tool in ping traceroute dig nslookup host ifconfig netstat lsof nc ssh ssh-keygen curl arp tcpdump; do
    which $tool > /dev/null 2>&1 && echo "   PASS: $tool" || echo "   FAIL: $tool not found"
done
echo ""

echo "3. Wireshark:"
which tshark > /dev/null 2>&1 && echo "   PASS: tshark (Wireshark CLI) found" || echo "   MISSING: Install with 'brew install --cask wireshark'"
echo ""

echo "4. nmap (optional):"
which nmap > /dev/null 2>&1 && echo "   PASS: nmap found" || echo "   MISSING: Install with 'brew install nmap' (optional)"
echo ""

echo "=== Setup check complete ==="
```

If everything shows PASS (with nmap being optional), you're ready for Module 01.

---

[Back to main guide](../README.md)
