#!/usr/bin/env python3
"""
Module 05: Subnets and Routing -- Python Exercises

Run with: python3 exercises.py

Covers:
  - Subnet calculator using the ipaddress module
  - "Is this IP in this subnet?" checker
  - Listing all hosts in a small subnet
  - Parsing the system routing table
  - Simulating longest-prefix-match routing lookups
"""

import ipaddress
import subprocess
import sys


# ---------------------------------------------------------------------------
# Exercise 1: Subnet Calculator
# ---------------------------------------------------------------------------

def subnet_calculator(cidr: str) -> None:
    """Given a CIDR string like '192.168.1.0/24', print all key subnet info."""

    network = ipaddress.IPv4Network(cidr, strict=False)

    print(f"  CIDR notation:      {network}")
    print(f"  Network address:    {network.network_address}")
    print(f"  Subnet mask:        {network.netmask}")
    print(f"  Wildcard mask:      {network.hostmask}")
    print(f"  Broadcast address:  {network.broadcast_address}")
    print(f"  Prefix length:      /{network.prefixlen}")
    print(f"  Total addresses:    {network.num_addresses}")

    # Usable hosts: total minus network and broadcast (only meaningful for /30 or larger)
    if network.prefixlen <= 30:
        hosts = list(network.hosts())
        print(f"  Usable hosts:       {len(hosts)}")
        print(f"  First usable host:  {hosts[0]}")
        print(f"  Last usable host:   {hosts[-1]}")
    else:
        print(f"  Usable hosts:       {network.num_addresses} (point-to-point or single host)")


def exercise_1() -> None:
    print("=" * 70)
    print("EXERCISE 1: Subnet Calculator")
    print("=" * 70)
    print()
    print("The ipaddress module does the binary math for us, but understanding")
    print("what it computes is the real lesson. The network address has all host")
    print("bits set to 0; the broadcast address has all host bits set to 1.")
    print()

    test_cidrs = [
        "192.168.1.0/24",
        "10.0.0.0/16",
        "172.16.5.0/20",
        "192.168.100.0/28",
    ]

    for cidr in test_cidrs:
        print(f"--- {cidr} ---")
        subnet_calculator(cidr)
        print()


# ---------------------------------------------------------------------------
# Exercise 2: "Is This IP in This Subnet?" Checker
# ---------------------------------------------------------------------------

def is_ip_in_subnet(ip: str, cidr: str) -> bool:
    """Return True if the given IP address belongs to the given subnet."""
    return ipaddress.IPv4Address(ip) in ipaddress.IPv4Network(cidr, strict=False)


def exercise_2() -> None:
    print("=" * 70)
    print("EXERCISE 2: Is This IP in This Subnet?")
    print("=" * 70)
    print()
    print("Every device makes this check before sending a packet: is the")
    print("destination on my local subnet (send directly) or elsewhere (send")
    print("to the default gateway)?")
    print()

    tests = [
        ("192.168.1.50",  "192.168.1.0/24"),    # Yes
        ("192.168.2.10",  "192.168.1.0/24"),    # No -- different third octet
        ("10.0.5.200",    "10.0.0.0/16"),        # Yes
        ("10.1.0.1",      "10.0.0.0/16"),        # No -- 10.1 is outside 10.0.x.x/16
        ("172.16.3.100",  "172.16.0.0/20"),      # Yes (172.16.0.0 - 172.16.15.255)
        ("172.16.20.1",   "172.16.0.0/20"),      # No -- 172.16.20 is outside /20
        ("8.8.8.8",       "192.168.1.0/24"),    # No -- public IP not in private subnet
    ]

    for ip, cidr in tests:
        result = is_ip_in_subnet(ip, cidr)
        status = "YES -- same subnet" if result else "NO  -- different subnet"
        print(f"  {ip:20s} in {cidr:20s}  -->  {status}")

    print()


# ---------------------------------------------------------------------------
# Exercise 3: List All Hosts in a Small Subnet
# ---------------------------------------------------------------------------

def exercise_3() -> None:
    print("=" * 70)
    print("EXERCISE 3: List All Hosts in a /28 Subnet")
    print("=" * 70)
    print()
    print("A /28 gives us 16 total addresses (4 host bits: 2^4 = 16).")
    print("Two are reserved (network + broadcast), leaving 14 usable hosts.")
    print("This is small enough to list every address individually.")
    print()

    network = ipaddress.IPv4Network("192.168.1.0/28")

    print(f"  Network:    {network}")
    print(f"  Netmask:    {network.netmask}")
    print(f"  Network addr (reserved):   {network.network_address}")
    print(f"  Broadcast addr (reserved): {network.broadcast_address}")
    print()
    print("  All usable host addresses:")

    for i, host in enumerate(network.hosts(), start=1):
        print(f"    {i:2d}. {host}")

    print()
    print(f"  Total usable hosts: {len(list(network.hosts()))}")
    print()


# ---------------------------------------------------------------------------
# Exercise 4: Parse the System Routing Table
# ---------------------------------------------------------------------------

