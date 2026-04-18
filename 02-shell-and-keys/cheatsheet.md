# Module 02 Cheatsheet: Shell and Keys

Quick reference card for SSH keys, ssh-agent, and SSH config.

---

## ssh-keygen Commands

```bash
# Generate an Ed25519 key (recommended)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Generate an Ed25519 key with a custom filename
ssh-keygen -t ed25519 -C "work-key" -f ~/.ssh/id_ed25519_work

# Generate an RSA key (when Ed25519 isn't supported)
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Change the passphrase on an existing key
ssh-keygen -p -f ~/.ssh/id_ed25519

# View the fingerprint of a key
ssh-keygen -lf ~/.ssh/id_ed25519.pub

# View the fingerprint in visual/randomart format
ssh-keygen -lvf ~/.ssh/id_ed25519.pub

# Remove a host from known_hosts
ssh-keygen -R hostname
ssh-keygen -R 192.168.1.50
ssh-keygen -R "[hostname]:2222"    # Non-standard port
```

### Key flags

| Flag | Purpose | Example |
|------|---------|---------|
| `-t` | Key type | `-t ed25519` or `-t rsa` |
| `-b` | Key size in bits (RSA only) | `-b 4096` |
| `-C` | Comment/label | `-C "mark@work"` |
| `-f` | Output filename | `-f ~/.ssh/id_ed25519_work` |
| `-p` | Change passphrase | `-p -f ~/.ssh/id_ed25519` |
| `-l` | Show fingerprint | `-lf ~/.ssh/id_ed25519.pub` |
| `-R` | Remove host from known_hosts | `-R hostname` |

---

## ssh-agent Commands

```bash
# Start ssh-agent (if not already running)
eval "$(ssh-agent -s)"

# Add a key to the agent
ssh-add ~/.ssh/id_ed25519

# Add a key and store passphrase in macOS Keychain
ssh-add --apple-use-keychain ~/.ssh/id_ed25519

# List loaded keys
ssh-add -l

# List loaded keys with full public key
ssh-add -L

# Remove a specific key
ssh-add -d ~/.ssh/id_ed25519

# Remove ALL keys from agent
ssh-add -D

# Check if agent is running
echo $SSH_AUTH_SOCK
```

---

## SSH Config File Syntax

**Location**: `~/.ssh/config`

### Basic structure

```
# Comment
Host <alias>
    HostName <hostname or IP>
    User <username>
    Port <port>
    IdentityFile <path to private key>
```

### Full example

```
# Personal server
Host personal
    HostName 203.0.113.50
    User mark
    IdentityFile ~/.ssh/id_ed25519

# Work jump host
Host bastion
    HostName bastion.company.com
    User mpham
    Port 2222
    IdentityFile ~/.ssh/id_ed25519_work

# Internal server accessed through bastion
Host internal
    HostName 10.0.1.100
    User deploy
    ProxyJump bastion

# GitHub (useful if you have multiple accounts)
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519

# Global defaults (apply to all hosts)
Host *
    AddKeysToAgent yes
    UseKeychain yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
    IdentityFile ~/.ssh/id_ed25519
```

### Common config options

| Option | Purpose | Example Value |
|--------|---------|---------------|
| `HostName` | Real hostname or IP | `192.168.1.50` |
| `User` | Remote username | `mark` |
| `Port` | Remote SSH port | `2222` |
| `IdentityFile` | Private key path | `~/.ssh/id_ed25519_work` |
| `ProxyJump` | Jump host alias | `bastion` |
| `ForwardAgent` | Forward agent to remote | `yes` |
| `AddKeysToAgent` | Auto-add keys to agent | `yes` |
| `UseKeychain` | Use macOS Keychain | `yes` |
| `ServerAliveInterval` | Keep-alive interval (sec) | `60` |
| `ServerAliveCountMax` | Max missed keep-alives | `3` |
| `LogLevel` | Verbosity | `VERBOSE` or `QUIET` |
| `StrictHostKeyChecking` | Host key policy | `ask` (default), `yes`, `no` |

---

## Deploying Keys to a Server

```bash
# Easiest method
ssh-copy-id user@remote-server

# Specify which key to copy
ssh-copy-id -i ~/.ssh/id_ed25519_work.pub user@remote-server

# Manual method (if ssh-copy-id isn't available)
cat ~/.ssh/id_ed25519.pub | ssh user@server "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

---

## File Permission Requirements

SSH is strict about file permissions. If they're too open, SSH refuses to use the files.

| Path | Required Permission | Command |
|------|-------------------|---------|
| `~/.ssh/` (directory) | `700` (drwx------) | `chmod 700 ~/.ssh` |
| `~/.ssh/id_ed25519` (private key) | `600` (-rw-------) | `chmod 600 ~/.ssh/id_ed25519` |
| `~/.ssh/id_ed25519.pub` (public key) | `644` (-rw-r--r--) | `chmod 644 ~/.ssh/id_ed25519.pub` |
| `~/.ssh/authorized_keys` | `600` (-rw-------) | `chmod 600 ~/.ssh/authorized_keys` |
| `~/.ssh/config` | `600` (-rw-------) | `chmod 600 ~/.ssh/config` |
| `~/.ssh/known_hosts` | `644` (-rw-r--r--) | `chmod 644 ~/.ssh/known_hosts` |

### Fix all permissions at once

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_* ~/.ssh/authorized_keys ~/.ssh/config 2>/dev/null
chmod 644 ~/.ssh/*.pub ~/.ssh/known_hosts 2>/dev/null
```

---

## Key-Based Auth vs Password Auth

| | Password | Key-Based |
|--|---------|-----------|
| What you type | Mac/server password | Passphrase (or nothing with agent) |
| Prompt looks like | `Password:` | `Enter passphrase for key '/path/to/key':` |
| Sent over network | Password (encrypted) | Never -- challenge-response only |
| Can be brute-forced | Yes | Practically no |
| Can use agent | No | Yes |
| `-v` output shows | `Next authentication method: password` | `Offering public key: /path/to/key` |

---

## Quick Troubleshooting

| Problem | Command to Debug | Likely Fix |
|---------|-----------------|-----------|
| Key auth not working | `ssh -v user@host` | Check authorized_keys and permissions |
| Agent not running | `echo $SSH_AUTH_SOCK` | `eval "$(ssh-agent -s)"` |
| No keys in agent | `ssh-add -l` | `ssh-add ~/.ssh/id_ed25519` |
| Permissions too open | `ls -la ~/.ssh/` | Run chmod commands above |
| Wrong key being used | `ssh -v user@host \| grep Offering` | Set `IdentityFile` in config |
| Config not loading | `ssh -v alias 2>&1 \| grep config` | Check `~/.ssh/config` permissions (600) |

---

[Back to Module 02 README](README.md) | [Module 02 Exercises](exercises.md)

[Back to main guide](../README.md)
