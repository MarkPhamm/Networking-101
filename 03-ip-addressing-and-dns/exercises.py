#!/usr/bin/env python3
"""
Module 03: IP Addressing and DNS - Exercises
=============================================
Explore IP addresses and DNS resolution using Python's standard library:
classify IPs, resolve hostnames, build a DNS cache, and do reverse lookups.

Run with: python3 exercises.py

No external dependencies required -- stdlib only.
"""

import ipaddress
import socket
import time
import sys


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
# Exercise 1: Classify IP Addresses
# ---------------------------------------------------------------------------

def exercise1_classify_ips():
    """Use the ipaddress module to classify IPs as public, private, etc."""
    banner("EXERCISE 1: Classifying IP Addresses")

    info("Python's ipaddress module can tell you everything about an IP.")
    info("Let's classify a set of addresses you'll encounter in practice.\n")

    test_ips = [
        "192.168.1.1",      # Private (home router)
        "10.0.0.1",         # Private (AWS VPC default)
        "172.16.0.1",       # Private (Docker default)
        "172.31.0.1",       # Private (AWS default VPC)
        "127.0.0.1",        # Loopback
        "8.8.8.8",          # Public (Google DNS)
        "1.1.1.1",          # Public (Cloudflare DNS)
        "169.254.1.1",      # Link-local (APIPA)
        "203.0.113.1",      # Documentation range (TEST-NET-3)
        "255.255.255.255",  # Broadcast
        "0.0.0.0",          # Unspecified
        "100.64.0.1",       # Shared address space (CGNAT)
    ]

    print(f"  {'IP Address':<20} {'Type':<15} {'Private?':<10} {'Notes'}")
    print(f"  {'-'*20} {'-'*15} {'-'*10} {'-'*30}")

    for ip_str in test_ips:
        ip = ipaddress.ip_address(ip_str)
        ip_type = _classify_ip(ip)
        is_private = ip.is_private
        notes = _ip_notes(ip_str)
        print(f"  {ip_str:<20} {ip_type:<15} {'Yes' if is_private else 'No':<10} {notes}")

    print()
    info("The private IP ranges (RFC 1918) you MUST memorize:")
    info("  10.0.0.0/8       -> 10.x.x.x        (large orgs, AWS VPCs)")
    info("  172.16.0.0/12    -> 172.16-31.x.x    (medium, Docker)")
    info("  192.168.0.0/16   -> 192.168.x.x      (home networks)")
    print()
    info("DE context: When you see 10.0.x.x in an AWS connection string,")
    info("that's a private IP inside a VPC. It's not reachable from the")
    info("internet -- you need a VPN, bastion host, or VPC peering.")


def _classify_ip(ip):
    """Return a human-readable classification of an IP address."""
    if ip.is_loopback:
        return "Loopback"
    if ip.is_link_local:
        return "Link-local"
    if ip.is_multicast:
        return "Multicast"
    if ip.is_reserved:
        return "Reserved"
    if ip.is_unspecified:
        return "Unspecified"
    if ip.is_private:
        return "Private"
    return "Public"


def _ip_notes(ip_str):
    """Return practical notes about specific IPs."""
    notes = {
        "192.168.1.1": "Typical home router",
        "10.0.0.1": "AWS VPC, corporate nets",
        "172.16.0.1": "Docker bridge default",
        "172.31.0.1": "AWS default VPC",
        "127.0.0.1": "Always this machine",
        "8.8.8.8": "Google Public DNS",
        "1.1.1.1": "Cloudflare DNS",
        "169.254.1.1": "Auto-assigned when DHCP fails",
        "203.0.113.1": "RFC 5737 docs (never real)",
        "255.255.255.255": "Broadcast to all on LAN",
        "0.0.0.0": "Bind to all interfaces",
        "100.64.0.1": "ISP CGNAT (shared space)",
    }
    return notes.get(ip_str, "")


# ---------------------------------------------------------------------------
# Exercise 2: DNS Resolution
# ---------------------------------------------------------------------------

