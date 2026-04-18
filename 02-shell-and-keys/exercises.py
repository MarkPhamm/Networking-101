#!/usr/bin/env python3
"""
Module 02: Shell and Keys - Exercises
======================================
Explore SSH key concepts: key structure, asymmetric encryption concepts,
SSH config parsing, and file permissions.

Run with: python3 exercises.py

No external dependencies required -- stdlib only.

DISCLAIMER: The cryptographic demonstrations in this file are for EDUCATION
ONLY. They are toy implementations to illustrate concepts. Never use them
for real security. Use established libraries (OpenSSH, libsodium, etc.).
"""

import base64
import hashlib
import os
import random
import stat
import struct
import sys
import time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def banner(title):
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
# Exercise 1: List and inspect ~/.ssh/ directory
# ---------------------------------------------------------------------------

def exercise1_ssh_directory():
    """List files in ~/.ssh/ with their permissions and explain each one."""
    banner("EXERCISE 1: Your ~/.ssh/ Directory")

    ssh_dir = os.path.expanduser("~/.ssh")

    if not os.path.isdir(ssh_dir):
        warn(f"Directory not found: {ssh_dir}")
        info("Run 'ssh-keygen -t ed25519' to create your first key pair.")
        info("This will also create the ~/.ssh/ directory.")
        return

    # Known file purposes
    file_descriptions = {
        "authorized_keys": "Public keys allowed to log in as YOU (server-side)",
        "known_hosts": "Host keys of servers you've connected to",
        "config": "Your SSH client configuration (host aliases, settings)",
        "id_rsa": "RSA private key (KEEP SECRET)",
        "id_rsa.pub": "RSA public key (safe to share)",
        "id_ed25519": "Ed25519 private key (KEEP SECRET)",
        "id_ed25519.pub": "Ed25519 public key (safe to share)",
        "id_ecdsa": "ECDSA private key (KEEP SECRET)",
        "id_ecdsa.pub": "ECDSA public key (safe to share)",
    }

    # Required permissions
    required_permissions = {
        "id_rsa": 0o600,
        "id_ed25519": 0o600,
        "id_ecdsa": 0o600,
        "authorized_keys": 0o600,
        "config": 0o600,
    }

    entries = sorted(os.listdir(ssh_dir))
    ok(f"Found {len(entries)} items in {ssh_dir}\n")

    print(f"  {'Permissions':<12} {'Size':>8}  {'File':<25} {'Purpose'}")
    print(f"  {'-'*12} {'-'*8}  {'-'*25} {'-'*40}")

    for entry in entries:
        filepath = os.path.join(ssh_dir, entry)
        try:
            st = os.stat(filepath)
            mode = stat.filemode(st.st_mode)
            size = st.st_size
            desc = file_descriptions.get(entry, "")
            print(f"  {mode:<12} {size:>8}  {entry:<25} {desc}")

            # Check permissions
            octal_mode = stat.S_IMODE(st.st_mode)
            if entry in required_permissions:
                expected = required_permissions[entry]
                if octal_mode != expected:
                    warn(f"    ^ Permission should be {oct(expected)} (currently {oct(octal_mode)})")
                    info(f"    Fix with: chmod {oct(expected)[2:]} ~/.ssh/{entry}")
        except OSError as e:
            print(f"  {'?':<12} {'?':>8}  {entry:<25} (error: {e})")

    print()
    info("Permission rules (SSH is strict about these):")
    info("  ~/.ssh/           -> 700 (drwx------) only you can enter")
    info("  private keys      -> 600 (-rw-------) only you can read")
    info("  public keys       -> 644 (-rw-r--r--) anyone can read")
    info("  authorized_keys   -> 600 (-rw-------) only you can modify")
    info("  config            -> 600 (-rw-------) only you can read")
    info("")
    info("If permissions are wrong, SSH will REFUSE to use the key.")
    info('You\'ll see: "Permissions 0644 for \'id_rsa\' are too open."')


# ---------------------------------------------------------------------------
# Exercise 2: Parse SSH public key structure
# ---------------------------------------------------------------------------

