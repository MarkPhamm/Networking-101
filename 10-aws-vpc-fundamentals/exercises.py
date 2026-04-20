#!/usr/bin/env python3
"""
Module 10: VPC CIDR Planning Simulator

Exercises:
  1. Validate VPC CIDRs (must be /16 to /28, RFC 1918 ranges)
  2. Plan a multi-environment VPC layout given requirements
  3. Detect overlapping CIDRs (critical for VPC peering)
  4. Print a visual layout of the planned VPC

Run: python3 exercises.py
No external dependencies required.
"""

import ipaddress


# ---------------------------------------------------------------------------
# Exercise 1: VPC CIDR Validator
# ---------------------------------------------------------------------------

# RFC 1918 private address ranges
RFC1918_RANGES = [
    ipaddress.IPv4Network("10.0.0.0/8"),
    ipaddress.IPv4Network("172.16.0.0/12"),
    ipaddress.IPv4Network("192.168.0.0/16"),
]

# AWS VPC CIDR prefix length must be between /16 and /28
MIN_PREFIX = 16
MAX_PREFIX = 28


def validate_vpc_cidr(cidr_str):
    """
    Validate whether a CIDR block is a valid AWS VPC CIDR.

    Rules:
    - Must be a valid CIDR notation
    - Prefix length must be between /16 and /28
    - Must fall within an RFC 1918 private range

    Returns a dict with 'valid' (bool) and 'reason' (str).
    """
    try:
        network = ipaddress.IPv4Network(cidr_str, strict=True)
    except (ValueError, ipaddress.AddressValueError) as e:
        return {"valid": False, "reason": f"Invalid CIDR notation: {e}"}

    prefix = network.prefixlen

    if prefix < MIN_PREFIX:
        return {
            "valid": False,
            "reason": (
                f"Prefix /{prefix} is too large. AWS VPC requires /{MIN_PREFIX} "
                f"to /{MAX_PREFIX}. A /{prefix} gives {network.num_addresses:,} "
                f"addresses -- maximum is /{MIN_PREFIX} ({2**(32-MIN_PREFIX):,} addresses)."
            ),
        }

    if prefix > MAX_PREFIX:
        return {
            "valid": False,
            "reason": (
                f"Prefix /{prefix} is too small. AWS VPC requires /{MIN_PREFIX} "
                f"to /{MAX_PREFIX}. A /{prefix} gives only {network.num_addresses} "
                f"addresses -- minimum is /{MAX_PREFIX} ({2**(32-MAX_PREFIX)} addresses)."
            ),
        }

    is_private = any(
        network.subnet_of(rfc1918) for rfc1918 in RFC1918_RANGES
    )
    if not is_private:
        return {
            "valid": False,
            "reason": (
                f"{cidr_str} is not in an RFC 1918 private range. "
                f"VPCs should use: 10.0.0.0/8, 172.16.0.0/12, or 192.168.0.0/16."
            ),
        }

    return {
        "valid": True,
        "reason": (
            f"{cidr_str} is valid. "
            f"{network.num_addresses:,} total addresses, "
            f"range {network.network_address} - {network.broadcast_address}."
        ),
    }


def exercise_1():
    """Validate a set of VPC CIDR candidates."""
    print("=" * 70)
    print("EXERCISE 1: VPC CIDR Validator")
    print("=" * 70)
    print()
    print("AWS VPC CIDRs must be /16 to /28 and use RFC 1918 private ranges.")
    print("Let's validate some candidates:")
    print()

    test_cidrs = [
        ("10.0.0.0/16", "Standard production VPC"),
        ("172.16.0.0/16", "Alternative private range"),
        ("192.168.1.0/24", "Smaller VPC for testing"),
        ("10.0.0.0/8", "Too large -- exceeds /16 maximum"),
        ("10.0.0.0/30", "Too small -- below /28 minimum"),
        ("8.8.8.0/24", "Public IP range -- not RFC 1918"),
        ("10.0.0.0/28", "Minimum allowed size"),
        ("192.168.0.0/20", "Mid-size VPC"),
        ("172.32.0.0/16", "Looks private but outside 172.16-31 range"),
        ("10.0.1.0/16", "Not on a network boundary -- host bits set"),
    ]

    for cidr, description in test_cidrs:
        result = validate_vpc_cidr(cidr)
        status = "VALID" if result["valid"] else "INVALID"
        icon = "[+]" if result["valid"] else "[X]"
        print(f"  {icon} {cidr:20s} ({description})")
        print(f"      {status}: {result['reason']}")
        print()