def exercise2_dns_resolution():
    """Resolve domain names using socket functions."""
    banner("EXERCISE 2: DNS Resolution")

    info("DNS translates human-readable names to IP addresses.")
    info("Let's see how Python resolves names under the hood.\n")

    domains = [
        "localhost",
        "google.com",
        "github.com",
        "amazon.com",
        "cloudflare.com",
    ]

    # Method 1: gethostbyname (simple, IPv4 only)
    print("  Method 1: socket.gethostbyname() -- simple, returns one IPv4\n")
    for domain in domains:
        try:
            ip = socket.gethostbyname(domain)
            ok(f"{domain:<25} -> {ip}")
        except socket.gaierror as e:
            fail(f"{domain:<25} -> {e}")
    print()

    # Method 2: getaddrinfo (full, supports IPv4 and IPv6)
    print("  Method 2: socket.getaddrinfo() -- full results, IPv4 + IPv6\n")
    for domain in domains[:3]:  # Just a few to keep output manageable
        try:
            results = socket.getaddrinfo(domain, None)
            unique_ips = []
            seen = set()
            for family, socktype, proto, canonname, sockaddr in results:
                ip = sockaddr[0]
                fam_name = "IPv4" if family == socket.AF_INET else "IPv6"
                key = (ip, fam_name)
                if key not in seen:
                    seen.add(key)
                    unique_ips.append((ip, fam_name))

            ok(f"{domain} resolved to {len(unique_ips)} unique addresses:")
            for ip, fam in unique_ips[:6]:
                print(f"      {fam:<5}  {ip}")
            if len(unique_ips) > 6:
                print(f"      ... and {len(unique_ips) - 6} more")
        except socket.gaierror as e:
            fail(f"{domain}: {e}")
        print()

    info("gethostbyname() is simpler but only returns one IPv4 address.")
    info("getaddrinfo() returns all addresses (IPv4 + IPv6) and is what")
    info("modern applications should use. SSH uses getaddrinfo() internally.")


# ---------------------------------------------------------------------------
# Exercise 3: Network Interfaces and Local IPs
# ---------------------------------------------------------------------------

def exercise3_local_interfaces():
    """Show the machine's network interfaces and their IP addresses."""
    banner("EXERCISE 3: Your Machine's Network Addresses")

    info("Your machine has multiple network interfaces, each with its own IP.")
    info("Understanding which is which helps diagnose 'can't connect' issues.\n")

    hostname = socket.gethostname()
    ok(f"Hostname: {hostname}")
    print()

    # Get all address info for this machine
    try:
        results = socket.getaddrinfo(hostname, None)
        seen = set()
        addresses = []
        for family, socktype, proto, canonname, sockaddr in results:
            ip = sockaddr[0]
            fam_name = "IPv4" if family == socket.AF_INET else "IPv6"
            key = (ip, fam_name)
            if key not in seen:
                seen.add(key)
                addresses.append((ip, fam_name))

        print(f"  {'Address':<40} {'Family':<6} {'Classification'}")
        print(f"  {'-'*40} {'-'*6} {'-'*20}")

        for ip, fam in addresses:
            try:
                ip_obj = ipaddress.ip_address(ip)
                classification = _classify_ip(ip_obj)
            except ValueError:
                classification = "unknown"
            print(f"  {ip:<40} {fam:<6} {classification}")

    except socket.gaierror:
        warn("Could not resolve hostname to addresses.")

    # Also show the loopback
    print()
    info("Well-known addresses on every machine:")
    info("  127.0.0.1       -> Loopback (IPv4) -- always this machine")
    info("  ::1             -> Loopback (IPv6) -- always this machine")
    info("  0.0.0.0         -> Bind to ALL interfaces (server wildcard)")
    print()
    info("DE context: When a config says 'host: 0.0.0.0', the service")
    info("accepts connections on ANY interface. When it says '127.0.0.1',")
    info("it only accepts connections from the same machine (localhost).")
    info("This is why a database bound to 127.0.0.1 can't be reached remotely.")


# ---------------------------------------------------------------------------
# Exercise 4: Build a Simple DNS Cache
# ---------------------------------------------------------------------------