def exercise2_parse_public_key():
    """Parse an SSH public key file and show its internal structure."""
    banner("EXERCISE 2: Inside an SSH Public Key")

    info("An SSH public key file looks like one long line:")
    info("  ssh-ed25519 AAAAC3Nza... user@host")
    info("But the base64 blob has internal structure. Let's decode it.\n")

    # Find a public key to parse
    ssh_dir = os.path.expanduser("~/.ssh")
    key_files = ["id_ed25519.pub", "id_rsa.pub", "id_ecdsa.pub"]

    pubkey_path = None
    for kf in key_files:
        candidate = os.path.join(ssh_dir, kf)
        if os.path.exists(candidate):
            pubkey_path = candidate
            break

    if pubkey_path is None:
        warn("No public key found in ~/.ssh/")
        info("Generate one with: ssh-keygen -t ed25519 -C 'your_email@example.com'")
        info("")
        info("Here's what the structure would look like:")
        _show_key_structure_example()
        return

    with open(pubkey_path, "r") as f:
        key_line = f.read().strip()

    parts = key_line.split()
    if len(parts) < 2:
        warn("Could not parse key file (unexpected format).")
        return

    key_type = parts[0]
    key_b64 = parts[1]
    comment = parts[2] if len(parts) > 2 else "(no comment)"

    ok(f"Parsing: {pubkey_path}")
    print(f"    Key type:  {key_type}")
    print(f"    Comment:   {comment}")
    print(f"    Base64:    {key_b64[:40]}...")
    print(f"    B64 len:   {len(key_b64)} characters")
    print()

    # Decode the base64 blob
    try:
        key_bytes = base64.b64decode(key_b64)
    except Exception as e:
        fail(f"Could not decode base64: {e}")
        return

    info(f"Decoded to {len(key_bytes)} raw bytes")
    info("Internal wire format (RFC 4253):\n")

    # Parse the internal structure: each field is a uint32 length prefix + data
    offset = 0
    field_num = 0
    while offset < len(key_bytes):
        if offset + 4 > len(key_bytes):
            break
        field_len = struct.unpack(">I", key_bytes[offset:offset+4])[0]
        offset += 4
        if offset + field_len > len(key_bytes):
            break
        field_data = key_bytes[offset:offset+field_len]
        offset += field_len
        field_num += 1

        # Describe the field
        if field_num == 1:
            # Key type string
            try:
                type_str = field_data.decode("ascii")
                print(f"    Field {field_num}: key type string = \"{type_str}\" ({field_len} bytes)")
            except Exception:
                print(f"    Field {field_num}: {field_len} bytes (expected key type)")
        else:
            # Key data
            hex_preview = field_data[:16].hex()
            if len(field_data) > 16:
                hex_preview += "..."
            print(f"    Field {field_num}: {field_len} bytes of key data")
            print(f"             hex: {hex_preview}")

    # Compute fingerprint
    fingerprint = hashlib.sha256(key_bytes).digest()
    fp_b64 = base64.b64encode(fingerprint).decode("ascii").rstrip("=")
    print()
    ok(f"Fingerprint: SHA256:{fp_b64}")
    info("This is what you see when SSH asks 'Are you sure you want to connect?'")
    info("It's a SHA-256 hash of the entire key blob, base64-encoded.")


def _show_key_structure_example():
    """Show example key structure when no real key is available."""
    print("  SSH public key format:")
    print("    [key-type] [base64-blob] [comment]")
    print()
    print("  The base64 blob contains:")
    print("    Field 1: 4-byte length + key type string (e.g., 'ssh-ed25519')")
    print("    Field 2: 4-byte length + key data (e.g., 32-byte Ed25519 public key)")
    print()
    print("  For RSA keys, the blob contains:")
    print("    Field 1: key type ('ssh-rsa')")
    print("    Field 2: public exponent (e)")
    print("    Field 3: modulus (n) -- this is the big number, often 2048-4096 bits")


# ---------------------------------------------------------------------------
# Exercise 3: Parse ~/.ssh/config
# ---------------------------------------------------------------------------

def exercise3_ssh_config():
    """Parse and display ~/.ssh/config host aliases."""
    banner("EXERCISE 3: Parsing ~/.ssh/config")

    info("~/.ssh/config lets you create shortcuts for SSH connections.")
    info("Instead of typing: ssh -i ~/.ssh/work_key -p 2222 mark@203.0.113.42")
    info("You can type: ssh work-server\n")

    config_path = os.path.expanduser("~/.ssh/config")

    if not os.path.exists(config_path):
        warn(f"File not found: {config_path}")
        info("You don't have an SSH config yet. Here's what one looks like:")
        _show_ssh_config_example()
        return

    with open(config_path, "r") as f:
        lines = f.readlines()

    # Parse the config into host blocks
    hosts = []
    current_host = None
    current_settings = {}

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Split on first whitespace
        parts = stripped.split(None, 1)
        if len(parts) != 2:
            continue

        key, value = parts[0], parts[1]

        if key.lower() == "host":
            if current_host is not None:
                hosts.append((current_host, current_settings))
            current_host = value
            current_settings = {}
        else:
            current_settings[key] = value

    if current_host is not None:
        hosts.append((current_host, current_settings))

    if not hosts:
        info("Config file exists but no Host entries found.")
        _show_ssh_config_example()
        return

    ok(f"Found {len(hosts)} Host entries:\n")

    for host_pattern, settings in hosts:
        print(f"  Host {host_pattern}")
        for key, value in settings.items():
            # Redact sensitive-looking values
            display_value = value
            if key.lower() in ("password", "proxycommand") and len(value) > 20:
                display_value = value[:10] + "..."
            print(f"    {key:<20} {display_value}")
        print()

    info("Common settings:")
    info("  HostName       -> Actual IP or hostname to connect to")
    info("  User           -> Default username for this host")
    info("  Port           -> Default port (if not 22)")
    info("  IdentityFile   -> Which private key to use")
    info("  ProxyJump      -> Jump through another host (bastion/jump box)")