# ---------------------------------------------------------------------------
# Exercise 2: VPC Planning Tool
# ---------------------------------------------------------------------------

def plan_vpc_layout(environments, services_per_env, base_network="10.0.0.0/8"):
    """
    Given a list of environments and number of services per environment,
    recommend a VPC CIDR layout with non-overlapping ranges.

    Each environment gets its own /16 VPC.
    Each service within an environment gets a /24 subnet.

    Args:
        environments: list of environment names (e.g., ["dev", "staging", "prod"])
        services_per_env: number of services/subnets per environment
        base_network: the RFC 1918 range to allocate from

    Returns:
        list of dicts with environment, vpc_cidr, and subnet allocations
    """
    base = ipaddress.IPv4Network(base_network)
    # Carve /16 blocks from the base network
    vpc_blocks = list(base.subnets(new_prefix=16))

    layout = []
    for i, env in enumerate(environments):
        if i >= len(vpc_blocks):
            raise ValueError(
                f"Not enough /16 blocks in {base_network} for {len(environments)} environments. "
                f"Available: {len(vpc_blocks)}, Requested: {len(environments)}."
            )
        vpc_cidr = vpc_blocks[i]
        # Carve /24 subnets from the /16 VPC
        subnets_available = list(vpc_cidr.subnets(new_prefix=24))

        env_subnets = []
        for j in range(services_per_env):
            if j < len(subnets_available):
                env_subnets.append(subnets_available[j])

        layout.append(
            {
                "environment": env,
                "vpc_cidr": str(vpc_cidr),
                "vpc_range": f"{vpc_cidr.network_address} - {vpc_cidr.broadcast_address}",
                "total_addresses": vpc_cidr.num_addresses,
                "subnets": [str(s) for s in env_subnets],
            }
        )

    return layout


def exercise_2():
    """Plan a multi-environment VPC layout."""
    print("=" * 70)
    print("EXERCISE 2: VPC Planning Tool")
    print("=" * 70)
    print()
    print("Scenario: You are setting up AWS infrastructure for a data platform.")
    print("You need 3 environments (dev, staging, prod) with 6 subnets each:")
    print("  - 3 public subnets (one per AZ: NAT gateways, bastion, ALB)")
    print("  - 3 private subnets (one per AZ: RDS, Redshift, EMR, Glue)")
    print()

    environments = ["dev", "staging", "prod"]
    services_per_env = 6  # 3 public + 3 private across 3 AZs

    layout = plan_vpc_layout(environments, services_per_env)

    for env_info in layout:
        print(f"  Environment: {env_info['environment'].upper()}")
        print(f"  VPC CIDR:    {env_info['vpc_cidr']}")
        print(f"  Range:       {env_info['vpc_range']}")
        print(f"  Addresses:   {env_info['total_addresses']:,}")
        print(f"  Subnets ({len(env_info['subnets'])}):")
        labels = [
            "Public  (AZ-a)", "Public  (AZ-b)", "Public  (AZ-c)",
            "Private (AZ-a)", "Private (AZ-b)", "Private (AZ-c)",
        ]
        for j, subnet in enumerate(env_info["subnets"]):
            net = ipaddress.IPv4Network(subnet)
            usable = net.num_addresses - 5  # AWS reserves 5
            label = labels[j] if j < len(labels) else f"Subnet {j+1}"
            print(f"    {label:17s}  {subnet:18s}  ({usable} usable IPs)")
        print()

    # Show that ranges do not overlap
    print("  Overlap check: ", end="")
    all_cidrs = [env_info["vpc_cidr"] for env_info in layout]
    overlaps = detect_overlaps(all_cidrs)
    if not overlaps:
        print("No overlaps detected. These VPCs can be peered safely.")
    else:
        for a, b in overlaps:
            print(f"    OVERLAP: {a} and {b}")
    print()


