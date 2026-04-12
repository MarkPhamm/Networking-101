#!/usr/bin/env python3
"""
Module 01: SSH and Remote Access - Exercises
=============================================
Explore SSH concepts using Python's standard library: parsing known_hosts,
reading SSH config, testing port connectivity, and understanding error modes.

Run with: python3 exercises.py

No external dependencies required -- stdlib only.
"""

import os
import socket
import base64
import hashlib
import struct
import time
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title):
    """Print a section banner."""
    print()
    print("=" * 65)
    print(f"  {title}")
    print("=" * 65)
    print()


def info(msg):
    print(f"  [INFO]  {msg}")


def ok(msg):
    print(f"  [OK]    {msg}")


def warn(msg):
    print(f"  [WARN]  {msg}")


def fail(msg):
    print(f"  [FAIL]  {msg}")


# ---------------------------------------------------------------------------
# Exercise 1: Parse ~/.ssh/known_hosts
# ---------------------------------------------------------------------------

def exercise1_known_hosts():
    """Parse and display the user's known_hosts file."""
    banner("EXERCISE 1: Parsing ~/.ssh/known_hosts")

    info("Every time you type 'yes' when SSH asks about a new host,")
    info("the server's host key is saved in ~/.ssh/known_hosts.")
    info("Let's see what's in yours.\n")

    known_hosts_path = os.path.expanduser("~/.ssh/known_hosts")

    if not os.path.exists(known_hosts_path):
        warn(f"File not found: {known_hosts_path}")
        info("You haven't SSH'd into any servers yet (or the file was cleared).")
        info("Connect to any server once and this file will be created.")
        return

    with open(known_hosts_path, "r") as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    if not lines:
        warn("known_hosts file exists but is empty.")
        return

    ok(f"Found {len(lines)} host entries in known_hosts\n")

    print(f"  {'Host/IP':<35} {'Key Type':<20} {'Fingerprint (SHA256)'}")
    print(f"  {'-'*35} {'-'*20} {'-'*45}")

    for line in lines[:15]:  # Show first 15 entries
        parts = line.split()
        if len(parts) < 3:
            continue

        host = parts[0]
        key_type = parts[1]

        # Compute the fingerprint (SHA256 of the base64-decoded key)
        try:
            key_bytes = base64.b64decode(parts[2])
            fingerprint = hashlib.sha256(key_bytes).digest()
            fp_b64 = base64.b64encode(fingerprint).decode("ascii").rstrip("=")
            fp_display = f"SHA256:{fp_b64}"
        except Exception:
            fp_display = "(could not compute)"

        # If the host field is hashed (starts with |1|), note that
        if host.startswith("|1|"):
            host_display = "(hashed)"
        else:
            # Truncate long host entries
            host_display = host[:33] + ".." if len(host) > 35 else host

        print(f"  {host_display:<35} {key_type:<20} {fp_display[:45]}")

    if len(lines) > 15:
        print(f"\n  ... and {len(lines) - 15} more entries")

    print()
    info("Hashed entries (shown as '(hashed)') protect your privacy --")
    info("an attacker who steals this file can't easily see which servers")
    info("you've connected to. HashKnownHosts is enabled by default on macOS.")
    print()
    info("To see the fingerprint SSH shows when you connect to a server:")
    info("  ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub  (on the server)")


# ---------------------------------------------------------------------------
# Exercise 2: Read SSH server configuration
# ---------------------------------------------------------------------------

