#!/usr/bin/env python3
"""
Module 06: Firewalls and NAT -- Python Exercises

Run with: python3 exercises.py

Covers:
  - A Python firewall rule engine (first-match-wins)
  - Testing packets against firewall rules
  - Common firewall scenarios (allow SSH, deny inbound, allow outbound HTTP)
  - NAT translation table simulation
  - Multiple internal hosts sharing one public IP
  - Why "default deny" matters
"""

import json
import random


# ---------------------------------------------------------------------------
# Exercise 1: Firewall Rule Engine
# ---------------------------------------------------------------------------

def match_rule(rule: dict, packet: dict) -> bool:
    """
    Check if a single firewall rule matches a packet.

    Rule fields (all optional -- omitted means "match any"):
      action:    "allow" or "deny"
      protocol:  "tcp", "udp", "icmp", or "*"
      src_ip:    source IP or "*"
      dst_ip:    destination IP or "*"
      dst_port:  destination port number or "*"
      direction: "inbound" or "outbound"

    Packet fields:
      protocol, src_ip, dst_ip, dst_port, direction
    """
    for field in ("protocol", "src_ip", "dst_ip", "dst_port", "direction"):
        rule_val = rule.get(field, "*")
        if rule_val != "*" and str(rule_val) != str(packet.get(field, "")):
            return False
    return True


def evaluate_firewall(rules: list, packet: dict) -> str:
    """
    Evaluate a packet against an ordered list of firewall rules.
    Uses first-match-wins logic (like iptables or AWS NACLs).
    Returns "allow" or "deny".
    """
    for i, rule in enumerate(rules):
        if match_rule(rule, packet):
            return rule["action"], i, rule
    # If no rule matches, implicit deny (this is the "default deny" concept)
    return "deny", -1, {"description": "implicit default deny (no rule matched)"}


def exercise_1() -> None:
    print("=" * 70)
    print("EXERCISE 1: Firewall Rule Engine")
    print("=" * 70)
    print()
    print("Firewalls process rules top-to-bottom, first match wins.")
    print("This is like a SQL CASE WHEN: the first matching condition")
    print("determines the result; everything after is ignored.")
    print()

    # Define a realistic set of firewall rules
    rules = [
        {
            "description": "Allow SSH from trusted admin IP",
            "action": "allow",
            "protocol": "tcp",
            "src_ip": "203.0.113.10",
            "dst_ip": "*",
            "dst_port": 22,
            "direction": "inbound",
        },
        {
            "description": "Allow inbound HTTP",
            "action": "allow",
            "protocol": "tcp",
            "src_ip": "*",
            "dst_ip": "*",
            "dst_port": 80,
            "direction": "inbound",
        },
        {
            "description": "Allow inbound HTTPS",
            "action": "allow",
            "protocol": "tcp",
            "src_ip": "*",
            "dst_ip": "*",
            "dst_port": 443,
            "direction": "inbound",
        },
        {
            "description": "Deny ALL other inbound traffic",
            "action": "deny",
            "protocol": "*",
            "src_ip": "*",
            "dst_ip": "*",
            "dst_port": "*",
            "direction": "inbound",
        },
        {
            "description": "Allow outbound HTTP",
            "action": "allow",
            "protocol": "tcp",
            "src_ip": "*",
            "dst_ip": "*",
            "dst_port": 80,
            "direction": "outbound",
        },
        {
            "description": "Allow outbound HTTPS",
            "action": "allow",
            "protocol": "tcp",
            "src_ip": "*",
            "dst_ip": "*",
            "dst_port": 443,
            "direction": "outbound",
        },
        {
            "description": "Allow outbound DNS",
            "action": "allow",
            "protocol": "udp",
            "src_ip": "*",
            "dst_ip": "*",
            "dst_port": 53,
            "direction": "outbound",
        },
        {
            "description": "Deny ALL other outbound traffic",
            "action": "deny",
            "protocol": "*",
            "src_ip": "*",
            "dst_ip": "*",
            "dst_port": "*",
            "direction": "outbound",
        },
    ]

    print("  Firewall rules (processed top to bottom):")
    print(f"  {'#':<4s} {'Action':<8s} {'Proto':<8s} {'Src IP':<18s} {'Dst Port':<10s} {'Dir':<10s} Description")
    print(f"  {'-'*4} {'-'*8} {'-'*8} {'-'*18} {'-'*10} {'-'*10} {'-'*35}")
    for i, r in enumerate(rules):
        print(
            f"  {i:<4d} {r['action']:<8s} {r.get('protocol','*'):<8s} "
            f"{r.get('src_ip','*'):<18s} {str(r.get('dst_port','*')):<10s} "
            f"{r.get('direction','*'):<10s} {r['description']}"
        )

    print()

    # Test packets
    packets = [
        {
            "label": "SSH from trusted admin",
            "protocol": "tcp", "src_ip": "203.0.113.10",
            "dst_ip": "10.0.0.5", "dst_port": 22, "direction": "inbound",
        },
        {
            "label": "SSH from unknown IP",
            "protocol": "tcp", "src_ip": "198.51.100.99",
            "dst_ip": "10.0.0.5", "dst_port": 22, "direction": "inbound",
        },
        {
            "label": "HTTP request from internet",
            "protocol": "tcp", "src_ip": "198.51.100.50",
            "dst_ip": "10.0.0.5", "dst_port": 80, "direction": "inbound",
        },
        {
            "label": "MySQL from internet (port 3306)",
            "protocol": "tcp", "src_ip": "198.51.100.50",
            "dst_ip": "10.0.0.5", "dst_port": 3306, "direction": "inbound",
        },
        {
            "label": "Outbound HTTPS (e.g., pip install)",
            "protocol": "tcp", "src_ip": "10.0.0.5",
            "dst_ip": "151.101.0.223", "dst_port": 443, "direction": "outbound",
        },
        {
            "label": "Outbound DNS lookup",
            "protocol": "udp", "src_ip": "10.0.0.5",
            "dst_ip": "8.8.8.8", "dst_port": 53, "direction": "outbound",
        },
        {
            "label": "Outbound SSH (not allowed)",
            "protocol": "tcp", "src_ip": "10.0.0.5",
            "dst_ip": "198.51.100.1", "dst_port": 22, "direction": "outbound",
        },
    ]

    print("  Packet evaluation results:")
    print(f"  {'Packet':<40s} {'Result':<8s} {'Matched Rule'}")
    print(f"  {'-'*40} {'-'*8} {'-'*40}")

    for pkt in packets:
        action, rule_idx, matched = evaluate_firewall(rules, pkt)
        rule_desc = matched.get("description", "?")
        marker = "PASS" if action == "allow" else "BLOCK"
        print(f"  {pkt['label']:<40s} {marker:<8s} #{rule_idx}: {rule_desc}")

    print()
    print("  Key insight: SSH from the trusted admin is allowed (rule #0),")
    print("  but SSH from any other IP is denied (rule #3: deny all inbound).")
    print("  Rule order matters. Moving the deny-all above the allow rules")
    print("  would block everything.")
    print()


