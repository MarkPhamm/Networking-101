#!/usr/bin/env python3
"""
Module 11: Subnet and Route Table Simulator

Exercises:
  1. Design a multi-AZ subnet layout from a /16 VPC
  2. Route table simulator -- walk through route matching for a given destination
  3. Calculate usable IPs per subnet (minus 5 AWS-reserved)
  4. Print an ASCII diagram of the subnet layout

Run: python3 exercises.py
No external dependencies required.
"""

import ipaddress


# ---------------------------------------------------------------------------
# Exercise 1: Multi-AZ Subnet Layout Designer
# ---------------------------------------------------------------------------

def design_subnet_layout(vpc_cidr_str, num_azs=3):
    """
    Given a VPC CIDR (/16), design a multi-AZ subnet layout with both
    public and private subnets in each AZ.

    Strategy:
    - Public subnets use /24 blocks starting from the low end
      (e.g., 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24)
    - Private subnets use /24 blocks starting from a higher offset
      (e.g., 10.0.10.0/24, 10.0.20.0/24, 10.0.30.0/24)
    - This leaves room for future subnets between them

    Returns a dict describing the layout.
    """
    vpc = ipaddress.IPv4Network(vpc_cidr_str, strict=True)
    base_octets = str(vpc.network_address).split(".")
    first_two = f"{base_octets[0]}.{base_octets[1]}"

    az_letters = [chr(ord("a") + i) for i in range(num_azs)]

    layout = {
        "vpc_cidr": vpc_cidr_str,
        "vpc_range": f"{vpc.network_address} - {vpc.broadcast_address}",
        "total_addresses": vpc.num_addresses,
        "azs": [],
    }

    for i, az_letter in enumerate(az_letters):
        public_cidr = f"{first_two}.{i + 1}.0/24"
        private_cidr = f"{first_two}.{(i + 1) * 10}.0/24"

        pub_net = ipaddress.IPv4Network(public_cidr)
        priv_net = ipaddress.IPv4Network(private_cidr)

        layout["azs"].append(
            {
                "az_name": f"us-east-1{az_letter}",
                "public_subnet": {
                    "cidr": public_cidr,
                    "range": f"{pub_net.network_address} - {pub_net.broadcast_address}",
                    "total_ips": pub_net.num_addresses,
                    "usable_ips": pub_net.num_addresses - 5,
                    "purpose": "NAT Gateway, Bastion Host, ALB",
                },
                "private_subnet": {
                    "cidr": private_cidr,
                    "range": f"{priv_net.network_address} - {priv_net.broadcast_address}",
                    "total_ips": priv_net.num_addresses,
                    "usable_ips": priv_net.num_addresses - 5,
                    "purpose": "RDS, Redshift, EMR, Glue",
                },
            }
        )

    return layout


def exercise_1():
    """Design a multi-AZ subnet layout."""
    print("=" * 70)
    print("EXERCISE 1: Multi-AZ Subnet Layout Designer")
    print("=" * 70)
    print()
    print("Given a VPC with CIDR 10.0.0.0/16, design a production-ready")
    print("subnet layout with public and private subnets across 3 AZs.")
    print()

    layout = design_subnet_layout("10.0.0.0/16", num_azs=3)

    print(f"  VPC CIDR:  {layout['vpc_cidr']}")
    print(f"  Range:     {layout['vpc_range']}")
    print(f"  Total IPs: {layout['total_addresses']:,}")
    print()

    for az_info in layout["azs"]:
        print(f"  AZ: {az_info['az_name']}")
        pub = az_info["public_subnet"]
        priv = az_info["private_subnet"]
        print(f"    Public  subnet: {pub['cidr']:18s}  "
              f"({pub['usable_ips']} usable)  Purpose: {pub['purpose']}")
        print(f"    Private subnet: {priv['cidr']:18s}  "
              f"({priv['usable_ips']} usable)  Purpose: {priv['purpose']}")
        print()

    # Show what is left over
    allocated = len(layout["azs"]) * 2  # 2 subnets per AZ
    total_24s = 256  # A /16 has 256 /24 subnets
    print(f"  Subnets allocated: {allocated} x /24")
    print(f"  Remaining /24 blocks in VPC: {total_24s - allocated}")
    print(f"  Plenty of room for future subnets (databases, caches, etc.)")
    print()