def _show_ssh_config_example():
    """Show an example SSH config file."""
    print()
    print("  Example ~/.ssh/config:")
    print("  " + "-" * 50)
    print("  # Work bastion host")
    print("  Host bastion")
    print("      HostName 203.0.113.42")
    print("      User mark")
    print("      Port 22")
    print("      IdentityFile ~/.ssh/work_ed25519")
    print()
    print("  # Database server (through bastion)")
    print("  Host db-prod")
    print("      HostName 10.0.1.50")
    print("      User deploy")
    print("      ProxyJump bastion")
    print("      IdentityFile ~/.ssh/work_ed25519")
    print()
    print("  # Then just: ssh db-prod")
    print("  # Instead of: ssh -J mark@203.0.113.42 -i ~/.ssh/work_ed25519 deploy@10.0.1.50")
    print()
    info("Create this file with: nano ~/.ssh/config")
    info("Then set permissions: chmod 600 ~/.ssh/config")


# ---------------------------------------------------------------------------
# Exercise 4: Asymmetric Encryption Concept (Toy Demo)
# ---------------------------------------------------------------------------

def exercise4_asymmetric_encryption():
    """Demonstrate asymmetric encryption concepts with a simple toy cipher."""
    banner("EXERCISE 4: Asymmetric Encryption Concept (Educational Toy)")

    print("  *** DISCLAIMER ***")
    print("  This is a TOY demonstration to show the CONCEPT of asymmetric")
    print("  encryption. It is NOT cryptographically secure. Real SSH uses")
    print("  Ed25519, RSA, or ECDSA with proper implementations.")
    print()

    info("The core idea of asymmetric encryption:")
    info("  - Two keys: PUBLIC (share freely) and PRIVATE (keep secret)")
    info("  - What one key encrypts, only the other can decrypt")
    info("  - Knowing the public key doesn't help you find the private key\n")

    # Simple RSA-like demonstration with tiny numbers
    # Using actual small-prime RSA to show the real concept
    info("Mini-RSA with small primes (real RSA uses 2048+ bit primes):\n")

    # Step 1: Choose two primes
    p = 61
    q = 53
    n = p * q           # 3233
    phi = (p - 1) * (q - 1)  # 3120

    print(f"  Key generation:")
    print(f"    Choose two primes: p={p}, q={q}")
    print(f"    Compute n = p * q = {n}")
    print(f"    Compute phi(n) = (p-1)(q-1) = {phi}")

    # Step 2: Choose e (public exponent)
    e = 17  # Must be coprime with phi
    print(f"    Choose public exponent e = {e} (coprime with {phi})")

    # Step 3: Compute d (private exponent) such that (d * e) % phi == 1
    # Extended Euclidean algorithm
    d = pow(e, -1, phi)  # Python 3.8+ modular inverse
    print(f"    Compute private exponent d = {d} (such that d*e mod phi = 1)")
    print(f"    Verify: {d} * {e} mod {phi} = {(d * e) % phi}")
    print()

    print(f"  PUBLIC KEY:  (e={e}, n={n})  -- share this with everyone")
    print(f"  PRIVATE KEY: (d={d}, n={n})  -- NEVER share this")
    print()

    # Encrypt a message
    message = 42  # Must be < n
    print(f"  Encrypting message: {message}")
    ciphertext = pow(message, e, n)  # message^e mod n
    print(f"    ciphertext = message^e mod n = {message}^{e} mod {n} = {ciphertext}")

    # Decrypt
    decrypted = pow(ciphertext, d, n)  # ciphertext^d mod n
    print(f"    decrypted  = ciphertext^d mod n = {ciphertext}^{d} mod {n} = {decrypted}")
    print()

    if decrypted == message:
        ok(f"Decryption successful: {decrypted} matches original {message}")
    else:
        fail("Decryption failed (bug in demo)")

    print()
    info("How this applies to SSH authentication:")
    info("  1. You generate a key pair (ssh-keygen)")
    info("  2. You put the PUBLIC key on the server (~/.ssh/authorized_keys)")
    info("  3. When you connect, the server sends a random challenge")
    info("  4. Your client SIGNS the challenge with the PRIVATE key")
    info("  5. Server verifies the signature with the PUBLIC key")
    info("  6. Only someone with the private key could produce a valid signature")
    print()
    info("The private key NEVER leaves your machine. The server never sees it.")
    info("Even if an attacker captures the signed challenge, they can't extract")
    info("the private key from it (that would require factoring n, which is")
    info("computationally infeasible for 2048+ bit numbers).")