# ---------------------------------------------------------------------------
# Exercise 2: Why Default Deny Matters
# ---------------------------------------------------------------------------

def exercise_2() -> None:
    print("=" * 70)
    print("EXERCISE 2: Why 'Default Deny' Is Important")
    print("=" * 70)
    print()
    print("Compare two firewall strategies:")
    print()

    # Strategy A: Default ALLOW (bad)
    rules_default_allow = [
        {"description": "Block known-bad IP",     "action": "deny",  "src_ip": "198.51.100.99", "direction": "inbound", "protocol": "*", "dst_ip": "*", "dst_port": "*"},
        {"description": "Block port 3306",        "action": "deny",  "dst_port": 3306,          "direction": "inbound", "protocol": "*", "src_ip": "*", "dst_ip": "*"},
        # Everything else? Implicitly allowed -- DANGEROUS
    ]

    # Strategy B: Default DENY (good)
    rules_default_deny = [
        {"description": "Allow SSH from admin",   "action": "allow", "src_ip": "203.0.113.10",  "dst_port": 22,  "direction": "inbound", "protocol": "tcp", "dst_ip": "*"},
        {"description": "Allow HTTP",             "action": "allow", "dst_port": 80,             "direction": "inbound", "protocol": "tcp", "src_ip": "*", "dst_ip": "*"},
        {"description": "Deny everything else",   "action": "deny",  "protocol": "*",            "src_ip": "*",  "dst_ip": "*", "dst_port": "*", "direction": "inbound"},
    ]

    # A surprise attack packet
    surprise = {
        "label": "New attack on port 5432 (Postgres)",
        "protocol": "tcp", "src_ip": "192.0.2.50",
        "dst_ip": "10.0.0.5", "dst_port": 5432, "direction": "inbound",
    }

    print("  Strategy A -- Default Allow (blocklist approach):")
    print("    Rules: block known-bad IP, block port 3306, allow everything else.")
    action_a, _, matched_a = evaluate_firewall(rules_default_allow, surprise)
    print(f"    Surprise Postgres attack --> {action_a.upper()}")
    print(f"    Reason: {matched_a.get('description', 'no rule matched -- implicit deny')}")
    print()

    print("  Strategy B -- Default Deny (allowlist approach):")
    print("    Rules: allow SSH from admin, allow HTTP, deny everything else.")
    action_b, _, matched_b = evaluate_firewall(rules_default_deny, surprise)
    print(f"    Surprise Postgres attack --> {action_b.upper()}")
    print(f"    Reason: {matched_b['description']}")
    print()

    print("  Lesson: Default deny is safer because unknown threats are blocked")
    print("  automatically. You only open what you explicitly need. This is the")
    print("  principle behind AWS Security Groups (default deny inbound) and")
    print("  the principle of least privilege in database access control.")
    print()


