#!/usr/bin/env python3
"""
Module 00: The Big Picture - Exercises
======================================
Traces the journey of an SSH connection step by step, using Python's
standard library to demonstrate what happens at each stage.

Run with: python3 exercises.py

No external dependencies required -- stdlib only.
"""

import socket
import struct
import sys
import time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(step_number, title):
    """Print a clear section banner for each step."""
    print()
    print("=" * 65)
    print(f"  STEP {step_number}: {title}")
    print("=" * 65)
    print()


def info(msg):
    """Print an indented informational line."""
    print(f"  [INFO]  {msg}")


def ok(msg):
    """Print a success line."""
    print(f"  [OK]    {msg}")


def warn(msg):
    """Print a warning line."""
    print(f"  [WARN]  {msg}")


def fail(msg):
    """Print a failure line."""
    print(f"  [FAIL]  {msg}")


# ---------------------------------------------------------------------------
# Step 1: Parsing the SSH command
# ---------------------------------------------------------------------------

def step1_parse_command():
    """Demonstrate how the shell parses an SSH command."""
    banner(1, "SHELL PARSES THE COMMAND")

    example_commands = [
        "ssh mark@my-server.example.com",
        "ssh -p 2222 mark@my-server.example.com",
        "ssh my-server",   # relies on ~/.ssh/config
    ]

    for cmd in example_commands:
        print(f"  Command: {cmd}")
        parts = cmd.split()

        # Extract user and host
        user = None
        host = None
        port = 22  # default

        i = 0
        while i < len(parts):
            if parts[i] == "ssh":
                i += 1
                continue
            if parts[i] == "-p" and i + 1 < len(parts):
                port = int(parts[i + 1])
                i += 2
                continue
            # The last positional argument is [user@]host
            target = parts[i]
            if "@" in target:
                user, host = target.split("@", 1)
            else:
                host = target
                user = "(current user)"
            i += 1

        print(f"    -> User: {user}")
        print(f"    -> Host: {host}")
        print(f"    -> Port: {port}")
        print()

    info("The SSH client also reads ~/.ssh/config for host aliases,")
    info("identity files, proxy commands, and other settings.")
    info("This is covered in Module 02 - Shell and Keys.")


# ---------------------------------------------------------------------------
# Step 2: DNS Resolution
# ---------------------------------------------------------------------------

def step2_dns_resolution():
    """Demonstrate DNS resolution using socket.getaddrinfo()."""
    banner(2, "DNS RESOLUTION (hostname -> IP address)")

    hostnames_to_resolve = [
        "localhost",
        "google.com",
        "github.com",
    ]

    for hostname in hostnames_to_resolve:
        print(f"  Resolving: {hostname}")
        try:
            # getaddrinfo returns a list of 5-tuples:
            # (family, type, proto, canonname, sockaddr)
            results = socket.getaddrinfo(hostname, 22, socket.AF_INET, socket.SOCK_STREAM)
            if results:
                ip = results[0][4][0]
                ok(f"{hostname} -> {ip}")
                if len(results) > 1:
                    other_ips = set(r[4][0] for r in results)
                    if len(other_ips) > 1:
                        info(f"  Multiple IPs returned: {', '.join(other_ips)}")
            else:
                warn(f"No results for {hostname}")
        except socket.gaierror as e:
            fail(f"Could not resolve {hostname}: {e}")
            info("This is the 'Could not resolve hostname' error you see in SSH.")
        print()

    # Also demonstrate a failing resolution
    print("  Resolving: this-host-does-not-exist.example.invalid")
    try:
        socket.getaddrinfo("this-host-does-not-exist.example.invalid", 22)
        warn("Somehow resolved! (unexpected)")
    except socket.gaierror as e:
        fail(f"Could not resolve: {e}")
        info("This is exactly what SSH shows when DNS fails:")
        info('  "ssh: Could not resolve hostname ... nodename nor servname provided"')


# ---------------------------------------------------------------------------
# Step 3: TCP Three-Way Handshake
# ---------------------------------------------------------------------------