# ---------------------------------------------------------------------------
# Exercise 2: Route Table Simulator
# ---------------------------------------------------------------------------

class RouteTable:
    """
    Simulates an AWS VPC route table.

    Each route has:
    - destination: CIDR block (e.g., "10.0.0.0/16")
    - target: where to send traffic (e.g., "local", "igw-abc123", "nat-xyz789")
    - description: human-readable label
    """

    def __init__(self, name):
        self.name = name
        self.routes = []

    def add_route(self, destination, target, description=""):
        self.routes.append(
            {
                "destination": ipaddress.IPv4Network(destination),
                "target": target,
                "description": description,
            }
        )

    def lookup(self, dest_ip_str):
        """
        Find the best matching route for a destination IP.
        Uses longest prefix match (most specific route wins).
        Returns the matching route or None.
        """
        dest_ip = ipaddress.IPv4Address(dest_ip_str)
        best_match = None
        best_prefix = -1

        for route in self.routes:
            if dest_ip in route["destination"]:
                if route["destination"].prefixlen > best_prefix:
                    best_match = route
                    best_prefix = route["destination"].prefixlen

        return best_match

    def print_table(self):
        print(f"  Route Table: {self.name}")
        print(f"  {'Destination':<20s} {'Target':<20s} {'Description'}")
        print(f"  {'-'*20} {'-'*20} {'-'*30}")
        for route in sorted(self.routes, key=lambda r: r["destination"].prefixlen):
            print(
                f"  {str(route['destination']):<20s} "
                f"{route['target']:<20s} "
                f"{route['description']}"
            )
        print()


def exercise_2():
    """Simulate route table lookups."""
    print("=" * 70)
    print("EXERCISE 2: Route Table Simulator")
    print("=" * 70)
    print()
    print("AWS route tables use longest prefix match -- the most specific")
    print("route wins. Let's simulate this for public and private subnets.")
    print()

    # Public subnet route table
    public_rt = RouteTable("Public-Subnet-RT")
    public_rt.add_route("10.0.0.0/16", "local", "VPC internal traffic")
    public_rt.add_route("0.0.0.0/0", "igw-abc12345", "Internet via IGW")
    public_rt.add_route("172.16.0.0/16", "pcx-peer01", "Peered VPC (shared services)")

    # Private subnet route table
    private_rt = RouteTable("Private-Subnet-RT")
    private_rt.add_route("10.0.0.0/16", "local", "VPC internal traffic")
    private_rt.add_route("0.0.0.0/0", "nat-xyz78901", "Internet via NAT Gateway")
    private_rt.add_route("172.16.0.0/16", "pcx-peer01", "Peered VPC (shared services)")
    private_rt.add_route("10.0.20.0/24", "local", "Direct to private subnet (more specific)")

    print("  --- Public Subnet ---")
    public_rt.print_table()

    print("  --- Private Subnet ---")
    private_rt.print_table()

    # Test lookups
    test_cases = [
        ("10.0.10.50", "public", "Airflow (public subnet) -> RDS (10.0.10.50 in VPC)"),
        ("8.8.8.8", "public", "Airflow (public subnet) -> Google DNS (internet)"),
        ("172.16.5.100", "public", "Airflow (public subnet) -> shared services VPC"),
        ("10.0.20.100", "private", "EMR (private subnet) -> Redshift (10.0.20.100, specific /24 route)"),
        ("10.0.10.50", "private", "EMR (private subnet) -> RDS (10.0.10.50 in VPC)"),
        ("8.8.8.8", "private", "EMR (private subnet) -> Google DNS (via NAT)"),
        ("203.0.113.50", "private", "EMR (private subnet) -> external API (via NAT)"),
    ]

    print("  ROUTE LOOKUPS:")
    print()
    for dest_ip, subnet_type, scenario in test_cases:
        rt = public_rt if subnet_type == "public" else private_rt
        match = rt.lookup(dest_ip)
        if match:
            print(f"  Scenario: {scenario}")
            print(f"    Destination: {dest_ip}")
            print(f"    Route table: {rt.name}")
            print(f"    Matched:     {match['destination']} -> {match['target']}")
            print(f"    Reason:      {match['description']}")

            # Explain the routing decision
            if match["target"] == "local":
                print(f"    Action:      Deliver within VPC (no gateway needed)")
            elif match["target"].startswith("igw-"):
                print(f"    Action:      Send to Internet Gateway -> internet")
            elif match["target"].startswith("nat-"):
                print(f"    Action:      Send to NAT Gateway -> internet (outbound only)")
            elif match["target"].startswith("pcx-"):
                print(f"    Action:      Send to VPC Peering Connection -> peered VPC")
        else:
            print(f"  Scenario: {scenario}")
            print(f"    Destination: {dest_ip}")
            print(f"    Result:      NO MATCHING ROUTE -- packet dropped (blackhole)")
        print()