# ---------------------------------------------------------------------------
# Exercise 3: NAT Translation Table
# ---------------------------------------------------------------------------

class NATTable:
    """
    Simulates a NAT (Network Address Translation) table.

    When an internal host sends a packet to the internet, the NAT device:
    1. Replaces the source (private IP, private port) with (public IP, mapped port)
    2. Records the mapping so return traffic can be translated back

    This is how your home router lets 10+ devices share one public IP.
    """

    def __init__(self, public_ip: str):
        self.public_ip = public_ip
        self.table = {}       # (private_ip, private_port) -> mapped_port
        self.reverse = {}     # mapped_port -> (private_ip, private_port)
        self.next_port = 40000  # Start of the ephemeral port range for mapping

    def outbound(self, private_ip: str, private_port: int, dst_ip: str, dst_port: int) -> dict:
        """Translate an outbound packet from private to public."""
        key = (private_ip, private_port)

        if key not in self.table:
            mapped_port = self.next_port
            self.next_port += 1
            self.table[key] = mapped_port
            self.reverse[mapped_port] = key

        mapped_port = self.table[key]
        return {
            "original_src": f"{private_ip}:{private_port}",
            "translated_src": f"{self.public_ip}:{mapped_port}",
            "dst": f"{dst_ip}:{dst_port}",
        }

    def inbound(self, mapped_port: int) -> dict | None:
        """Translate an inbound reply back to the original private host."""
        if mapped_port in self.reverse:
            private_ip, private_port = self.reverse[mapped_port]
            return {
                "public_dst": f"{self.public_ip}:{mapped_port}",
                "translated_to": f"{private_ip}:{private_port}",
            }
        return None

    def display_table(self) -> None:
        print(f"  {'Private (LAN)':<30s} {'Public (WAN)':<30s}")
        print(f"  {'-'*30} {'-'*30}")
        for (priv_ip, priv_port), mapped_port in self.table.items():
            print(f"  {priv_ip}:{priv_port:<10d} <-->  {self.public_ip}:{mapped_port}")


def exercise_3() -> None:
    print("=" * 70)
    print("EXERCISE 3: NAT Translation Simulation")
    print("=" * 70)
    print()
    print("NAT lets many private devices share a single public IP.")
    print("The router keeps a mapping table to route return traffic")
    print("back to the correct internal host. Think of it like a")
    print("mailroom in an office building: one street address, but")
    print("the mailroom knows which desk to deliver each envelope to.")
    print()

    nat = NATTable(public_ip="203.0.113.1")

    # Multiple internal hosts making outbound connections
    connections = [
        ("192.168.1.10", 54321, "93.184.216.34",  80),   # Laptop -> example.com HTTP
        ("192.168.1.11", 54322, "93.184.216.34",  443),  # Phone -> example.com HTTPS
        ("192.168.1.12", 54323, "151.101.1.69",   443),  # Server -> reddit.com HTTPS
        ("192.168.1.10", 54324, "8.8.8.8",        53),   # Laptop -> DNS query
        ("192.168.1.13", 54325, "93.184.216.34",  80),   # Another device -> example.com
    ]

    print("  --- Outbound translations (private -> public) ---")
    print()
    for priv_ip, priv_port, dst_ip, dst_port in connections:
        result = nat.outbound(priv_ip, priv_port, dst_ip, dst_port)
        print(f"  {result['original_src']:<25s} --> {result['translated_src']:<25s} --> {result['dst']}")

    print()
    print("  --- NAT table (what the router remembers) ---")
    print()
    nat.display_table()

    print()
    print("  --- Inbound reply translation (public -> private) ---")
    print()
    print("  When a reply comes back to the public IP, the router checks")
    print("  the destination port to find the original internal host:")
    print()

    for mapped_port in [40000, 40001, 40002]:
        result = nat.inbound(mapped_port)
        if result:
            print(f"  Reply to {result['public_dst']:<25s} --> forward to {result['translated_to']}")

    # Show what happens with an unknown port
    result = nat.inbound(99999)
    print(f"  Reply to {nat.public_ip}:99999{'':15s} --> DROPPED (no mapping -- unsolicited inbound)")

    print()
    print("  All 5 connections from different internal devices appear to")
    print(f"  come from the same public IP ({nat.public_ip}). The external")
    print("  server has no idea there are multiple devices behind the NAT.")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("###################################################################")
    print("#  Module 06: Firewalls and NAT -- Python Exercises               #")
    print("###################################################################")
    print()

    exercise_1()
    exercise_2()
    exercise_3()

    print("=" * 70)
    print("All exercises complete.")
    print()
    print("Key takeaways:")
    print("  - Firewalls use first-match-wins: rule order is critical.")
    print("  - Default deny is always safer than default allow.")
    print("  - NAT maps (private_ip, port) to (public_ip, mapped_port).")
    print("  - Multiple LAN devices share one public IP via port mapping.")
    print("  - These concepts map directly to AWS Security Groups / NACLs.")
    print("=" * 70)


if __name__ == "__main__":
    main()
