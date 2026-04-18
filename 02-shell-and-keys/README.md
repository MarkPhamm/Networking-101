# Module 02: Shell and Keys

## What You'll Learn

- What a shell is and how SSH gives you a remote one
- Symmetric vs asymmetric cryptography (the concepts, not the math)
- How public/private key pairs work
- Why Ed25519 keys are preferred over RSA
- How to generate and deploy SSH keys
- How `authorized_keys` lets the server verify your identity
- How ssh-agent saves you from retyping passphrases
- How to use `~/.ssh/config` to create host aliases

---

## What Is a Shell?

A **shell** is the program that takes what you type and turns it into actions on the computer. When you open Terminal on your Mac, you're running a shell.

Common shells:

- **zsh** -- the default shell on modern macOS
- **bash** -- the default on most Linux systems and older Macs
- **sh** -- the original Bourne shell, still available everywhere

You can check which shell you're using:

```bash
echo $SHELL
# /bin/zsh on modern Mac
```

### How SSH gives you a remote shell

When you SSH into a server, the SSH daemon (`sshd`) starts a shell process running as your user on that machine. Your keystrokes travel over the encrypted SSH channel to that remote shell, the remote shell executes them, and the output travels back to your terminal.

```
┌─────────────┐     encrypted tunnel     ┌──────────────┐
│ Your Mac    │ =========================│ Remote Server│
│             │                          │              │
│ Terminal    │ ──> keystrokes ────────> │ zsh/bash     │
│             │ <── output    <────────  │ (as "mark")  │
└─────────────┘                          └──────────────┘
```

**Key point**: The shell on the remote machine has its own environment. It has different environment variables, a different `$HOME`, different installed software, and potentially a different operating system. When you type `ls`, it runs `/bin/ls` on the *remote* machine, not yours.

---

## Cryptography Concepts (No Math Required)

To understand SSH keys, you need two concepts: symmetric and asymmetric encryption.

### Symmetric encryption: One key for everything

Imagine a lockbox with a single key. If I lock something in it, the same key unlocks it. If you want to exchange secrets with me, we both need a copy of the same key.

**Problem**: How do I get the key to you securely in the first place? If I send it over the network, someone could intercept it.

This is what SSH uses for the actual data transfer *after* the connection is established -- it's fast and efficient. But it can't solve the initial key exchange problem alone.

### Asymmetric encryption: Two keys, one pair

Now imagine a different system: two keys that are mathematically linked.

- **Public key**: A lock that anyone can use to lock a box shut
- **Private key**: The only key that can open boxes locked by that specific public key

I can send you the lock (public key) openly -- even if someone intercepts it, all they can do is lock more boxes. Only I have the key (private key) that opens them.

This is how SSH key authentication works. And it's how the initial connection is secured before switching to faster symmetric encryption.

---

## Public/Private Key Pairs

### The lock-and-key analogy

Think of it this way:

- Your **public key** is a special padlock. You can make unlimited copies and give them to anyone. They're useless without the matching key.
- Your **private key** is the one key that opens all copies of your padlock. You never give this to anyone. Ever.

When you want to SSH into a server:

1. You give the server a copy of your padlock (public key) ahead of time
2. The server puts a challenge in a box and locks it with your padlock
3. If you can open the box (using your private key), you are who you claim to be
4. Authentication complete -- no password ever crossed the network

### In actual SSH terms

The real process uses a mathematical "challenge-response" protocol:

1. Your public key is stored on the server in `~/.ssh/authorized_keys`
2. When you connect, the server generates a random challenge
3. The server encrypts the challenge with your public key
4. Your SSH client decrypts it with your private key and sends a response
5. The server verifies the response -- if correct, you're authenticated

The private key never leaves your machine. The password never crosses the network. There's nothing to intercept.

### Data engineering analogy

Key-based authentication is like using a **GCP service account JSON key** or an **AWS IAM role** instead of a username/password in your ETL pipelines.

Think about it:

- A service account JSON is a private key file stored on the machine running the pipeline
- GCP has the corresponding public component registered
- When your pipeline authenticates, it proves identity using the key -- no password is typed or sent

