#!/usr/bin/env python3
"""
Module 07: LAN, WAN, and Network Segments -- Python Exercises

Run with: python3 exercises.py

Covers:
  - Display the system's ARP table
  - Parse network interfaces and MAC addresses
  - Simulate ARP resolution (cache hit vs. broadcast request)
  - Layer 2 (MAC) vs. Layer 3 (IP) addressing demonstration
  - Simple VLAN simulator
"""

import subprocess
import sys
import random


# ---------------------------------------------------------------------------
# Exercise 1: Display the System ARP Table
# ---------------------------------------------------------------------------

def exercise_1() -> None:
    print("=" * 70)
    print("EXERCISE 1: Display the System ARP Table")
    print("=" * 70)
    print()
    print("The ARP table maps IP addresses to MAC addresses on your local")
    print("network. When your machine needs to send a frame to another device")
    print("on the same subnet, it looks up the MAC address here.")
    print()

    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            print(f"  [ERROR] arp returned code {result.returncode}")
            return

        lines = result.stdout.strip().splitlines()
        print("  --- ARP table entries ---")
        for line in lines[:20]:
            print(f"  {line}")
        if len(lines) > 20:
            print(f"  ... ({len(lines) - 20} more entries)")

        print()
        print("  Each entry shows: hostname (IP) at MAC-address on interface")
        print("  - The MAC address is the Layer 2 (data link) address")
        print("  - The IP address is the Layer 3 (network) address")
        print("  - 'incomplete' entries mean ARP got no reply (device may be offline)")

    except FileNotFoundError:
        print("  [SKIP] 'arp' command not found on this system.")
    except subprocess.TimeoutExpired:
        print("  [SKIP] arp command timed out.")

    print()


# ---------------------------------------------------------------------------
# Exercise 2: Parse Network Interfaces and MAC Addresses
# ---------------------------------------------------------------------------