# ---------------------------------------------------------------------------
# Exercise 3: CIDR Overlap Detector
# ---------------------------------------------------------------------------

def detect_overlaps(cidr_list):
    """
    Given a list of CIDR strings, check if any two overlap.
    Returns a list of (cidr_a, cidr_b) tuples that overlap.

    Two CIDRs overlap if one is a subnet of the other, or they share any
    addresses. We check this using the ipaddress module's overlap detection.
    """
    networks = []
    for cidr_str in cidr_list:
        try:
            networks.append(ipaddress.IPv4Network(cidr_str, strict=True))
        except ValueError:
            # Try with strict=False to handle host bits
            networks.append(ipaddress.IPv4Network(cidr_str, strict=False))

    overlaps = []
    for i in range(len(networks)):
        for j in range(i + 1, len(networks)):
            if networks[i].overlaps(networks[j]):
                overlaps.append((str(networks[i]), str(networks[j])))

    return overlaps


def exercise_3():
    """Detect overlapping VPC CIDRs."""
    print("=" * 70)
    print("EXERCISE 3: CIDR Overlap Detector")
    print("=" * 70)
    print()
    print("When you peer VPCs or connect them via Transit Gateway, their CIDR")
    print("blocks MUST NOT overlap. Let's check some scenarios.")
    print()

    # Scenario 1: Good layout -- no overlaps
    print("  Scenario 1: Well-planned layout")
    cidrs_good = ["10.0.0.0/16", "10.1.0.0/16", "10.2.0.0/16"]
    print(f"    VPCs: {', '.join(cidrs_good)}")
    overlaps = detect_overlaps(cidrs_good)
    if not overlaps:
        print("    Result: No overlaps. These VPCs can be peered.")
    print()

    # Scenario 2: Identical CIDRs -- definite overlap
    print("  Scenario 2: Copy-pasted CIDR (common mistake)")
    cidrs_bad = ["10.0.0.0/16", "10.0.0.0/16", "10.2.0.0/16"]
    print(f"    VPCs: {', '.join(cidrs_bad)}")
    overlaps = detect_overlaps(cidrs_bad)
    for a, b in overlaps:
        print(f"    OVERLAP: {a} and {b} -- cannot be peered!")
    print()

    # Scenario 3: Partial overlap -- one is a superset
    print("  Scenario 3: Partial overlap (superset/subset)")
    cidrs_partial = ["10.0.0.0/8", "10.0.0.0/16", "172.16.0.0/16"]
    print(f"    VPCs: {', '.join(cidrs_partial)}")
    overlaps = detect_overlaps(cidrs_partial)
    for a, b in overlaps:
        print(f"    OVERLAP: {a} contains {b} (or vice versa) -- cannot be peered!")
    print()

    # Scenario 4: Tricky near-miss
    print("  Scenario 4: Adjacent but non-overlapping (this is fine)")
    cidrs_adjacent = ["10.0.0.0/24", "10.0.1.0/24", "10.0.2.0/24"]
    print(f"    VPCs: {', '.join(cidrs_adjacent)}")
    overlaps = detect_overlaps(cidrs_adjacent)
    if not overlaps:
        print("    Result: No overlaps. Adjacent CIDRs are fine -- they share a boundary but no addresses.")
    print()

    # Scenario 5: Real-world mess with on-prem
    print("  Scenario 5: Real-world -- VPCs + on-prem network")
    cidrs_real = [
        "10.0.0.0/16",       # Prod VPC
        "10.1.0.0/16",       # Dev VPC
        "10.2.0.0/16",       # Staging VPC
        "10.0.0.0/8",        # On-prem network (overlaps with all VPCs!)
        "172.16.0.0/16",     # Shared services VPC
    ]
    print(f"    Networks:")
    labels = ["Prod VPC", "Dev VPC", "Staging VPC", "On-prem", "Shared Svc VPC"]
    for cidr, label in zip(cidrs_real, labels):
        print(f"      {label:20s} {cidr}")
    overlaps = detect_overlaps(cidrs_real)
    if overlaps:
        print(f"    Found {len(overlaps)} overlap(s):")
        for a, b in overlaps:
            print(f"      OVERLAP: {a} <-> {b}")
        print("    Fix: Use non-overlapping ranges, e.g., 10.100.0.0/16 for on-prem.")
    print()


