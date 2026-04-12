# Module 01 Cheatsheet: SSH and Remote Access

Quick reference card. Print this or keep it in a tab.

---

## Basic Commands

```bash
# Connect to a remote host
ssh user@hostname
ssh user@192.168.1.50

# Connect on a non-standard port
ssh -p 2222 user@hostname

# Connect with verbose output (debugging)
ssh -v user@hostname
ssh -vv user@hostname       # More verbose
ssh -vvv user@hostname      # Maximum verbosity

# Connect with a specific private key
ssh -i ~/.ssh/my_key user@hostname

# Connect with a timeout
ssh -o ConnectTimeout=5 user@hostname

# Run a single command remotely (no interactive shell)
ssh user@hostname "command"
ssh user@hostname "ls -la /tmp"
ssh user@hostname "df -h"
```

---

## Config File Locations

| File | Purpose |
| ------ | --------- |
| `~/.ssh/known_hosts` | Stored host keys for servers you've connected to |
| `~/.ssh/config` | Your personal SSH client config (host aliases, key settings) |
| `~/.ssh/id_ed25519` | Your private key (default Ed25519) |
| `~/.ssh/id_ed25519.pub` | Your public key (default Ed25519) |
| `~/.ssh/id_rsa` | Your private key (default RSA) |
| `~/.ssh/id_rsa.pub` | Your public key (default RSA) |
| `/etc/ssh/ssh_config` | System-wide SSH client config |
| `/etc/ssh/sshd_config` | SSH server (daemon) config |

---

## Error Messages Decoded

| Error | Step That Failed | Likely Cause | First Thing to Try |
| ------- | ----------------- | ------------- | ------------------- |
| `Connection refused` | TCP connection | sshd not running or port blocked (REJECT) | Check if sshd is running on the server |
| `Operation timed out` | TCP connection | Wrong IP, firewall DROP, or host unreachable | Verify the IP with `ping`; check your network |
| `Permission denied (publickey,password)` | Authentication | Wrong user, wrong password, or key not authorized | Verify username and credentials |
| `Could not resolve hostname` | DNS resolution | Typo in hostname or DNS issue | Try the IP address directly |
| `REMOTE HOST IDENTIFICATION HAS CHANGED` | Host key verification | Server was rebuilt or IP reassigned | `ssh-keygen -R hostname` to clear old key |
| `No route to host` | Network routing | Network unreachable or misconfigured routing | Check if you're on the right network |

---

## Key Flags and Options

| Flag | What It Does | Example |
| ------ | ------------- | --------- |
| `-p PORT` | Connect to a specific port | `ssh -p 2222 user@host` |
| `-v` | Verbose output (debugging) | `ssh -v user@host` |
| `-i KEY` | Use a specific private key | `ssh -i ~/.ssh/work_key user@host` |
| `-o OPTION=VALUE` | Set an option | `ssh -o ConnectTimeout=5 user@host` |
| `-N` | No remote command (port forwarding only) | `ssh -N -L 8080:localhost:80 user@host` |
| `-L` | Local port forwarding | `ssh -L 5432:db-host:5432 user@bastion` |
| `-J` | Jump through a bastion/jump host | `ssh -J user@bastion user@internal` |
| `-A` | Forward SSH agent | `ssh -A user@host` |

---

## Managing known_hosts

```bash
# View all known hosts
cat ~/.ssh/known_hosts

# Remove a specific host entry (after server rebuild)
ssh-keygen -R hostname
ssh-keygen -R 192.168.1.50

# Remove a host on a non-standard port
ssh-keygen -R "[hostname]:2222"
```

---

## Checking If SSH Is Running

```bash
# On macOS (your machine)
sudo launchctl list | grep ssh

# On Linux (remote server)
systemctl status sshd
# or
sudo service ssh status
```

---

## The Connection Sequence (For Debugging)

When you run `ssh user@host`, these steps happen in order. If the connection fails, it fails at one of these steps:

```text
1. DNS Resolution        --> "Could not resolve hostname"
2. TCP Connection (SYN)  --> "Connection timed out" or "Connection refused"
3. Protocol Exchange     --> (rare failures)
4. Key Exchange          --> (rare failures)
5. Host Key Verification --> "REMOTE HOST IDENTIFICATION HAS CHANGED"
6. User Authentication   --> "Permission denied"
7. Shell Session         --> Success!
```

Use `ssh -v` to see exactly which step fails.

---

[Back to Module 01 README](README.md) | [Module 01 Exercises](exercises.md)

[Back to main guide](../README.md)
