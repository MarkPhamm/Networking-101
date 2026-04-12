# Module 01: SSH and Remote Access

## What You'll Learn

- What SSH is and why it exists
- The client-server model for remote access
- Step-by-step what happens when you type `ssh user@host`
- How password authentication works
- How to read and fix common SSH error messages
- How the `known_hosts` file protects you

---

## What Is SSH?

**SSH** stands for **Secure Shell**. It's a protocol that lets you securely connect to a remote machine and run commands on it, as if you were sitting right in front of it.

Before SSH, people used `telnet` and `rsh` (remote shell), which sent everything -- including passwords -- in plain text across the network. Anyone listening on the network could see your credentials. SSH encrypts everything: your password, your commands, the output. It's the difference between shouting your database password across an open office and whispering it through a secure phone line.

SSH operates on **port 22** by default. Remember this number. You'll see it everywhere.

### Data engineering analogy

Think of SSH like a **secure JDBC/ODBC connection** to a database. When your Python script connects to Postgres at `host:5432` with a username and password, it's doing conceptually the same thing: establishing an encrypted channel to a remote service, authenticating, and then exchanging data. SSH does this for shell access instead of SQL queries.

---

## The Client-Server Model

SSH uses a **client-server architecture**:

- **Client**: Your Mac. It initiates the connection. The program is `ssh`.
- **Server**: Your friend's machine (or an EC2 instance, or a database server). It runs `sshd` (the SSH daemon), which listens on port 22 and waits for incoming connections.

```
┌──────────────┐          ┌──────────────┐
│  Your Mac    │  ──────> │ Friend's     │
│  (client)    │  port 22 │ Server       │
│  runs: ssh   │  <────── │ runs: sshd   │
└──────────────┘          └──────────────┘
```

This is the same pattern as every client-server system you already use:

- Your browser (client) talks to a web server
- Your `psql` command (client) talks to PostgreSQL (server)
- Your Airflow worker (client) talks to a cloud API (server)

The key insight: **the server must be running and listening before the client can connect.** If `sshd` isn't running on your friend's machine, your connection will fail, no matter what you do on your end.

---

## What Happens When You Type `ssh user@host`

Let's trace what happens step by step when you run:

```bash
ssh mark@192.168.1.50
```

### Step 1: DNS Resolution (if using a hostname)

If you typed a hostname instead of an IP address (like `ssh mark@my-server.example.com`), your Mac first needs to convert that name into an IP address. It queries DNS (Domain Name System) to look up the IP. We cover this in depth in Module 03.

If you typed an IP address directly, this step is skipped.

### Step 2: TCP Connection to Port 22

Your Mac opens a **TCP connection** to the server's IP address on **port 22** (or whatever port you specify with `-p`). This is a three-way handshake:

1. Your Mac sends a SYN (synchronize) packet: "Hey, I want to connect."
2. The server replies with SYN-ACK: "Got it, I'm ready."
3. Your Mac sends ACK: "Great, let's go."

This happens in milliseconds on a local network. If this step fails, you'll get "Connection timed out" or "Connection refused."

### Step 3: Protocol Version Exchange

Both sides announce which version of SSH they support. You'll almost always see SSH-2.0 (the current standard).

```
SSH-2.0-OpenSSH_9.6
```

### Step 4: Key Exchange

This is where the encryption is set up. The client and server agree on:

- An encryption algorithm (like AES-256)
- A method to securely exchange keys (like Diffie-Hellman)

After this step, everything is encrypted. No one eavesdropping can read the traffic.

### Step 5: Server Authentication (Host Key Verification)

The server presents its **host key** -- a unique fingerprint that identifies it. Your Mac checks this against `~/.ssh/known_hosts`:

- **First connection**: You've never seen this server before, so SSH asks:

  ```
  The authenticity of host '192.168.1.50' can't be established.
  ED25519 key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxx.
  Are you sure you want to continue connecting (yes/no)?
  ```

  If you type `yes`, the server's key is saved to `~/.ssh/known_hosts`.

- **Subsequent connections**: SSH silently checks the stored key. If it matches, you proceed. If it doesn't match, you get a scary warning (more on that below).

### Step 6: User Authentication

Now the server knows it's talking to someone over an encrypted channel, but it doesn't know *who*. You authenticate, typically by:

- **Password**: The server prompts you and you type it in (sent encrypted)
- **Public key**: Your client proves it holds the private key matching a public key the server has on file (covered in Module 02)

### Step 7: Shell Session

Authentication succeeded. The server starts a shell session (bash, zsh, etc.) running as the user you specified. Your terminal is now connected to the remote machine. Every command you type is sent over the encrypted channel, executed remotely, and the output is sent back.

```
mark@remote-server:~$
```

You're in.

---

## Password Authentication Flow

The simplest authentication method:

1. The server sends a prompt: "Password:"
2. You type your password (it doesn't echo to the screen)
3. The password is sent to the server **over the encrypted channel** (it's safe in transit)
4. The server checks it against its user database (like `/etc/shadow` on Linux)
5. If correct, you're in. If not, you get "Permission denied" and can try again (usually 3 attempts)

Password auth is simple but has downsides:

- Passwords can be guessed or brute-forced
- You have to type them every time
- They can be phished

That's why Module 02 covers key-based authentication, which is better in almost every way.

---

## Common Failure Modes

This is the most important section. When SSH fails, the error message tells you *exactly* what went wrong -- if you know how to read it.

### "Connection refused"

```
ssh: connect to host 192.168.1.50 port 22: Connection refused
```

**What it means**: Your Mac successfully reached the server's IP, but nothing is listening on port 22. The server actively rejected the connection.

**Common causes**:

- The SSH daemon (`sshd`) is not running on the server
- SSH is running on a non-standard port (not 22)
- A firewall on the server is blocking port 22 with a REJECT rule

**What to check**:

- Is sshd running? (`systemctl status sshd` or `sudo launchctl list | grep ssh` on the server)
- Is it on a different port? Check `/etc/ssh/sshd_config` for the `Port` setting
- Try specifying the port: `ssh -p 2222 user@host`

**DE analogy**: This is like getting "Connection refused" when connecting to Postgres -- the database isn't running or it's on a different port than 5432.

### "Connection timed out"

```
ssh: connect to host 192.168.1.50 port 22: Operation timed out
```

**What it means**: Your Mac sent packets but never got a response. The packets disappeared into the void.

**Common causes**:

- The IP address is wrong (no machine exists at that address)
- A firewall is silently dropping packets (DROP rule, not REJECT)
- The server is on a different network you can't reach
- The server is powered off

**What to check**:

- Can you ping it? `ping 192.168.1.50`
- Is the IP correct? Double-check with the server owner
- Are you on the same network? (A 192.168.x.x address won't work from outside the LAN)

**DE analogy**: This is like your Airflow DAG timing out trying to reach a database in a VPC you don't have access to.

### "Permission denied"

```
mark@192.168.1.50: Permission denied (publickey,password).
```

**What it means**: You reached the server and SSH is running, but authentication failed. The connection is fine -- your credentials are wrong.

**Common causes**:

- Wrong username (the user doesn't exist on the server)
- Wrong password
- The server doesn't allow password auth (only public key)
- Your public key isn't in the server's `authorized_keys`

**What to check**:

- Is the username correct? (It's the *remote* user, not your local one)
- Look at what auth methods are listed in parentheses:
  - `(publickey,password)` -- server accepts both, but both failed
  - `(publickey)` -- server only accepts keys, no password allowed

### "Could not resolve hostname"

```
ssh: Could not resolve hostname my-server.example.com: nodename nor servname provided, or not known
```

**What it means**: DNS couldn't translate the hostname into an IP address. This happens before any connection attempt.

**Common causes**:

- Typo in the hostname
- DNS is down or misconfigured
- The hostname doesn't exist in any DNS server you can reach
- You're offline

**What to check**:

- Check your spelling
- Try the IP address directly instead: `ssh user@203.0.113.10`
- Test DNS: `dig my-server.example.com` or `nslookup my-server.example.com`
- Check your internet connection: `ping 8.8.8.8`

### "WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!"

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
```

**What it means**: The server's host key doesn't match what's stored in your `~/.ssh/known_hosts`. The server's identity appears to have changed.

**Common causes**:

- The server was reinstalled or its SSH keys were regenerated (most common)
- You're connecting to a different machine that now has the same IP (common with DHCP or cloud instances)
- An actual man-in-the-middle attack (rare but possible)

**What to do**:

- If you know the server was rebuilt, remove the old key:

  ```bash
  ssh-keygen -R 192.168.1.50
  ```

- Then connect again and accept the new key

---

## The `~/.ssh/known_hosts` File

Every time you connect to a new server and type `yes`, SSH saves that server's host key in `~/.ssh/known_hosts`. This file is your local record of "servers I've verified."

```bash
# View your known hosts
cat ~/.ssh/known_hosts
```

Each line looks something like:

```
192.168.1.50 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

The format is: `hostname-or-ip key-type public-key`

**Why it matters**: This protects you from man-in-the-middle attacks. If someone redirected your connection to a malicious server, the host key wouldn't match your `known_hosts` file, and SSH would warn you loudly.

**DE analogy**: It's like SSL certificate pinning. When your ETL pipeline connects to a database over TLS, it can verify the server's certificate to make sure it's talking to the real database and not an imposter. `known_hosts` does the same thing for SSH.

---

## Key Takeaways

1. **SSH is just an encrypted client-server connection** -- conceptually identical to a database connection
2. **The server must be running `sshd`** before you can connect
3. **Read the error messages** -- they tell you exactly which step failed
4. **"Connection refused" means the server rejects you** -- sshd isn't running or port is blocked
5. **"Connection timed out" means packets disappear** -- wrong IP, firewall, or unreachable network
6. **"Permission denied" means auth failed** -- right server, wrong credentials
7. **"Could not resolve hostname" means DNS failed** -- the name can't be turned into an IP

---

Next: [Module 02 - Shell and Keys](../02-shell-and-keys/) -- Learn key-based authentication so you never type a password again.

[Back to main guide](../README.md)