# ---------------------------------------------------------------------------
# Exercise 4: Visual VPC Layout
# ---------------------------------------------------------------------------

def print_vpc_layout(layout):
    """
    Print an ASCII diagram of a planned VPC layout.
    Shows each environment's VPC with its subnets.
    """
    print("=" * 70)
    print("EXERCISE 4: Visual VPC Layout")
    print("=" * 70)
    print()

    border = "+" + "-" * 66 + "+"

    for env_info in layout:
        env = env_info["environment"].upper()
        vpc = env_info["vpc_cidr"]

        print(border)
        print(f"|  VPC: {env:8s}  CIDR: {vpc:18s}                            |")
        print(f"|  Range: {env_info['vpc_range']:55s} |")
        print("|" + "-" * 66 + "|")

        subnets = env_info["subnets"]
        az_labels = ["AZ-a", "AZ-b", "AZ-c"]

        # Group subnets: first 3 are public, next 3 are private
        public_subnets = subnets[:3]
        private_subnets = subnets[3:6]

        # Print public subnets row
        print("|                                                                  |")
        print("|  PUBLIC SUBNETS (route 0.0.0.0/0 -> IGW)                         |")
        for i, s in enumerate(public_subnets):
            net = ipaddress.IPv4Network(s)
            usable = net.num_addresses - 5
            az = az_labels[i] if i < len(az_labels) else f"AZ-{i}"
            line = f"|    [{az}] {s:18s}  ({usable:>3d} usable IPs)"
            print(f"{line:<67s}|")

        print("|                                                                  |")
        print("|  PRIVATE SUBNETS (route 0.0.0.0/0 -> NAT GW)                    |")
        for i, s in enumerate(private_subnets):
            net = ipaddress.IPv4Network(s)
            usable = net.num_addresses - 5
            az = az_labels[i] if i < len(az_labels) else f"AZ-{i}"
            line = f"|    [{az}] {s:18s}  ({usable:>3d} usable IPs)"
            print(f"{line:<67s}|")

        print("|                                                                  |")
        print(border)
        print()

    # Print the connectivity summary
    print("  CONNECTIVITY DIAGRAM:")
    print()
    print("           Internet")
    print("              |")
    print("       [Internet Gateway]")
    print("              |")
    print("     +--------+--------+")
    print("     |                 |")
    print("  [Public           [Public")
    print("   Subnets]          Subnets]")
    print("     |                 |")
    print("  [NAT GW]         [NAT GW]")
    print("     |                 |")
    print("  [Private          [Private")
    print("   Subnets]          Subnets]")
    print("   (RDS, EMR,        (RDS, EMR,")
    print("    Redshift,         Redshift,")
    print("    Glue)             Glue)")
    print()


def exercise_4():
    """Print a visual layout of a planned VPC."""
    environments = ["dev", "staging", "prod"]
    services_per_env = 6
    layout = plan_vpc_layout(environments, services_per_env)
    print_vpc_layout(layout)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("*" * 70)
    print("  Module 10: VPC CIDR Planning Simulator")
    print("  AWS VPC Fundamentals -- Hands-on Exercises")
    print("*" * 70)
    print()
    print("These exercises simulate AWS VPC CIDR planning in pure Python.")
    print("No AWS account or SDK needed -- we model the concepts locally.")
    print()

    exercise_1()
    exercise_2()
    exercise_3()
    exercise_4()

    print("=" * 70)
    print("KEY LESSONS:")
    print("=" * 70)
    print()
    print("  1. VPC CIDRs must be /16 to /28 and use RFC 1918 private ranges.")
    print("  2. Plan non-overlapping CIDRs across environments BEFORE creating VPCs.")
    print("  3. Overlapping CIDRs prevent VPC peering and VPN connections.")
    print("  4. Size your VPCs generously (/16) -- you can always subdivide.")
    print("  5. Assign subnets across multiple AZs for high availability.")
    print()


if __name__ == "__main__":
    main()