def exercise4_dns_cache():
    """Build a simple DNS cache with TTL tracking."""
    banner("EXERCISE 4: Building a DNS Cache")

    info("Real DNS resolvers cache results to avoid repeated lookups.")
    info("Let's build a simple cache and see the performance difference.\n")

    class DNSCache:
        """A simple DNS cache with TTL (Time To Live) support."""

        def __init__(self, default_ttl=30):
            self._cache = {}  # {hostname: (ip, expiry_time)}
            self._default_ttl = default_ttl
            self.hits = 0
            self.misses = 0

        def resolve(self, hostname):
            """Resolve a hostname, using cache if available and not expired."""
            now = time.time()

            # Check cache
            if hostname in self._cache:
                ip, expiry = self._cache[hostname]
                if now < expiry:
                    self.hits += 1
                    return ip, "CACHE HIT"
                else:
                    # Expired
                    del self._cache[hostname]

            # Cache miss -- do actual DNS lookup
            self.misses += 1
            try:
                ip = socket.gethostbyname(hostname)
                self._cache[hostname] = (ip, now + self._default_ttl)
                return ip, "CACHE MISS (resolved)"
            except socket.gaierror as e:
                return None, f"CACHE MISS (failed: {e})"

        def show_cache(self):
            """Display current cache contents."""
            now = time.time()
            if not self._cache:
                print("    (cache is empty)")
                return
            for hostname, (ip, expiry) in self._cache.items():
                remaining = max(0, expiry - now)
                print(f"    {hostname:<30} -> {ip:<16} TTL: {remaining:.0f}s")

    # Create cache with 60-second TTL
    cache = DNSCache(default_ttl=60)

    # First round: all cache misses
    domains = ["google.com", "github.com", "amazon.com", "google.com", "github.com"]

    print("  Round 1: First lookups (all should be cache misses)")
    print("  " + "-" * 55)
    for domain in domains[:3]:
        start = time.time()
        ip, status = cache.resolve(domain)
        elapsed_ms = (time.time() - start) * 1000
        print(f"    {domain:<25} -> {ip or 'FAILED':<16} [{status}] {elapsed_ms:.1f}ms")

    print()

    # Second round: should be cache hits
    print("  Round 2: Repeat lookups (should be cache hits)")
    print("  " + "-" * 55)
    for domain in domains:
        start = time.time()
        ip, status = cache.resolve(domain)
        elapsed_ms = (time.time() - start) * 1000
        print(f"    {domain:<25} -> {ip or 'FAILED':<16} [{status}] {elapsed_ms:.1f}ms")

    print()
    print("  Cache contents:")
    cache.show_cache()
    print()
    print(f"  Stats: {cache.hits} hits, {cache.misses} misses")
    print(f"  Hit rate: {cache.hits / max(1, cache.hits + cache.misses) * 100:.0f}%")

    print()
    info("Real DNS caches (in your OS, router, and ISP) work the same way.")
    info("The TTL is set by the domain owner -- popular sites use short TTLs")
    info("(60-300s) so they can update IPs quickly. Less-changed domains")
    info("use longer TTLs (3600s+) to reduce DNS traffic.")
    info("")
    info("DE context: When an Airflow DAG caches a database hostname resolution")
    info("and the IP changes (e.g., AWS RDS failover), stale cache = failed jobs.")
    info("This is why DNS TTLs matter for data infrastructure.")


# ---------------------------------------------------------------------------
# Exercise 5: Reverse DNS Lookup
# ---------------------------------------------------------------------------

def exercise5_reverse_dns():
    """Demonstrate reverse DNS: IP address -> hostname."""
    banner("EXERCISE 5: Reverse DNS Lookup")

    info("Forward DNS: hostname -> IP address")
    info("Reverse DNS: IP address -> hostname (PTR record)")
    info("Not all IPs have reverse DNS entries, but many do.\n")

    test_ips = [
        "8.8.8.8",          # Google DNS
        "1.1.1.1",          # Cloudflare DNS
        "127.0.0.1",        # Loopback
        "208.67.222.222",   # OpenDNS
    ]

    print(f"  {'IP Address':<20} {'Reverse DNS (hostname)'}")
    print(f"  {'-'*20} {'-'*40}")

    for ip in test_ips:
        try:
            hostname, aliases, addrs = socket.gethostbyaddr(ip)
            print(f"  {ip:<20} {hostname}")
            if aliases:
                for alias in aliases[:2]:
                    print(f"  {'':20} (alias: {alias})")
        except socket.herror as e:
            print(f"  {ip:<20} (no reverse DNS: {e})")
        except socket.gaierror as e:
            print(f"  {ip:<20} (lookup failed: {e})")
        except OSError as e:
            print(f"  {ip:<20} (error: {e})")

    print()
    info("Reverse DNS is used for:")
    info("  - Email server validation (anti-spam)")
    info("  - Logging (seeing hostnames instead of raw IPs)")
    info("  - Security auditing (who owns this IP?)")
    info("  - Traceroute output (route hops shown as hostnames)")
    print()
    info("DE context: When you see an IP in your Spark or Airflow logs,")
    info("reverse DNS can tell you which service that IP belongs to.")