def exercise_4() -> None:
    print("=" * 70)
    print("EXERCISE 4: Parse the System Routing Table")
    print("=" * 70)
    print()
    print("The routing table is your machine's rulebook for forwarding packets.")
    print("Every packet your computer sends is matched against these rules.")
    print()

    try:
        result = subprocess.run(
            ["netstat", "-rn"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout

        if result.returncode != 0:
            print(f"  [ERROR] netstat returned code {result.returncode}")
            if result.stderr:
                print(f"  stderr: {result.stderr.strip()}")
            return

        print("--- Raw routing table (first 30 lines) ---")
        lines = output.strip().splitlines()
        for line in lines[:30]:
            print(f"  {line}")

        if len(lines) > 30:
            print(f"  ... ({len(lines) - 30} more lines)")

        # Try to identify the default gateway
        print()
        print("--- Key observations ---")
        for line in lines:
            lower = line.lower()
            if lower.startswith("default") or lower.startswith("0.0.0.0"):
                print(f"  Default route found: {line.strip()}")

    except FileNotFoundError:
        print("  [SKIP] 'netstat' not found on this system.")
    except subprocess.TimeoutExpired:
        print("  [SKIP] netstat timed out.")

    print()


# ---------------------------------------------------------------------------
# Exercise 5: Simulate Routing Table Lookups (Longest Prefix Match)
# ---------------------------------------------------------------------------

def longest_prefix_match(routing_table: list, destination: str) -> dict | None:
    """
    Given a routing table (list of dicts) and a destination IP string,
    find the best matching route using longest-prefix match.

    Each route dict has:
      - "network": CIDR string, e.g. "10.0.0.0/8"
      - "gateway": next-hop IP or "direct"
      - "interface": e.g. "eth0"

    Returns the best matching route dict, or None.
    """
    dest = ipaddress.IPv4Address(destination)
    best_match = None
    best_prefix_len = -1

    for route in routing_table:
        net = ipaddress.IPv4Network(route["network"], strict=False)
        if dest in net and net.prefixlen > best_prefix_len:
            best_match = route
            best_prefix_len = net.prefixlen

    return best_match


def exercise_5() -> None:
    print("=" * 70)
    print("EXERCISE 5: Simulated Routing Table Lookups")
    print("=" * 70)
    print()
    print("Routers pick the most specific (longest prefix) matching route.")
    print("If 10.0.0.0/8 and 10.0.1.0/24 both match, the /24 wins because")
    print("it is more specific -- like a SQL query optimizer choosing the")
    print("most selective index.")
    print()

    # Simulated routing table
    routing_table = [
        {"network": "0.0.0.0/0",       "gateway": "192.168.1.1",   "interface": "eth0"},
        {"network": "192.168.1.0/24",   "gateway": "direct",        "interface": "eth0"},
        {"network": "10.0.0.0/8",       "gateway": "192.168.1.254", "interface": "eth0"},
        {"network": "10.0.1.0/24",      "gateway": "192.168.1.253", "interface": "eth1"},
        {"network": "172.16.0.0/16",    "gateway": "192.168.1.252", "interface": "eth0"},
        {"network": "172.16.5.0/24",    "gateway": "192.168.1.251", "interface": "eth2"},
    ]

    print("  Routing table:")
    print(f"  {'Network':<22s} {'Gateway':<20s} {'Interface'}")
    print(f"  {'-' * 22} {'-' * 20} {'-' * 10}")
    for route in routing_table:
        print(f"  {route['network']:<22s} {route['gateway']:<20s} {route['interface']}")

    print()

    # Test destinations
    test_destinations = [
        "192.168.1.50",   # Direct -- matches /24
        "10.0.1.100",     # Matches both /8 and /24 -- /24 wins
        "10.0.2.50",      # Matches /8 only
        "172.16.5.10",    # Matches both /16 and /24 -- /24 wins
        "172.16.100.1",   # Matches /16 only
        "8.8.8.8",        # Matches only the default route 0.0.0.0/0
    ]

    print("  Lookup results:")
    print(f"  {'Destination':<18s} {'Matched Route':<22s} {'Gateway':<20s} {'Why'}")
    print(f"  {'-' * 18} {'-' * 22} {'-' * 20} {'-' * 30}")

    for dest in test_destinations:
        match = longest_prefix_match(routing_table, dest)
        if match:
            net = ipaddress.IPv4Network(match["network"], strict=False)
            reason = f"/{net.prefixlen} is most specific match"
            print(f"  {dest:<18s} {match['network']:<22s} {match['gateway']:<20s} {reason}")
        else:
            print(f"  {dest:<18s} {'NO MATCH':<22s} {'--':<20s} dropped!")

    print()
    print("  Notice how 10.0.1.100 matches the /24 route (via .253) rather")
    print("  than the /8 route (via .254). Longest prefix match in action.")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("###################################################################")
    print("#  Module 05: Subnets and Routing -- Python Exercises             #")
    print("###################################################################")
    print()

    exercise_1()
    exercise_2()
    exercise_3()
    exercise_4()
    exercise_5()

    print("=" * 70)
    print("All exercises complete.")
    print()
    print("Key takeaways:")
    print("  - The ipaddress module handles subnet math; understanding the")
    print("    binary logic behind it is what matters.")
    print("  - 'Is this IP in this subnet?' is the fundamental routing decision.")
    print("  - Longest-prefix match is how routers (and cloud VPCs) choose routes.")
    print("  - Your machine already has a routing table -- inspect it often.")
    print("=" * 70)


if __name__ == "__main__":
    main()
