# Module 01 Exercises: SSH and Remote Access

Work through these exercises in order. Each one builds on the previous.

**Prerequisites**: Complete the [Mac Setup Guide](../appendix/mac-setup.md) first. Remote Login must be enabled.

---

## Exercise 1: SSH to Yourself

The simplest possible SSH connection. You're going to SSH from your Mac into your own Mac.

### Steps

1. Open Terminal.

2. SSH to localhost:

   ```bash
   ssh localhost
   ```

3. You'll see the host key verification prompt:

   ```text
   The authenticity of host 'localhost (127.0.0.1)' can't be established.
   ED25519 key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxx.
   Are you sure you want to continue connecting (yes/no/[fingerprint])?
   ```

   Type `yes` and press Enter.

4. Enter your Mac login password when prompted.

5. You're now SSHed into your own machine. Confirm:

   ```bash
   whoami
   # Should print your username

   hostname
   # Should print your Mac's hostname

   pwd
   # Should print your home directory
   ```

6. Exit the SSH session:

   ```bash
   exit
   ```

   You'll see "Connection to localhost closed."

7. Now connect using an explicit username and the loopback IP:

   ```bash
   ssh $(whoami)@127.0.0.1
   ```

   This time you should NOT see the host key prompt (because you already accepted it for localhost/127.0.0.1 -- but you might, since `localhost` and `127.0.0.1` can be stored as separate entries). Enter your password and verify you're connected, then `exit`.

### What you learned

- How to initiate an SSH connection
- What the host key verification prompt looks like
- That `localhost` and `127.0.0.1` both point to your own machine
- How to verify you're connected and how to disconnect

### Check your work

```bash
# You should now have entries in known_hosts
cat ~/.ssh/known_hosts | grep -E "localhost|127.0.0.1"
```

---

## Exercise 2: Intentional Failures

Understanding error messages is more useful than understanding successful connections. Let's deliberately cause every common failure and learn to recognize them.

### 2a: Permission Denied (Wrong Username)

```bash
ssh nonexistent_user_12345@localhost
```

**Expected output**:

```
nonexistent_user_12345@localhost: Permission denied (publickey,password,keyboard-interactive).
```

**What happened**: SSH connected to sshd successfully, but there's no user called `nonexistent_user_12345` on your Mac, so authentication failed.

### 2b: Connection Refused (Wrong Port)

```bash
ssh localhost -p 9999
```

**Expected output**:

```text
ssh: connect to host localhost port 9999: Connection refused
```

**What happened**: Your Mac reached localhost, but nothing is listening on port 9999. The operating system sent back a TCP RST (reset) packet, meaning "nobody's home at this port."

### 2c: Connection Timed Out (Unreachable Host)

```bash
ssh 192.0.2.1
```

**Note**: `192.0.2.0/24` is a "documentation" IP range that's guaranteed to not be routed anywhere. This means packets sent to it simply disappear.

**Expected output** (after 60+ seconds):

```text
ssh: connect to host 192.0.2.1 port 22: Operation timed out
```

**What happened**: Your Mac sent SYN packets but never got a response. After waiting (the default timeout), SSH gave up. This is what happens when you have the wrong IP or a firewall is silently dropping your packets.

**Tip**: You can set a shorter timeout to avoid waiting so long:

```bash
ssh -o ConnectTimeout=5 192.0.2.1
# Times out after 5 seconds instead of ~75
```

### 2d: Hostname Resolution Failure

```bash
ssh totally.fake.hostname.invalid
```

**Expected output**:

```text
ssh: Could not resolve hostname totally.fake.hostname.invalid: nodename nor servname provided, or not known
```

**What happened**: Before even trying to connect, SSH asked DNS to resolve the hostname into an IP address. DNS said "never heard of it." No TCP connection was ever attempted.

### Write it down

Create a personal reference by filling in this table:

| Error Message | What Step Failed | Most Likely Cause |
| --------------- | ------------------ | ------------------- |
| Connection refused | Step 2: TCP Connection | Wrong port (or sshd not running) |
| Operation timed out | Step 2: TCP Connection | Unreachable host (wrong IP, firewall DROP, different network) |
| Permission denied | Step 6: User Authentication | Unauthenticated user (wrong password, wrong username, missing key) |
| Could not resolve hostname | Step 1: DNS Resolution | DNS cannot find the corresponding IP address |