# ---------------------------------------------------------------------------
# Exercise 6: IP Network Calculations
# ---------------------------------------------------------------------------

def exercise6_network_calculations():
    """Use the ipaddress module to work with CIDR notation and subnets."""
    banner("EXERCISE 6: IP Network Calculations (CIDR)")

    info("CIDR notation (like 10.0.0.0/16) defines a range of IP addresses.")
    info("Understanding this is essential for AWS VPCs, security groups, etc.\n")

    networks = [
        ("10.0.0.0/8", "Large private range (Class A)"),
        ("172.16.0.0/12", "Medium private range (Class B)"),
        ("192.168.1.0/24", "Typical home/small office LAN"),
        ("10.0.1.0/24", "Typical AWS subnet"),
        ("10.0.0.0/16", "Typical AWS VPC"),
        ("0.0.0.0/0", "Default route (all IPs)"),
    ]

    for cidr, description in networks:
        net = ipaddress.ip_network(cidr)
        print(f"  Network: {cidr}")
        print(f"    Description:     {description}")
        print(f"    Network address: {net.network_address}")
        print(f"    Broadcast:       {net.broadcast_address}")
        print(f"    Netmask:         {net.netmask}")
        print(f"    Host bits:       {net.max_prefixlen - net.prefixlen}")
        print(f"    Total addresses: {net.num_addresses:,}")
        print(f"    Usable hosts:    {max(0, net.num_addresses - 2):,}")

        # Show first and last few addresses
        if net.num_addresses <= 256:
            hosts = list(net.hosts())
            if hosts:
                print(f"    First host:      {hosts[0]}")
                print(f"    Last host:       {hosts[-1]}")
        print()

    # Demonstrate containment checks
    info("Containment checks (is this IP in this network?):\n")
    checks = [
        ("10.0.1.50", "10.0.0.0/16"),
        ("10.0.1.50", "10.0.1.0/24"),
        ("10.0.1.50", "10.0.2.0/24"),
        ("192.168.1.100", "10.0.0.0/8"),
        ("8.8.8.8", "0.0.0.0/0"),
    ]

    for ip_str, net_str in checks:
        ip = ipaddress.ip_address(ip_str)
        net = ipaddress.ip_network(net_str)
        contained = ip in net
        symbol = "IN" if contained else "NOT IN"
        print(f"    {ip_str:<18} {symbol:<8} {net_str}")

    print()
    info("DE context: AWS security groups and NACLs use CIDR notation.")
    info("When you set an inbound rule to allow 10.0.0.0/16 on port 5432,")
    info("you're allowing any IP from 10.0.0.0 to 10.0.255.255 to connect")
    info("to your database. Getting the CIDR wrong = security hole or lockout.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("*" * 65)
    print("  MODULE 03: IP ADDRESSING AND DNS - EXERCISES")
    print("  Exploring IP addresses and DNS with Python")
    print("*" * 65)

    exercise1_classify_ips()
    exercise2_dns_resolution()
    exercise3_local_interfaces()
    exercise4_dns_cache()
    exercise5_reverse_dns()
    exercise6_network_calculations()

    print()
    print("=" * 65)
    print("  KEY TAKEAWAYS")
    print("=" * 65)
    print()
    info("1. Private IPs (10.x, 172.16-31.x, 192.168.x) are not internet-routable")
    info("2. DNS is hierarchical caching: local cache -> resolver -> root -> TLD")
    info("3. getaddrinfo() is the modern way to resolve names (supports IPv6)")
    info("4. Reverse DNS (IP -> hostname) doesn't always work but is useful")
    info("5. CIDR notation defines IP ranges: /24 = 256 IPs, /16 = 65536 IPs")
    info("6. 'Is this IP in this network?' is the core question for firewalls/ACLs")
    print()
    info("Next: Module 04 - Ports and Services")
    print()


if __name__ == "__main__":
    main()