# ---------------------------------------------------------------------------
# Exercise 3: Usable IP Calculator
# ---------------------------------------------------------------------------

def calculate_usable_ips(cidr_str):
    """
    Calculate usable IPs in an AWS subnet.
    AWS reserves 5 IPs in every subnet:
    - First IP: Network address
    - Second IP: VPC router
    - Third IP: DNS server
    - Fourth IP: Reserved for future use
    - Last IP: Broadcast address
    """
    network = ipaddress.IPv4Network(cidr_str, strict=True)
    total = network.num_addresses
    reserved = 5
    usable = max(0, total - reserved)

    reserved_ips = []
    hosts = list(network.hosts())
    all_addrs = list(network)

    if len(all_addrs) >= 5:
        reserved_ips = [
            (str(all_addrs[0]), "Network address"),
            (str(all_addrs[1]), "VPC router"),
            (str(all_addrs[2]), "DNS server"),
            (str(all_addrs[3]), "Reserved for future use"),
            (str(all_addrs[-1]), "Broadcast address"),
        ]

    return {
        "cidr": cidr_str,
        "total_addresses": total,
        "aws_reserved": reserved,
        "usable_ips": usable,
        "reserved_details": reserved_ips,
        "first_usable": str(all_addrs[4]) if len(all_addrs) > 4 else "N/A",
        "last_usable": str(all_addrs[-2]) if len(all_addrs) > 2 else "N/A",
    }