def step3_tcp_handshake():
    """Demonstrate the TCP connection (the Python-visible part of the handshake)."""
    banner(3, "TCP THREE-WAY HANDSHAKE (SYN, SYN-ACK, ACK)")

    info("When you call socket.connect(), the OS performs the 3-way handshake")
    info("under the hood: SYN -> SYN-ACK -> ACK. Python doesn't expose the")
    info("individual packets, but we can observe the result.\n")

    # Try connecting to localhost on port 22 (SSH)
    target_host = "127.0.0.1"
    target_port = 22

    print(f"  Attempting TCP connection to {target_host}:{target_port} (SSH)...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)

    try:
        start = time.time()
        sock.connect((target_host, target_port))
        elapsed_ms = (time.time() - start) * 1000

        ok(f"TCP connection established in {elapsed_ms:.1f} ms")
        local_addr = sock.getsockname()
        remote_addr = sock.getpeername()
        info(f"Local  endpoint: {local_addr[0]}:{local_addr[1]}  (your machine, ephemeral port)")
        info(f"Remote endpoint: {remote_addr[0]}:{remote_addr[1]}  (server, SSH port)")
        print()
        info("The three-way handshake completed successfully:")
        info("  Your Mac  ---- SYN ---->  Server:22")
        info("  Your Mac  <--- SYN-ACK -  Server:22")
        info("  Your Mac  ---- ACK ---->  Server:22")
        info("  Connection ESTABLISHED")

        # Try to read the SSH banner (Step 4 preview)
        try:
            ssh_banner = sock.recv(256)
            if ssh_banner:
                print()
                info(f"Server SSH banner: {ssh_banner.decode('utf-8', errors='replace').strip()}")
                info("(This is Step 4 -- the version exchange that happens right after TCP connects)")
        except Exception:
            pass

        sock.close()

    except ConnectionRefusedError:
        fail(f"Connection REFUSED on {target_host}:{target_port}")
        print()
        info("This means the TCP SYN reached the server, but the server sent")
        info("back a RST (reset) packet. Nothing is listening on port 22.")
        info("The SSH daemon (sshd) is likely not running.")
        print()
        info("In SSH, this looks like:")
        info('  "ssh: connect to host 127.0.0.1 port 22: Connection refused"')

    except socket.timeout:
        fail(f"Connection TIMED OUT to {target_host}:{target_port}")
        print()
        info("This means the SYN packet was sent but no SYN-ACK came back.")
        info("A firewall is dropping packets, or the host is unreachable.")
        print()
        info("In SSH, this looks like:")
        info('  "ssh: connect to host ... port 22: Operation timed out"')

    except OSError as e:
        fail(f"Connection failed: {e}")

    finally:
        sock.close()

    # Also demonstrate connecting to a port with nothing listening
    print()
    unused_port = 59123
    print(f"  Attempting TCP connection to {target_host}:{unused_port} (nothing listening)...")
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.settimeout(3)
    try:
        sock2.connect((target_host, unused_port))
        ok("Connected (something is unexpectedly listening here)")
        sock2.close()
    except ConnectionRefusedError:
        fail(f"Connection REFUSED -- nothing listening on port {unused_port}")
        info("This is what 'Connection refused' looks like at the socket level.")
    except socket.timeout:
        fail("Connection timed out.")
    finally:
        sock2.close()


# ---------------------------------------------------------------------------
# Step 4: SSH Version Exchange
# ---------------------------------------------------------------------------

def step4_version_exchange():
    """Show the SSH version exchange by connecting to port 22."""
    banner(4, "SSH VERSION EXCHANGE")

    info("Right after the TCP handshake, both sides send a version string.")
    info("This is plain text -- the only unencrypted part of SSH.\n")

    target_host = "127.0.0.1"
    target_port = 22

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect((target_host, target_port))
        # Read the server's version string
        server_version = sock.recv(256).decode("utf-8", errors="replace").strip()
        ok(f"Server version: {server_version}")

        # Send our "client" version string
        client_version = "SSH-2.0-Networking101_Exercise"
        sock.sendall((client_version + "\r\n").encode("utf-8"))
        info(f"We sent:        {client_version}")
        print()
        info("Both sides now know they speak SSH-2.0.")
        info("Next would come the key exchange (Step 5), but that requires")
        info("implementing the full SSH protocol -- way beyond a socket demo.")

        sock.close()
    except ConnectionRefusedError:
        warn("Cannot demonstrate -- SSH not running on localhost:22.")
        info("If sshd were running, we would see something like:")
        info("  Server version: SSH-2.0-OpenSSH_9.6")
        info("  Client version: SSH-2.0-OpenSSH_9.7")
    except socket.timeout:
        warn("Connection timed out to localhost:22.")
    except OSError as e:
        warn(f"Could not connect: {e}")
    finally:
        sock.close()


# ---------------------------------------------------------------------------
# Step 5: Key Exchange (Conceptual)
# ---------------------------------------------------------------------------

def step5_key_exchange_concept():
    """Demonstrate the Diffie-Hellman concept with small numbers."""
    banner(5, "KEY EXCHANGE (Diffie-Hellman Concept)")

    info("SSH uses Diffie-Hellman to establish a shared secret without")
    info("ever sending the secret over the network. Here's how it works")
    info("with small numbers (real SSH uses numbers hundreds of digits long).\n")

    # Simplified Diffie-Hellman with small numbers for illustration
    # DISCLAIMER: This is for education only. Real DH uses much larger primes.
    p = 23  # A prime number (publicly known)
    g = 5   # A generator (publicly known)

    print(f"  Public parameters (both sides know these):")
    print(f"    p (prime)     = {p}")
    print(f"    g (generator) = {g}")
    print()

    # Alice (client) picks a private secret
    a = 6  # Alice's private key (secret, never sent)
    A = pow(g, a, p)  # Alice's public value: g^a mod p
    print(f"  Client (Alice):")
    print(f"    Private secret:  a = {a}  (NEVER leaves the client)")
    print(f"    Public value:    A = g^a mod p = {g}^{a} mod {p} = {A}")
    print()

    # Bob (server) picks a private secret
    b = 15  # Bob's private key (secret, never sent)
    B = pow(g, b, p)  # Bob's public value: g^b mod p
    print(f"  Server (Bob):")
    print(f"    Private secret:  b = {b}  (NEVER leaves the server)")
    print(f"    Public value:    B = g^b mod p = {g}^{b} mod {p} = {B}")
    print()

    # They exchange public values (visible to anyone watching)
    print(f"  Exchanged over the network (visible to eavesdroppers):")
    print(f"    Client sends A = {A}")
    print(f"    Server sends B = {B}")
    print()

    # Each side computes the shared secret
    shared_secret_alice = pow(B, a, p)  # B^a mod p
    shared_secret_bob = pow(A, b, p)    # A^b mod p

    print(f"  Client computes shared secret: B^a mod p = {B}^{a} mod {p} = {shared_secret_alice}")
    print(f"  Server computes shared secret: A^b mod p = {A}^{b} mod {p} = {shared_secret_bob}")
    print()

    if shared_secret_alice == shared_secret_bob:
        ok(f"Both sides arrived at the SAME shared secret: {shared_secret_alice}")
        print()
        info("An eavesdropper saw: p=23, g=5, A=8, B=2")
        info("But computing the shared secret from these public values requires")
        info("solving the discrete logarithm problem -- computationally infeasible")
        info("with the large numbers (2048+ bits) used in real SSH.")
    else:
        fail("Shared secrets don't match (bug in demo code!)")

    print()
    info("After the key exchange, SSH also verifies the server's host key")
    info("against your ~/.ssh/known_hosts file -- covered in Module 01.")


# ---------------------------------------------------------------------------
# Step 6: Authentication (Conceptual)
# ---------------------------------------------------------------------------

def step6_authentication_concept():
    """Demonstrate authentication concepts."""
    banner(6, "AUTHENTICATION (password or public key)")

    info("After encryption is established, the server verifies your identity.")
    info("Two common methods:\n")

    # Password auth
    print("  METHOD 1: Password Authentication")
    print("  " + "-" * 40)
    print("    1. Server sends: 'Password:'")
    print("    2. You type your password (encrypted in transit)")
    print("    3. Server checks against /etc/shadow")
    print("    4. Match -> access granted")
    print()

    # Public key auth
    print("  METHOD 2: Public Key Authentication")
    print("  " + "-" * 40)
    print("    1. Client offers a public key from ~/.ssh/id_ed25519.pub")
    print("    2. Server checks ~/.ssh/authorized_keys for that key")
    print("    3. If found, server sends a random challenge")
    print("    4. Client signs challenge with private key")
    print("    5. Server verifies signature with public key")
    print("    6. Valid signature -> access granted (no password needed)")
    print()

    info("Public key auth is more secure because:")
    info("  - Private key never leaves your machine")
    info("  - Nothing replayable is sent over the network")
    info("  - No password to guess or brute-force")
    info("")
    info("Covered in depth in Module 02 - Shell and Keys.")


# ---------------------------------------------------------------------------
# Step 7: Channel Opens
# ---------------------------------------------------------------------------

def step7_channel_opens():
    """Describe the final step of the SSH connection."""
    banner(7, "CHANNEL OPENS -- YOU GET A SHELL")

    info("Authentication succeeded. Here's what happens next:")
    print()
    print("    1. Client requests a 'session' channel")
    print("    2. Client requests a pseudo-terminal (pty) allocation")
    print("    3. Client requests the server to start a shell")
    print("    4. Server launches /bin/bash (or /bin/zsh) as the remote user")
    print("    5. stdin/stdout/stderr are wired through the encrypted tunnel")
    print()
    print("    mark@my-server:~$")
    print("    ^")
    print("    |")
    print("    You're in. Every keystroke you type is encrypted, sent to the")
    print("    server, fed to the shell, and the output is sent back encrypted.")
    print()

    info("The entire journey -- from pressing Enter to seeing the remote prompt --")
    info("typically takes under a second on a fast network.")


# ---------------------------------------------------------------------------
# Bonus: Full Connection Lifecycle Demo
# ---------------------------------------------------------------------------

def bonus_connection_lifecycle():
    """Demonstrate the full TCP connection lifecycle."""
    print()
    print("=" * 65)
    print("  BONUS: TCP CONNECTION LIFECYCLE")
    print("=" * 65)
    print()

    info("Let's trace a complete TCP connection lifecycle.\n")

    target_host = "127.0.0.1"
    target_port = 22

    # Create socket
    print("  1. CREATE SOCKET")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    info(f"Socket created: family={sock.family.name}, type={sock.type.name}")
    print()

    try:
        # Connect (3-way handshake)
        print("  2. CONNECT (TCP 3-way handshake)")
        start = time.time()
        sock.connect((target_host, target_port))
        elapsed_ms = (time.time() - start) * 1000
        local = sock.getsockname()
        remote = sock.getpeername()
        ok(f"Connected in {elapsed_ms:.1f} ms")
        info(f"  {local[0]}:{local[1]} <---> {remote[0]}:{remote[1]}")
        print()

        # Exchange data
        print("  3. EXCHANGE DATA")
        banner_data = sock.recv(256)
        info(f"Received {len(banner_data)} bytes from server")
        info(f"Content: {banner_data.decode('utf-8', errors='replace').strip()}")
        print()

        # Close (FIN handshake)
        print("  4. CLOSE (TCP FIN handshake)")
        info("Closing connection gracefully...")
        sock.close()
        ok("Connection closed")
        print()
        info("Under the hood, closing involves another handshake:")
        info("  Client ---- FIN ---->  Server")
        info("  Client <--- ACK -----  Server")
        info("  Client <--- FIN -----  Server")
        info("  Client ---- ACK ---->  Server")
        info("  Connection CLOSED")

    except ConnectionRefusedError:
        warn("SSH not running on localhost:22 -- can't demonstrate full lifecycle.")
        info("The lifecycle would be: create -> connect -> exchange data -> close.")
        info("Each phase corresponds to a part of the SSH connection process.")
        sock.close()
    except socket.timeout:
        warn("Connection timed out.")
        sock.close()
    except OSError as e:
        warn(f"Connection error: {e}")
        sock.close()


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

def print_summary():
    """Print a summary mapping steps to modules."""
    print()
    print("=" * 65)
    print("  SUMMARY: THE SSH CONNECTION JOURNEY")
    print("=" * 65)
    print()
    print("  Step  What Happens              Where to Learn More")
    print("  ----  ------------------------  ----------------------------")
    print("  1     Shell parses command       Module 02: Shell and Keys")
    print("  2     DNS resolves hostname      Module 03: IP Addressing & DNS")
    print("  3     TCP 3-way handshake        Module 04: Ports and Services")
    print("  4     SSH version exchange       Module 01: SSH and Remote Access")
    print("  5     Key exchange (DH)          Module 01 + Module 02")
    print("  6     Authentication             Module 02: Shell and Keys")
    print("  7     Channel opens (shell)      Module 01: SSH and Remote Access")
    print()
    print("  Error Message                    -> Step That Failed")
    print("  ---------------------------------  -------------------")
    print("  'Could not resolve hostname'     -> Step 2 (DNS)")
    print("  'Connection timed out'           -> Step 3 (TCP)")
    print("  'Connection refused'             -> Step 3 (TCP)")
    print("  'HOST IDENTIFICATION CHANGED'    -> Step 5 (Key Exchange)")
    print("  'Permission denied'              -> Step 6 (Auth)")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("*" * 65)
    print("  MODULE 00: THE BIG PICTURE")
    print("  What Actually Happens When You Type 'ssh user@host'")
    print("*" * 65)
    print()
    print("  This script traces the 7 steps of an SSH connection,")
    print("  demonstrating each with real Python socket operations")
    print("  where possible, and conceptual explanations where not.")
    print()

    step1_parse_command()
    step2_dns_resolution()
    step3_tcp_handshake()
    step4_version_exchange()
    step5_key_exchange_concept()
    step6_authentication_concept()
    step7_channel_opens()
    bonus_connection_lifecycle()
    print_summary()

    print("  Done! Work through Modules 01-08 to deep-dive into each step.")
    print()


if __name__ == "__main__":
    main()