def exercise2_sshd_config():
    """Parse /etc/ssh/sshd_config and show key settings."""
    banner("EXERCISE 2: Reading SSH Server Configuration")

    info("The SSH server (sshd) is configured via /etc/ssh/sshd_config.")
    info("Let's look at the important settings.\n")

    sshd_config_path = "/etc/ssh/sshd_config"

    if not os.path.exists(sshd_config_path):
        warn(f"File not found: {sshd_config_path}")
        info("This file exists on machines running an SSH server.")
        return

    try:
        with open(sshd_config_path, "r") as f:
            lines = f.readlines()
    except PermissionError:
        warn(f"Permission denied reading {sshd_config_path}")
        info("Try running: sudo python3 exercises.py")
        info("Or view it manually: sudo cat /etc/ssh/sshd_config")
        info("")
        info("Key settings you'd typically find:")
        _show_sshd_config_explainer()
        return

    # Parse key settings
    important_keys = {
        "Port": "Which port sshd listens on (default: 22)",
        "PermitRootLogin": "Whether root can SSH in directly",
        "PasswordAuthentication": "Whether password login is allowed",
        "PubkeyAuthentication": "Whether public key login is allowed",
        "AuthorizedKeysFile": "Where the server looks for authorized public keys",
        "MaxAuthTries": "How many auth attempts before disconnecting",
        "X11Forwarding": "Whether X11 GUI forwarding is allowed",
        "AllowTcpForwarding": "Whether SSH tunneling is allowed",
        "UsePAM": "Whether Pluggable Auth Modules are used",
        "PermitEmptyPasswords": "Whether empty passwords are allowed (should be no!)",
    }

    found_settings = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split(None, 1)
        if len(parts) == 2:
            key, value = parts
            if key in important_keys:
                found_settings[key] = value

    if found_settings:
        ok(f"Found {len(found_settings)} active settings (non-commented):\n")
        for key, value in found_settings.items():
            desc = important_keys.get(key, "")
            print(f"    {key:<25} = {value:<15}  # {desc}")
    else:
        info("All settings appear to be commented out (using defaults).")
        info("SSH uses sensible defaults when settings are not explicitly set.")

    print()
    _show_sshd_config_explainer()


def _show_sshd_config_explainer():
    """Show what key sshd_config settings mean."""
    print("  Key settings to understand:")
    print()
    print("    Port 22")
    print("      -> The port sshd listens on. Change this to reduce automated")
    print("         scanning, but remember to use 'ssh -p <port>' to connect.")
    print()
    print("    PasswordAuthentication yes|no")
    print("      -> If 'no', only key-based auth works. More secure, but you")
    print("         MUST set up your public key first or you'll be locked out.")
    print()
    print("    PermitRootLogin no|yes|prohibit-password")
    print("      -> 'prohibit-password' allows root login only with a key.")
    print("         Best practice: set to 'no' and use sudo after logging in.")
    print()
    print("    PubkeyAuthentication yes")
    print("      -> Enables public key authentication (the default and recommended).")


# ---------------------------------------------------------------------------
# Exercise 3: Test SSH Port Connectivity
# ---------------------------------------------------------------------------

def exercise3_ssh_port_test():
    """Test SSH port connectivity on localhost."""
    banner("EXERCISE 3: Testing SSH Port Connectivity")

    info("Before SSH can negotiate anything, the TCP connection to port 22")
    info("must succeed. Let's test it.\n")

    targets = [
        ("127.0.0.1", 22, "localhost SSH"),
        ("127.0.0.1", 2222, "localhost alternate SSH port"),
    ]

    for host, port, description in targets:
        print(f"  Testing: {description} ({host}:{port})")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)

        try:
            start = time.time()
            sock.connect((host, port))
            elapsed_ms = (time.time() - start) * 1000
            ok(f"Port {port} is OPEN (connected in {elapsed_ms:.1f} ms)")

            # Try to read the SSH banner
            try:
                data = sock.recv(256)
                if data:
                    decoded = data.decode("utf-8", errors="replace").strip()
                    if decoded.startswith("SSH-"):
                        info(f"SSH server identified: {decoded}")
                    else:
                        info(f"Service response: {decoded[:60]}")
            except Exception:
                pass

        except ConnectionRefusedError:
            fail(f"Port {port} is CLOSED (connection refused)")
            info("No service is listening on this port.")

        except socket.timeout:
            fail(f"Port {port} TIMED OUT")
            info("Packets are being dropped (firewall?) or host is unreachable.")

        except OSError as e:
            fail(f"Error: {e}")

        finally:
            sock.close()
            print()