---

## Exercise 3: Inspect SSH Files

Peek under the hood at the configuration files that control SSH behavior.

### 3a: Your known_hosts file

```bash
cat ~/.ssh/known_hosts
```

**Questions to answer**:

- How many entries are there?
- Can you identify the hostname/IP, key type, and public key for each entry?
- Do you see entries from Exercise 1?

### 3b: The SSH server configuration

```bash
# View the server config (read-only -- don't change anything)
cat /etc/ssh/sshd_config
```

**Things to look for**:

- What port is sshd configured to listen on? (Look for `Port`)
- Is password authentication enabled? (Look for `PasswordAuthentication`)
- Is root login allowed? (Look for `PermitRootLogin`)
- What authentication methods are enabled?

**Note**: Lines starting with `#` are comments (disabled). On macOS, most settings are commented out, meaning the defaults are in use.

```bash
# Show only non-comment, non-empty lines
grep -v '^#' /etc/ssh/sshd_config | grep -v '^$'
```

### 3c: The SSH client configuration

```bash
# View the client config
cat /etc/ssh/ssh_config
```

This is the system-wide client configuration. Your personal config would be at `~/.ssh/config` (which may not exist yet -- we'll create it in Module 02).

### What you learned

- Where SSH stores its data and configuration
- How to read the server and client config files
- That config files control authentication methods, ports, and security settings

---

## Exercise 4: Verbose Mode

SSH's `-v` flag shows you every step of the connection process. This is your most powerful debugging tool.

### Steps

1. Connect with verbose output:

   ```bash
   ssh -v localhost
   ```

2. You'll see a wall of text. Look for these key lines (your output will differ in details):

   **Reading configuration**:

   ```bash
   debug1: Reading configuration data /etc/ssh/ssh_config
   ```

   **DNS resolution / connection**:

   ```text
   debug1: Connecting to localhost [127.0.0.1] port 22.
   debug1: Connection established.
   ```

   **Protocol exchange**:

   ```text
   debug1: Remote protocol version 2.0, remote software version OpenSSH_9.6
   ```

   **Key exchange**:

   ```text
   debug1: SSH2_MSG_KEXINIT sent
   debug1: SSH2_MSG_KEXINIT received
   debug1: kex: algorithm: sntrup761x25519-sha512@openssh.com
   ```

   **Host key verification**:

   ```text
   debug1: Host 'localhost' is known and matches the ED25519 host key.
   debug1: Found key in /Users/yourname/.ssh/known_hosts:1
   ```

   **Authentication**:

   ```text
   debug1: Authentications that can continue: publickey,password,keyboard-interactive
   debug1: Next authentication method: password
   ```

3. Enter your password, then type `exit`.

4. Now try verbose mode on a failing connection:

   ```bash
   ssh -v -o ConnectTimeout=5 192.0.2.1
   ```

   Notice how the output stops at the connection step -- it never gets to key exchange or authentication because it can't even reach the server.

### Advanced: Even more verbosity

```bash
# -vv gives more detail
ssh -vv localhost

# -vvv gives maximum detail (probably more than you need right now)
ssh -vvv localhost
```

### What you learned

- How to use `-v` to debug SSH connections
- How to identify which step of the connection process is failing
- That SSH tries multiple authentication methods in sequence
- Where SSH reads its configuration from

---

## Bonus: Document Your Network Environment

This isn't an SSH exercise, but it sets you up for later modules. Run these commands and save the output:

```bash
echo "=== My Network Info ==="
echo ""
echo "Hostname: $(hostname)"
echo "Username: $(whoami)"
echo ""
echo "IP Addresses:"
ifconfig | grep "inet " | grep -v 127.0.0.1
echo ""
echo "Default Gateway:"
netstat -rn | grep default | head -1
echo ""
echo "DNS Servers:"
scutil --dns | grep nameserver | head -3
```

Save this somewhere. You'll reference it throughout the course.

---

[Back to Module 01 README](README.md) | [Module 01 Cheatsheet](cheatsheet.md)

[Back to main guide](../README.md)