def exercise_3():
    """Calculate usable IPs for various subnet sizes."""
    print("=" * 70)
    print("EXERCISE 3: Usable IP Calculator")
    print("=" * 70)
    print()
    print("AWS reserves 5 IPs in every subnet. This matters when sizing")
    print("subnets for services like EMR and Lambda that need many IPs.")
    print()

    subnets = [
        ("10.0.1.0/24", "Standard subnet"),
        ("10.0.2.0/25", "Half-size subnet"),
        ("10.0.3.0/26", "Quarter-size subnet"),
        ("10.0.4.0/27", "Small subnet"),
        ("10.0.5.0/28", "Minimum AWS subnet"),
    ]

    print(f"  {'CIDR':<18s} {'Total':<8s} {'Reserved':<10s} {'Usable':<8s} "
          f"{'First Usable':<16s} {'Last Usable':<16s} Note")
    print(f"  {'-'*18} {'-'*8} {'-'*10} {'-'*8} {'-'*16} {'-'*16} {'-'*20}")

    for cidr, note in subnets:
        info = calculate_usable_ips(cidr)
        print(
            f"  {info['cidr']:<18s} "
            f"{info['total_addresses']:<8d} "
            f"{info['aws_reserved']:<10d} "
            f"{info['usable_ips']:<8d} "
            f"{info['first_usable']:<16s} "
            f"{info['last_usable']:<16s} "
            f"{note}"
        )

    print()
    print("  Detailed breakdown for 10.0.1.0/24:")
    info = calculate_usable_ips("10.0.1.0/24")
    for ip, purpose in info["reserved_details"]:
        print(f"    {ip:<16s}  RESERVED -- {purpose}")
    print(f"    {info['first_usable']:<16s}  First assignable IP")
    print(f"    ...              (247 more usable IPs)")
    print(f"    {info['last_usable']:<16s}  Last assignable IP")
    print()

    # Practical sizing scenarios
    print("  PRACTICAL SIZING:")
    print()
    scenarios = [
        ("EMR cluster with 50 nodes", 50, "Need at least a /26 (59 usable)"),
        ("Lambda (100 concurrent executions)", 100, "Need at least a /25 (123 usable)"),
        ("RDS Multi-AZ (2 instances)", 2, "A /28 (11 usable) is sufficient"),
        ("EKS cluster (20 pods per node, 10 nodes)", 200, "Need at least a /24 (251 usable)"),
        ("Glue (10 DPUs, 1 ENI each)", 10, "A /28 (11 usable) is tight but works"),
    ]

    print(f"  {'Scenario':<45s} {'IPs Needed':<12s} Recommendation")
    print(f"  {'-'*45} {'-'*12} {'-'*40}")
    for scenario, ips_needed, recommendation in scenarios:
        print(f"  {scenario:<45s} {ips_needed:<12d} {recommendation}")
    print()


# ---------------------------------------------------------------------------
# Exercise 4: ASCII Subnet Diagram
# ---------------------------------------------------------------------------