# ---------------------------------------------------------------------------
# Exercise 4: SSH Connection Error Scenarios
# ---------------------------------------------------------------------------

def exercise4_error_scenarios():
    """Demonstrate different SSH connection error scenarios at the socket level."""
    banner("EXERCISE 4: SSH Connection Error Scenarios")

    info("When SSH fails, the error maps to a specific socket-level failure.")
    info("Let's see what each one looks like in Python.\n")

    # Scenario 1: Connection Refused
    print("  SCENARIO 1: Connection Refused")
    print("  " + "-" * 50)
    info("Cause: Port is reachable but nothing is listening.")
    info("SSH error: 'ssh: connect to host ... port 22: Connection refused'")
    print()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect(("127.0.0.1", 59876))  # Unlikely to have anything listening
        ok("Connected (unexpected!)")
        sock.close()
    except ConnectionRefusedError as e:
        fail(f"Socket error: {e}")
        info("The OS sent a RST packet back immediately -- it knows nothing")
        info("is listening on that port. This is fast (milliseconds).")
    except Exception as e:
        fail(f"Other error: {e}")
    finally:
        sock.close()

    print()

    # Scenario 2: Connection Timeout (simulated)
    print("  SCENARIO 2: Connection Timeout")
    print("  " + "-" * 50)
    info("Cause: Packets sent but no response (firewall DROP, wrong IP, host down).")
    info("SSH error: 'ssh: connect to host ... port 22: Operation timed out'")
    print()

    # Using a non-routable IP to simulate timeout (RFC 5737 test range)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)  # Short timeout for demo
    try:
        info("Connecting to 192.0.2.1 (RFC 5737 TEST-NET, non-routable)...")
        info("This will timeout -- packets go out but no response comes back...")
        start = time.time()
        sock.connect(("192.0.2.1", 22))
        ok("Connected (unexpected!)")
    except socket.timeout:
        elapsed = time.time() - start
        fail(f"Timed out after {elapsed:.1f} seconds")
        info("No response at all. The SYN packet was sent but nothing came back.")
        info("This is slow (waits for the full timeout) and frustrating.")
    except OSError as e:
        # On some systems, non-routable addresses fail differently
        fail(f"OS error: {e}")
        info("The OS couldn't route to this address at all.")
    finally:
        sock.close()

    print()

    # Scenario 3: DNS Resolution Failure
    print("  SCENARIO 3: DNS Resolution Failure")
    print("  " + "-" * 50)
    info("Cause: Hostname cannot be resolved to an IP address.")
    info("SSH error: 'Could not resolve hostname ... nodename nor servname'")
    print()

    try:
        socket.getaddrinfo("this-server-does-not-exist.invalid", 22)
        warn("Resolved (unexpected!)")
    except socket.gaierror as e:
        fail(f"DNS error: {e}")
        info("The hostname could not be translated to an IP address.")
        info("This fails BEFORE any connection is attempted.")

    print()

    # Summary comparison
    print("  COMPARISON: How to tell errors apart")
    print("  " + "-" * 50)
    print()
    print("    Error               Speed      Meaning")
    print("    -----------------   ---------  --------------------------------")
    print("    Connection refused  Instant    Server reachable, port closed")
    print("    Connection timeout  Slow       Packets lost (firewall/wrong IP)")
    print("    DNS failure         Instant    Hostname can't be resolved")
    print("    Permission denied   After ~1s  Connected OK, auth failed")
    print()
    info("Speed of failure is a diagnostic clue! Instant failure means the")
    info("server responded; slow timeout means packets are being dropped.")


# ---------------------------------------------------------------------------
# Exercise 5: Understanding known_hosts entries in detail
# ---------------------------------------------------------------------------