# ---------------------------------------------------------------------------
# Exercise 5: Simulating Key-Based Authentication
# ---------------------------------------------------------------------------

def exercise5_key_auth_simulation():
    """Simulate the SSH key-based authentication challenge-response."""
    banner("EXERCISE 5: Simulating Key-Based Auth (Challenge-Response)")

    info("SSH key authentication is a challenge-response protocol.")
    info("Let's simulate it step by step using HMAC (stdlib).\n")

    # In reality, SSH uses digital signatures (RSA/Ed25519).
    # We'll use HMAC with a shared-secret analogy to show the flow.
    # The concept is: prove you know a secret without revealing it.

    import hmac

    # Simulate key pair (in reality these are mathematically linked)
    # We use a shared secret here to demonstrate the FLOW, not the crypto.
    private_key = os.urandom(32)  # Client's private key
    # In real SSH, the public key is derived from the private key.
    # Here, the server stores a hash of the key as the "public key."
    public_key_hash = hashlib.sha256(private_key).hexdigest()

    print("  SETUP (done once with ssh-keygen + ssh-copy-id):")
    print(f"    Client has private key: {private_key[:8].hex()}... (secret!)")
    print(f"    Server has public key hash: {public_key_hash[:32]}...")
    print()

    # Step 1: Server creates a random challenge
    challenge = os.urandom(32)
    print("  AUTHENTICATION FLOW:")
    print(f"    1. Server sends challenge: {challenge[:16].hex()}...")

    # Step 2: Client signs the challenge with private key
    signature = hmac.new(private_key, challenge, hashlib.sha256).hexdigest()
    print(f"    2. Client signs with private key: {signature[:32]}...")

    # Step 3: Server verifies the signature
    # The server recomputes using the stored public info
    expected_sig = hmac.new(private_key, challenge, hashlib.sha256).hexdigest()
    valid = hmac.compare_digest(signature, expected_sig)

    print(f"    3. Server verifies signature: {'VALID' if valid else 'INVALID'}")
    print()

    if valid:
        ok("Authentication successful -- client proved it holds the private key!")
    else:
        fail("Authentication failed -- signature mismatch")

    print()
    info("Key insight: the private key was NEVER sent over the network.")
    info("The server only saw: the challenge it created, and the signature.")
    info("An eavesdropper who captures the signature cannot reuse it")
    info("(the next connection will have a different random challenge).")

    # Show what happens with a wrong key
    print()
    print("  FAILED ATTEMPT (wrong key):")
    wrong_key = os.urandom(32)
    wrong_sig = hmac.new(wrong_key, challenge, hashlib.sha256).hexdigest()
    matches = hmac.compare_digest(wrong_sig, expected_sig)
    print(f"    Attacker's signature: {wrong_sig[:32]}...")
    print(f"    Server verification:  {'VALID' if matches else 'INVALID'}")
    if not matches:
        fail("Permission denied (publickey) -- signature doesn't match")
        info("This is exactly what SSH returns when you use the wrong key.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("*" * 65)
    print("  MODULE 02: SHELL AND KEYS - EXERCISES")
    print("  Understanding SSH keys and authentication")
    print("*" * 65)

    exercise1_ssh_directory()
    exercise2_parse_public_key()
    exercise3_ssh_config()
    exercise4_asymmetric_encryption()
    exercise5_key_auth_simulation()

    print()
    print("=" * 65)
    print("  KEY TAKEAWAYS")
    print("=" * 65)
    print()
    info("1. ~/.ssh/ permissions matter -- SSH refuses to use keys with wrong perms")
    info("2. Public keys have internal structure: type string + key data fields")
    info("3. ~/.ssh/config saves you from typing long SSH commands")
    info("4. Asymmetric crypto: public key encrypts, private key decrypts")
    info("5. SSH auth is challenge-response: prove you have the key without sending it")
    info("6. The private key NEVER leaves your machine during authentication")
    print()
    info("Next: Module 03 - IP Addressing and DNS")
    print()


if __name__ == "__main__":
    main()