def exercise_4():
    """Print an ASCII diagram of the subnet layout."""
    print("=" * 70)
    print("EXERCISE 4: ASCII Subnet Layout Diagram")
    print("=" * 70)
    print()

    layout = design_subnet_layout("10.0.0.0/16", num_azs=3)

    # Draw the diagram
    w = 68  # inner width
    border = "+" + "=" * w + "+"

    print(border)
    print(f"|{'VPC: 10.0.0.0/16 (65,536 addresses)':^{w}}|")
    print(f"|{'Region: us-east-1':^{w}}|")
    print("+" + "-" * w + "+")

    # Internet Gateway
    print(f"|{'':^{w}}|")
    print(f"|{'[ Internet ]':^{w}}|")
    print(f"|{'|':^{w}}|")
    print(f"|{'[ Internet Gateway: igw-abc12345 ]':^{w}}|")
    print(f"|{'|':^{w}}|")
    igw_line = "|" + " " * 12 + "+" + "-" * 12 + "+" + "-" * 14 + "+" + "-" * 12 + "+" + " " * 14 + "|"
    print(igw_line)
    print(f"|{'|               |              |':^{w}}|")

    # Public subnets
    print("+" + "-" * w + "+")
    print(f"|  {'PUBLIC SUBNETS (route: 0.0.0.0/0 -> igw-abc12345)':<{w-2}}|")
    print("|" + "-" * w + "|")

    az_data = layout["azs"]
    # Print public subnet boxes side by side
    box_w = 20
    pad = 2

    # Top borders
    line = "|  "
    for az in az_data:
        line += "+" + "-" * box_w + "+  "
    line = f"{line:<{w+1}}|"
    print(line)

    # AZ names
    line = "|  "
    for az in az_data:
        name = az["az_name"][-2:]  # "1a", "1b", "1c"
        line += f"|{'AZ-' + name:^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    # CIDRs
    line = "|  "
    for az in az_data:
        cidr = az["public_subnet"]["cidr"]
        line += f"|{cidr:^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    # Usable IPs
    line = "|  "
    for az in az_data:
        usable = f"{az['public_subnet']['usable_ips']} usable"
        line += f"|{usable:^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    # Purpose
    line = "|  "
    for az in az_data:
        line += f"|{'Bastion, NAT GW':^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    # Bottom borders
    line = "|  "
    for az in az_data:
        line += "+" + "-" * box_w + "+  "
    line = f"{line:<{w+1}}|"
    print(line)

    # NAT GW arrows
    line = "|  "
    for az in az_data:
        line += f"|{'[NAT GW]':^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    line = "|  "
    for az in az_data:
        line += f"{'|':^{box_w+2}}  "
    line = f"{line:<{w+1}}|"
    print(line)

    # Private subnets
    print("+" + "-" * w + "+")
    print(f"|  {'PRIVATE SUBNETS (route: 0.0.0.0/0 -> nat-xxxxx)':<{w-2}}|")
    print("|" + "-" * w + "|")

    # Top borders
    line = "|  "
    for az in az_data:
        line += "+" + "-" * box_w + "+  "
    line = f"{line:<{w+1}}|"
    print(line)

    # AZ names
    line = "|  "
    for az in az_data:
        name = az["az_name"][-2:]
        line += f"|{'AZ-' + name:^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    # CIDRs
    line = "|  "
    for az in az_data:
        cidr = az["private_subnet"]["cidr"]
        line += f"|{cidr:^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    # Usable IPs
    line = "|  "
    for az in az_data:
        usable = f"{az['private_subnet']['usable_ips']} usable"
        line += f"|{usable:^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    # Purpose
    line = "|  "
    for az in az_data:
        line += f"|{'RDS, Redshift':^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    line = "|  "
    for az in az_data:
        line += f"|{'EMR, Glue':^{box_w}}|  "
    line = f"{line:<{w+1}}|"
    print(line)

    # Bottom borders
    line = "|  "
    for az in az_data:
        line += "+" + "-" * box_w + "+  "
    line = f"{line:<{w+1}}|"
    print(line)

    print(f"|{'':^{w}}|")
    print(border)
    print()

    # Route table summary
    print("  ROUTE TABLE SUMMARY:")
    print()
    print("  Public Subnet Route Table:")
    print("    Destination        Target              Note")
    print("    10.0.0.0/16        local               VPC internal traffic")
    print("    0.0.0.0/0          igw-abc12345        Internet via IGW")
    print()
    print("  Private Subnet Route Table:")
    print("    Destination        Target              Note")
    print("    10.0.0.0/16        local               VPC internal traffic")
    print("    0.0.0.0/0          nat-xyz78901        Internet via NAT (outbound only)")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("*" * 70)
    print("  Module 11: Subnet and Route Table Simulator")
    print("  AWS Subnets and Routing -- Hands-on Exercises")
    print("*" * 70)
    print()
    print("These exercises simulate AWS subnet design and route table")
    print("lookups in pure Python. No AWS account or SDK needed.")
    print()

    exercise_1()
    exercise_2()
    exercise_3()
    exercise_4()

    print("=" * 70)
    print("KEY LESSONS:")
    print("=" * 70)
    print()
    print("  1. Public subnets route 0.0.0.0/0 to an IGW. Private subnets")
    print("     route 0.0.0.0/0 to a NAT Gateway.")
    print("  2. AWS reserves 5 IPs per subnet. A /24 gives 251 usable IPs.")
    print("  3. Route tables use longest prefix match (most specific wins).")
    print("  4. Spread subnets across multiple AZs for high availability.")
    print("  5. Size subnets generously -- EMR, Lambda, and Glue eat IPs fast.")
    print("  6. The 'local' route for VPC traffic is always present and cannot")
    print("     be removed.")
    print()


if __name__ == "__main__":
    main()