def exercise5_host_key_deep_dive():
    """Deep dive into SSH host key structure."""
    banner("EXERCISE 5: Understanding SSH Host Keys")

    info("When SSH connects, the server presents a host key. Let's look")
    info("at what an SSH public key actually contains.\n")

    # Check for system host keys (the server's identity)
    host_key_paths = [
        "/etc/ssh/ssh_host_ed25519_key.pub",
        "/etc/ssh/ssh_host_rsa_key.pub",
        "/etc/ssh/ssh_host_ecdsa_key.pub",
    ]

    found_key = False
    for path in host_key_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    key_line = f.read().strip()
                parts = key_line.split()
                if len(parts) >= 2:
                    key_type = parts[0]
                    key_b64 = parts[1]
                    comment = parts[2] if len(parts) > 2 else "(no comment)"

                    # Decode and analyze the key
                    key_bytes = base64.b64decode(key_b64)
                    fingerprint = hashlib.sha256(key_bytes).digest()
                    fp_b64 = base64.b64encode(fingerprint).decode("ascii").rstrip("=")

                    ok(f"Host key found: {path}")
                    print(f"    Type:        {key_type}")
                    print(f"    Comment:     {comment}")
                    print(f"    Key size:    {len(key_bytes)} bytes (raw)")
                    print(f"    Fingerprint: SHA256:{fp_b64}")
                    print()

                    # Parse the internal structure
                    info("Internal structure of the key blob:")
                    offset = 0
                    field_num = 0
                    while offset < len(key_bytes) and field_num < 4:
                        if offset + 4 > len(key_bytes):
                            break
                        field_len = struct.unpack(">I", key_bytes[offset:offset+4])[0]
                        offset += 4
                        if offset + field_len > len(key_bytes):
                            break
                        field_data = key_bytes[offset:offset+field_len]
                        offset += field_len
                        field_num += 1

                        # First field is always the key type string
                        if field_num == 1:
                            try:
                                print(f"    Field {field_num}: key type = {field_data.decode('ascii')}")
                            except Exception:
                                print(f"    Field {field_num}: {field_len} bytes")
                        else:
                            print(f"    Field {field_num}: {field_len} bytes of key data")

                    found_key = True
                    print()

            except PermissionError:
                warn(f"Permission denied: {path}")
                info("Try: ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub")
            except Exception as e:
                warn(f"Error reading {path}: {e}")

    if not found_key:
        warn("No system host keys found (or no permission to read them).")
        info("Host keys are created when sshd is first configured.")
        info("On macOS, enable Remote Login in System Preferences to generate them.")

    # Explain the fingerprint
    print()
    info("The fingerprint is what SSH shows when you first connect:")
    info("  'ED25519 key fingerprint is SHA256:xxxxxxxxxxx'")
    info("  'Are you sure you want to continue connecting (yes/no)?'")
    info("")
    info("If you say 'yes', the full public key is saved in ~/.ssh/known_hosts.")
    info("On future connections, SSH silently compares the server's key to")
    info("what's in known_hosts. If they don't match, you get the scary")
    info("'REMOTE HOST IDENTIFICATION HAS CHANGED' warning.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("*" * 65)
    print("  MODULE 01: SSH AND REMOTE ACCESS - EXERCISES")
    print("  Exploring SSH concepts with Python sockets")
    print("*" * 65)

    exercise1_known_hosts()
    exercise2_sshd_config()
    exercise3_ssh_port_test()
    exercise4_error_scenarios()
    exercise5_host_key_deep_dive()

    print()
    print("=" * 65)
    print("  KEY TAKEAWAYS")
    print("=" * 65)
    print()
    info("1. known_hosts maps servers to their public keys (trust on first use)")
    info("2. sshd_config controls what the server allows (ports, auth methods)")
    info("3. Connection refused = fast failure = port closed or sshd not running")
    info("4. Connection timeout = slow failure = firewall or wrong IP")
    info("5. DNS failure = instant = hostname can't be resolved")
    info("6. Host keys have internal structure: type + key data fields")
    print()
    info("Next: Module 02 - Shell and Keys (key-based authentication)")
    print()


if __name__ == "__main__":
    main()