SSH keys work exactly the same way. And just like you'd never check a service account JSON into git, you never share your SSH private key.

---

## Key Types: RSA vs Ed25519

When generating SSH keys, you choose an algorithm. The two you'll encounter:

### RSA

- The classic. Has been around since 1977.
- Default key size is 3072 bits (used to be 2048; 4096 is also common).
- Larger keys = slower operations, but more secure.
- Widely compatible -- works with everything, including ancient systems.
- Files: `~/.ssh/id_rsa` (private) and `~/.ssh/id_rsa.pub` (public)

### Ed25519

- Modern algorithm based on elliptic curves (specifically Curve25519).
- Fixed 256-bit keys that are as secure as 3072-bit RSA keys.
- Faster to generate, faster to authenticate.
- Smaller key size (more convenient).
- Supported by any OpenSSH version from 2014 onward.
- Files: `~/.ssh/id_ed25519` (private) and `~/.ssh/id_ed25519.pub` (public)

### Which should you use?

**Ed25519**, unless you need to connect to a very old system that doesn't support it. It's faster, more secure per bit, and produces shorter keys.

```bash
# Ed25519 public key (short)
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGrKx... user@host

# RSA public key (long)
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7... (much longer) user@host
```

---

## The ssh-keygen Workflow

### Generating a key pair

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

Flags:

- `-t ed25519` -- Use the Ed25519 algorithm
- `-C "comment"` -- Attach a comment (usually your email; helps identify the key)

You'll be prompted:

```
Generating public/private ed25519 key pair.
Enter file in which to save the key (/Users/you/.ssh/id_ed25519):
```

Press Enter for the default location, or specify a custom path.

```
Enter passphrase (empty for no passphrase):
```

**Always set a passphrase.** If someone steals your private key file, the passphrase is the last line of defense. It's like encrypting a service account JSON at rest. We'll use ssh-agent to avoid typing it constantly.

```
Your identification has been saved in /Users/you/.ssh/id_ed25519
Your public key has been saved in /Users/you/.ssh/id_ed25519.pub
```

### What got created

```
~/.ssh/
  id_ed25519       # Private key -- NEVER share this
  id_ed25519.pub   # Public key -- safe to share
```

### Viewing your public key

```bash
cat ~/.ssh/id_ed25519.pub
```

Output looks like:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGrKx... your_email@example.com
```

This is what you give to servers, put in GitHub, etc.

---

## authorized_keys: How the Server Checks Your Key

On the server, your public key must be in:

```
~/.ssh/authorized_keys
```

This file contains one public key per line. When you connect, sshd reads this file and checks if any of the keys match what the client presents.

### Deploying your key manually

```bash
# Copy your public key to the server's authorized_keys
# Method 1: Using ssh-copy-id (easiest)
ssh-copy-id user@remote-server

# Method 2: Manual (if ssh-copy-id isn't available)
cat ~/.ssh/id_ed25519.pub | ssh user@remote-server "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# Method 3: Copy-paste
# 1. Copy your public key
cat ~/.ssh/id_ed25519.pub
# 2. SSH to the server with your password
ssh user@remote-server
# 3. Append the key to authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1..." >> ~/.ssh/authorized_keys
```

### File permissions matter

SSH is strict about permissions. If your key files or directories have overly permissive permissions, SSH will refuse to use them:

```
~/.ssh/               --> 700 (drwx------)
~/.ssh/id_ed25519     --> 600 (-rw-------)
~/.ssh/id_ed25519.pub --> 644 (-rw-r--r--)
~/.ssh/authorized_keys --> 600 (-rw-------)
~/.ssh/config         --> 600 (-rw-------)
~/.ssh/known_hosts    --> 644 (-rw-r--r--)
```

If permissions are wrong:

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/authorized_keys
```

---

## ssh-agent: Managing Passphrases

If you set a passphrase on your key (and you should), you'd normally have to type it every time you SSH somewhere. That gets old fast. `ssh-agent` solves this.

`ssh-agent` is a background process that holds your decrypted private keys in memory. When SSH needs a key, it asks the agent instead of prompting you.

