# Module 02 Exercises: Shell and Keys

Work through these exercises in order. By the end, you'll have key-based authentication working and never type your password again (for SSH, at least).

**Prerequisites**: Complete [Module 01 exercises](../01-ssh-and-remote-access/exercises.md). Remote Login must be enabled.

---

## Exercise 1: Generate and Deploy a Key

You'll create an Ed25519 key pair and set up passwordless SSH to your own machine.

### Step 1: Generate the key pair

```bash
ssh-keygen -t ed25519 -C "learning-networking"
```

When prompted:

- **File location**: Press Enter to accept the default (`~/.ssh/id_ed25519`). If you already have a key there, use a custom path like `~/.ssh/id_ed25519_learning`.
- **Passphrase**: Type a passphrase you'll remember. (For this learning exercise, you can use something simple. For real keys, use something strong.)

### Step 2: Examine what was created

```bash
# List the new files
ls -la ~/.ssh/id_ed25519*

# View your public key
cat ~/.ssh/id_ed25519.pub

# View the private key (just to see the format -- never share this)
head -2 ~/.ssh/id_ed25519
# You'll see: -----BEGIN OPENSSH PRIVATE KEY-----
# followed by base64-encoded data
```

### Step 3: Deploy the key to a server

`ssh-copy-id` copies your public key to a server's `authorized_keys` file. The syntax is:

```bash
ssh-copy-id user@server
```

For example:

```bash
# Deploy to your own machine (for practice)
ssh-copy-id localhost

# Deploy to a remote server by IP
ssh-copy-id root@103.56.158.28

# Deploy to a remote server by hostname
ssh-copy-id deploy@my-data-server.company.com

# Deploy a specific key (if you have multiple)
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@103.56.158.28
```

You'll be asked for the **server's password** one last time. After that, key-based auth takes over and you'll never need the password again for that server.

If `ssh-copy-id` isn't available, you can do it manually:

```bash
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Step 4: Test passwordless login

```bash
ssh localhost
```

If you set a passphrase on your key, you'll be prompted for the passphrase (not your Mac password). If you didn't set a passphrase, you'll log in immediately.

Either way, notice the difference: it says "Enter passphrase for key" instead of "Password:".

```bash
# Verify you're connected
whoami
exit
```

### Step 5: Verify it's using the key

```bash
ssh -v localhost 2>&1 | grep -E "Offering|Accepted|authentication"
```

You should see lines like:

```
debug1: Offering public key: /Users/you/.ssh/id_ed25519 ED25519
debug1: Server accepts key: /Users/you/.ssh/id_ed25519 ED25519
debug1: Authentication succeeded (publickey).
```

### What you learned

- How to generate an SSH key pair
- The difference between the public and private key files
- How to deploy a key to a server
- That key-based auth says "passphrase for key" instead of "Password:"

---

## Exercise 2: SSH Config Aliases

Create shortcuts for SSH connections using the config file.

### Step 1: Create or edit the config file

```bash
# Create the file if it doesn't exist
touch ~/.ssh/config
chmod 600 ~/.ssh/config
```

Open `~/.ssh/config` in your preferred editor and add:

```
# Learning alias for localhost
Host mylocal
    HostName localhost
    User YOUR_USERNAME_HERE
    IdentityFile ~/.ssh/id_ed25519

# Another alias with the IP
Host mylocal-ip
    HostName 127.0.0.1
    User YOUR_USERNAME_HERE
    IdentityFile ~/.ssh/id_ed25519

# Global settings
Host *
    AddKeysToAgent yes
    UseKeychain yes
    ServerAliveInterval 60
```

Replace `YOUR_USERNAME_HERE` with the output of `whoami`.

### Step 2: Test the aliases

```bash
# Instead of: ssh your-username@localhost
ssh mylocal
# Should connect without asking for host or user

exit

# Try the other alias
ssh mylocal-ip

exit
```

### Step 3: Test that the config is being used

```bash
ssh -v mylocal 2>&1 | grep "Reading configuration"
# Should show it reading ~/.ssh/config
```

### Step 4: Experiment with more options

Add this entry to your config:

```
Host mylocal-verbose
    HostName localhost
    User YOUR_USERNAME_HERE
    IdentityFile ~/.ssh/id_ed25519
    LogLevel VERBOSE