def exercise_2() -> None:
    print("=" * 70)
    print("EXERCISE 2: Network Interfaces and MAC Addresses")
    print("=" * 70)
    print()
    print("Each network interface on your machine has a unique MAC address")
    print("(burned into the hardware or assigned by the OS). Let's find them.")
    print()

    try:
        result = subprocess.run(
            ["ifconfig", "-a"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            print(f"  [ERROR] ifconfig returned code {result.returncode}")
            return

        output = result.stdout
        current_iface = None
        interfaces = {}

        for line in output.splitlines():
            # Interface header line (no leading whitespace)
            if line and not line[0].isspace() and ":" in line:
                current_iface = line.split(":")[0]
                interfaces[current_iface] = {"mac": None, "ipv4": None}
            elif current_iface:
                stripped = line.strip()
                # MAC address (ether on macOS/Linux)
                if stripped.startswith("ether "):
                    interfaces[current_iface]["mac"] = stripped.split()[1]
                # IPv4 address
                if stripped.startswith("inet ") and "inet6" not in stripped:
                    interfaces[current_iface]["ipv4"] = stripped.split()[1]

        print(f"  {'Interface':<12s} {'MAC Address':<22s} {'IPv4 Address'}")
        print(f"  {'-'*12} {'-'*22} {'-'*18}")
        for iface, info in interfaces.items():
            mac = info["mac"] or "(none)"
            ipv4 = info["ipv4"] or "(none)"
            print(f"  {iface:<12s} {mac:<22s} {ipv4}")

        print()
        print("  Note:")
        print("  - lo0 (loopback) typically has no MAC address")
        print("  - en0 is usually Wi-Fi on macOS")
        print("  - MAC addresses are 6 bytes in hex (e.g., aa:bb:cc:dd:ee:ff)")

    except FileNotFoundError:
        print("  [SKIP] 'ifconfig' not found. On newer Linux, try 'ip addr'.")
    except subprocess.TimeoutExpired:
        print("  [SKIP] ifconfig timed out.")

    print()


# ---------------------------------------------------------------------------
# Exercise 3: Simulate ARP Resolution
# ---------------------------------------------------------------------------

def exercise_3() -> None:
    print("=" * 70)
    print("EXERCISE 3: Simulate ARP Resolution")
    print("=" * 70)
    print()
    print("ARP (Address Resolution Protocol) translates IP -> MAC on the")
    print("local subnet. If the mapping is cached, the frame is sent")
    print("immediately. If not, an ARP broadcast request goes out.")
    print()

    # Simulated ARP cache (what the machine already knows)
    arp_cache = {
        "192.168.1.1":   "aa:bb:cc:dd:ee:01",   # Router
        "192.168.1.10":  "aa:bb:cc:dd:ee:10",   # Laptop
        "192.168.1.20":  "aa:bb:cc:dd:ee:20",   # Phone
    }

    def arp_resolve(ip: str, cache: dict) -> str:
        """Look up IP in ARP cache; simulate broadcast if not found."""
        if ip in cache:
            print(f"  [CACHE HIT]  {ip} -> {cache[ip]}")
            return cache[ip]
        else:
            print(f"  [CACHE MISS] {ip} not in ARP cache")
            print(f"               Sending ARP broadcast: 'Who has {ip}? Tell 192.168.1.100'")
            # Simulate receiving a reply
            new_mac = "aa:bb:cc:dd:ee:{:02x}".format(random.randint(0x30, 0xFF))
            print(f"               ARP reply received: '{ip} is at {new_mac}'")
            cache[ip] = new_mac
            print(f"               ARP cache updated. {ip} -> {new_mac}")
            return new_mac

    print("  Current ARP cache:")
    for ip, mac in arp_cache.items():
        print(f"    {ip:<18s} -> {mac}")
    print()

    # Test lookups
    test_ips = [
        "192.168.1.1",    # Cache hit (router)
        "192.168.1.10",   # Cache hit (laptop)
        "192.168.1.50",   # Cache miss -- triggers ARP request
        "192.168.1.99",   # Cache miss -- triggers ARP request
    ]

    print("  Resolving addresses:")
    print()
    for ip in test_ips:
        arp_resolve(ip, arp_cache)
        print()

    print("  Updated ARP cache:")
    for ip, mac in arp_cache.items():
        print(f"    {ip:<18s} -> {mac}")
    print()


# ---------------------------------------------------------------------------
# Exercise 4: Layer 2 vs. Layer 3 Addressing
# ---------------------------------------------------------------------------

def exercise_4() -> None:
    print("=" * 70)
    print("EXERCISE 4: Layer 2 (MAC) vs. Layer 3 (IP) Addressing")
    print("=" * 70)
    print()
    print("When a packet travels across multiple networks, the IP addresses")
    print("(Layer 3) stay the same end-to-end, but the MAC addresses (Layer 2)")
    print("change at every hop. The MAC addresses are only meaningful within")
    print("a single network segment.")
    print()

    # Simulate a packet going from Host A -> Router -> Host B
    print("  Scenario: Host A (192.168.1.10) sends data to Host B (10.0.0.50)")
    print("            via Router (192.168.1.1 / 10.0.0.1)")
    print()

    hops = [
        {
            "segment": "LAN 1 (192.168.1.0/24)",
            "src_mac": "AA:AA:AA:AA:AA:01",  # Host A
            "dst_mac": "CC:CC:CC:CC:CC:01",  # Router's LAN1 interface
            "src_ip":  "192.168.1.10",
            "dst_ip":  "10.0.0.50",
            "note":    "Host A sends to Router (its default gateway)",
        },
        {
            "segment": "LAN 2 (10.0.0.0/24)",
            "src_mac": "CC:CC:CC:CC:CC:02",  # Router's LAN2 interface
            "dst_mac": "BB:BB:BB:BB:BB:01",  # Host B
            "src_ip":  "192.168.1.10",
            "dst_ip":  "10.0.0.50",
            "note":    "Router forwards to Host B on the next segment",
        },
    ]

    for i, hop in enumerate(hops, 1):
        print(f"  --- Hop {i}: {hop['segment']} ---")
        print(f"  Ethernet frame:")
        print(f"    Src MAC: {hop['src_mac']:<22s}  (Layer 2 -- changes per hop)")
        print(f"    Dst MAC: {hop['dst_mac']:<22s}  (Layer 2 -- changes per hop)")
        print(f"  IP packet (inside the frame):")
        print(f"    Src IP:  {hop['src_ip']:<22s}  (Layer 3 -- stays the same)")
        print(f"    Dst IP:  {hop['dst_ip']:<22s}  (Layer 3 -- stays the same)")
        print(f"  Note: {hop['note']}")
        print()

    print("  Key insight: The IP addresses are the 'final destination' -- they")
    print("  never change (ignoring NAT). The MAC addresses are 'next hop'")
    print("  directions that change at every router. It is like a postal")
    print("  system: the address on the letter (IP) stays the same, but the")
    print("  delivery truck (MAC) changes at each sorting facility.")
    print()


# ---------------------------------------------------------------------------
# Exercise 5: VLAN Simulator
# ---------------------------------------------------------------------------

def exercise_5() -> None:
    print("=" * 70)
    print("EXERCISE 5: VLAN Simulator")
    print("=" * 70)
    print()
    print("VLANs (Virtual LANs) logically segment a physical network.")
    print("Devices on the same VLAN can communicate directly (Layer 2).")
    print("Devices on different VLANs need a router, even if they are on")
    print("the same physical switch. Think of it like database schemas:")
    print("same server, but logically isolated.")
    print()

    # Define hosts and their VLAN assignments
    hosts = {
        "web-server-1":     {"ip": "10.0.10.10", "mac": "AA:00:00:00:10:01", "vlan": 10},
        "web-server-2":     {"ip": "10.0.10.11", "mac": "AA:00:00:00:10:02", "vlan": 10},
        "db-server-1":      {"ip": "10.0.20.10", "mac": "AA:00:00:00:20:01", "vlan": 20},
        "db-server-2":      {"ip": "10.0.20.11", "mac": "AA:00:00:00:20:02", "vlan": 20},
        "dev-workstation":  {"ip": "10.0.30.10", "mac": "AA:00:00:00:30:01", "vlan": 30},
        "admin-laptop":     {"ip": "10.0.30.11", "mac": "AA:00:00:00:30:02", "vlan": 30},
    }

    vlan_names = {
        10: "Web Tier",
        20: "Database Tier",
        30: "Management",
    }

    print("  Host assignments:")
    print(f"  {'Host':<22s} {'IP':<18s} {'VLAN':<8s} {'VLAN Name'}")
    print(f"  {'-'*22} {'-'*18} {'-'*8} {'-'*15}")
    for name, info in hosts.items():
        vname = vlan_names.get(info["vlan"], "?")
        print(f"  {name:<22s} {info['ip']:<18s} {info['vlan']:<8d} {vname}")

    print()

    # Test communication pairs
    test_pairs = [
        ("web-server-1",    "web-server-2"),      # Same VLAN
        ("db-server-1",     "db-server-2"),       # Same VLAN
        ("web-server-1",    "db-server-1"),       # Different VLANs
        ("dev-workstation", "admin-laptop"),       # Same VLAN
        ("admin-laptop",    "db-server-1"),       # Different VLANs
    ]

    print("  Communication test:")
    print(f"  {'Source':<22s} {'Destination':<22s} {'Same VLAN?':<12s} {'Result'}")
    print(f"  {'-'*22} {'-'*22} {'-'*12} {'-'*35}")

    for src_name, dst_name in test_pairs:
        src = hosts[src_name]
        dst = hosts[dst_name]
        same_vlan = src["vlan"] == dst["vlan"]

        if same_vlan:
            result = "Direct L2 communication (switch only)"
        else:
            result = "Requires router (inter-VLAN routing)"

        same_str = f"Yes ({src['vlan']})" if same_vlan else f"No ({src['vlan']}->{dst['vlan']})"
        print(f"  {src_name:<22s} {dst_name:<22s} {same_str:<12s} {result}")

    print()
    print("  Why VLANs matter for data engineering:")
    print("  - Database servers on VLAN 20 are isolated from web traffic")
    print("  - Only routed (and firewalled) traffic can cross VLAN boundaries")
    print("  - This is network-level defense in depth, like putting your")
    print("    data warehouse on a separate subnet from your application tier")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("###################################################################")
    print("#  Module 07: LAN, WAN, and Network Segments -- Python Exercises  #")
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
    print("  - ARP maps IP -> MAC on the local subnet (Layer 3 -> Layer 2).")
    print("  - MAC addresses change at every hop; IP addresses stay the same.")
    print("  - VLANs create logical segments on a physical switch.")
    print("  - Cross-VLAN traffic must pass through a router (and firewall).")
    print("  - Network segmentation is a security best practice, just like")
    print("    database schema isolation.")
    print("=" * 70)


if __name__ == "__main__":
    main()