### macOS Keychain integration

On macOS, ssh-agent integrates with the system Keychain. You can store your passphrase in Keychain so you don't even have to type it after a reboot.

```bash
# Add your key to the agent and store passphrase in Keychain
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

You'll be prompted for the passphrase once. After that, the Keychain remembers it.

### Standard ssh-agent workflow (all platforms)

```bash
# Start the agent (if not already running)
eval "$(ssh-agent -s)"
# Output: Agent pid 12345

# Add your key to the agent
ssh-add ~/.ssh/id_ed25519
# Enter passphrase once

# Verify the key is loaded
ssh-add -l
# Output: 256 SHA256:xxxxx your_email@example.com (ED25519)

# Now SSH without typing the passphrase
ssh user@remote-server
```

### Making it persistent on macOS

Add this to `~/.ssh/config` so macOS automatically uses the Keychain:

```
Host *
    AddKeysToAgent yes
    UseKeychain yes
    IdentityFile ~/.ssh/id_ed25519
```

With this config, the first time you SSH after a reboot, you'll be prompted for the passphrase. It gets stored in Keychain and you won't be asked again until you change the password.

---

## SSH Config File (~/.ssh/config)

The SSH config file lets you create **aliases** for hosts and set per-host options. Instead of typing:

```bash
ssh -p 2222 -i ~/.ssh/work_key mark@very-long-hostname.internal.company.com
```

You can type:

```bash
ssh work
```

### Creating the config file

```bash
# Create if it doesn't exist
touch ~/.ssh/config
chmod 600 ~/.ssh/config
```

### Syntax

```
Host <alias>
    HostName <actual hostname or IP>
    User <username>
    Port <port number>
    IdentityFile <path to private key>
```

### Example config

```
# Personal server
Host myserver
    HostName 203.0.113.50
    User mark
    IdentityFile ~/.ssh/id_ed25519

# Work bastion host
Host bastion
    HostName bastion.company.com
    User mpham
    Port 2222
    IdentityFile ~/.ssh/work_key

# Production database server (through bastion)
Host prod-db
    HostName 10.0.1.50
    User deploy
    ProxyJump bastion

# Apply to all hosts
Host *
    AddKeysToAgent yes
    UseKeychain yes
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

### What `ServerAliveInterval` does

Sends a keep-alive packet every 60 seconds to prevent idle connections from being dropped by firewalls or NAT devices. `ServerAliveCountMax 3` means SSH gives up after 3 missed keep-alives (3 minutes of no response).

### Config file options reference

| Option | What It Does | Example |
|--------|-------------|---------|
| `HostName` | Actual hostname or IP | `203.0.113.50` |
| `User` | Remote username | `mark` |
| `Port` | Remote port | `2222` |
| `IdentityFile` | Private key to use | `~/.ssh/work_key` |
| `ProxyJump` | Jump through another host | `bastion` |
| `ForwardAgent` | Forward ssh-agent to remote | `yes` |
| `ServerAliveInterval` | Keep-alive interval (seconds) | `60` |
| `AddKeysToAgent` | Auto-add keys to agent | `yes` |
| `UseKeychain` | Use macOS Keychain | `yes` |

---

## Key Takeaways

1. **A shell is just a command interpreter** -- SSH gives you a remote one over an encrypted channel
2. **Asymmetric crypto uses two keys** -- public (share freely) and private (guard with your life)
3. **Use Ed25519 keys** -- they're faster, shorter, and more secure than RSA
4. **Always set a passphrase** on your private key -- use ssh-agent so you don't have to type it every time
5. **authorized_keys is the gatekeeper** -- your public key must be in this file on the server
6. **File permissions matter** -- SSH refuses to use keys with loose permissions
7. **~/.ssh/config is your friend** -- create aliases to save typing and reduce errors
8. **SSH keys are like service account credentials** -- they prove identity without sending secrets over the network

---

Next: [Module 03 - IP Addressing and DNS](../03-ip-addressing-and-dns/) -- Learn how machines find each other.

[Back to main guide](../README.md)