```

Now try:

```bash
ssh mylocal-verbose
# You'll see verbose output automatically, without -v flag
exit
```

### What you learned

- How to create SSH host aliases
- How the config file eliminates repetitive typing
- That per-host settings override global `Host *` settings

---

## Exercise 3: ssh-agent Workflow

Learn to use ssh-agent so you type your passphrase once instead of every connection.

### Step 1: Check if ssh-agent is running

```bash
# On macOS, ssh-agent usually runs automatically
echo $SSH_AUTH_SOCK
# If this prints a path, the agent is running

# Check what keys are currently loaded
ssh-add -l
# "The agent has no identities" means no keys are loaded
# Or you'll see keys that are already loaded
```

### Step 2: Add your key to the agent

```bash
# Add the key (macOS with Keychain)
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
# Enter your passphrase when prompted

# Or on any system (without Keychain):
# ssh-add ~/.ssh/id_ed25519
```

### Step 3: Verify the key is loaded

```bash
ssh-add -l
# Should show something like:
# 256 SHA256:xxxxxxxxxx learning-networking (ED25519)
```

### Step 4: Test it

```bash
# SSH should now connect without any passphrase prompt
ssh localhost
# Straight in -- no password, no passphrase
exit
```

### Step 5: Understand the lifecycle

```bash
# Remove all keys from the agent
ssh-add -D
# "All identities removed."

# Verify
ssh-add -l
# "The agent has no identities."

# Now try to SSH -- you'll be prompted for the passphrase again
ssh localhost
# Prompts for passphrase (or uses Keychain if configured)
exit
```

### What you learned

- How to start and interact with ssh-agent
- How to add and remove keys from the agent
- That ssh-agent eliminates repeated passphrase prompts
- How macOS Keychain integration provides persistence across reboots

---

## Exercise 4: Multiple Keys

In the real world, you'll have different keys for different purposes: one for personal servers, one for work, one for GitHub.

### Step 1: Generate a second key

```bash
ssh-keygen -t ed25519 -C "second-key-learning" -f ~/.ssh/id_ed25519_second
# Use a different passphrase than your first key
```

### Step 2: Deploy the second key

```bash
# Add the second public key to authorized_keys
cat ~/.ssh/id_ed25519_second.pub >> ~/.ssh/authorized_keys
```

### Step 3: Configure per-host key selection

Edit `~/.ssh/config` and add:

```
# Uses the first key
Host local-key1
    HostName localhost
    User YOUR_USERNAME_HERE
    IdentityFile ~/.ssh/id_ed25519

# Uses the second key
Host local-key2
    HostName localhost
    User YOUR_USERNAME_HERE
    IdentityFile ~/.ssh/id_ed25519_second
```

### Step 4: Test each alias

```bash
# Connect with the first key
ssh -v local-key1 2>&1 | grep "Offering"
# Should show: Offering public key: ~/.ssh/id_ed25519

exit

# Connect with the second key
ssh -v local-key2 2>&1 | grep "Offering"
# Should show: Offering public key: ~/.ssh/id_ed25519_second

exit
```

### Step 5: See what happens with the wrong key

```bash
# Remove the second key from authorized_keys
# First, view authorized_keys and identify the second key
cat ~/.ssh/authorized_keys

# Remove it (only do this if you have more than one line)
# Find the line containing "second-key-learning" and remove it manually with a text editor
```

Now test:

```bash
ssh local-key2
# Should fall back to password auth or fail with "Permission denied"
```

### Step 6: Clean up

```bash
# Re-add the second key if you removed it
cat ~/.ssh/id_ed25519_second.pub >> ~/.ssh/authorized_keys

# Add both keys to ssh-agent
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_second

# Verify both are loaded
ssh-add -l
```

### What you learned

- How to manage multiple SSH key pairs
- How `IdentityFile` in the config controls which key is used per host
- Why having separate keys for separate purposes (personal, work, CI/CD) is a good practice
- How SSH falls back when the specified key isn't authorized

---

## Bonus: Inspect authorized_keys

Take a closer look at what's in your `authorized_keys` file:

```bash
cat ~/.ssh/authorized_keys
```

Each line is a complete public key entry:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGrKx... learning-networking
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPqRx... second-key-learning
```

Format: `key-type base64-encoded-key comment`

The comment (like `learning-networking`) has no security function -- it's just a label to help you identify which key is which. This is why the `-C` flag in `ssh-keygen` is useful: it makes keys identifiable.

```bash
# Count how many keys are authorized
wc -l ~/.ssh/authorized_keys
```

---

[Back to Module 02 README](README.md) | [Module 02 Cheatsheet](cheatsheet.md)

[Back to main guide](../README.md)
