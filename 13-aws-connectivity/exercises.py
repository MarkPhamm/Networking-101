#!/usr/bin/env python3
"""
Module 13: AWS Connectivity -- Python Exercises

Run with: python3 exercises.py

Covers:
  - Connectivity decision tree: answer architecture questions, get recommendations
  - VPC peering relationship modeler: validate CIDRs and show non-transitive limits
  - Cost comparison calculator: NAT Gateway vs VPC endpoints for S3 access
"""

import ipaddress


# ---------------------------------------------------------------------------
# Exercise 1: Connectivity Decision Tree
# ---------------------------------------------------------------------------

def recommend_connectivity(
    num_vpcs: int,
    needs_s3_access: bool,
    needs_onprem: bool,
    data_volume_gb_per_day: int,
    needs_transitive: bool,
    latency_sensitive: bool,
) -> dict:
    """
    Given architecture requirements, recommend connectivity options.

    Returns a dict with:
      - "vpc_connectivity": recommended VPC-to-VPC connectivity
      - "s3_access": recommended S3 access method
      - "onprem_connectivity": recommended on-prem connectivity (or None)
      - "reasoning": list of explanation strings
    """
    result = {
        "vpc_connectivity": None,
        "s3_access": None,
        "onprem_connectivity": None,
        "reasoning": [],
    }

    # --- VPC-to-VPC connectivity ---
    if num_vpcs <= 1:
        result["vpc_connectivity"] = "None needed (single VPC)"
        result["reasoning"].append(
            "With only one VPC, no inter-VPC connectivity is required."
        )
    elif num_vpcs <= 3 and not needs_transitive:
        result["vpc_connectivity"] = "VPC Peering"
        connections = num_vpcs * (num_vpcs - 1) // 2
        result["reasoning"].append(
            f"With {num_vpcs} VPCs and no transitive routing needed, "
            f"VPC Peering is simplest ({connections} peering connections). "
            f"It's free (data transfer only) and has the lowest latency."
        )
    else:
        result["vpc_connectivity"] = "Transit Gateway"
        if needs_transitive:
            result["reasoning"].append(
                f"Transitive routing required -- Transit Gateway is the only "
                f"option that supports this. All {num_vpcs} VPCs connect to "
                f"the TGW hub and can reach each other."
            )
        else:
            connections = num_vpcs * (num_vpcs - 1) // 2
            result["reasoning"].append(
                f"With {num_vpcs} VPCs, full-mesh peering would require "
                f"{connections} connections. Transit Gateway simplifies this "
                f"to {num_vpcs} attachments with centralized routing."
            )

    # --- S3 access ---
    if needs_s3_access:
        result["s3_access"] = "S3 Gateway Endpoint (FREE)"
        result["reasoning"].append(
            "S3 Gateway Endpoint is always the right answer for S3 access "
            "from within a VPC. It costs nothing, adds a route table entry, "
            "and keeps traffic on the AWS backbone. Without it, traffic "
            "goes through a NAT Gateway at $0.045/GB."
        )
    else:
        result["s3_access"] = "None needed"
        result["reasoning"].append("No S3 access required from VPC.")

    # --- On-prem connectivity ---
    if needs_onprem:
        if data_volume_gb_per_day > 500 or latency_sensitive:
            result["onprem_connectivity"] = "Direct Connect"
            reasons = []
            if data_volume_gb_per_day > 500:
                reasons.append(
                    f"high data volume ({data_volume_gb_per_day} GB/day)"
                )
            if latency_sensitive:
                reasons.append("latency sensitivity")
            result["reasoning"].append(
                f"Direct Connect recommended due to: {', '.join(reasons)}. "
                f"Provides dedicated bandwidth (1-100 Gbps) and consistent "
                f"latency. Takes weeks to provision -- use VPN as interim."
            )
        else:
            result["onprem_connectivity"] = "Site-to-Site VPN"
            result["reasoning"].append(
                f"Site-to-Site VPN is sufficient for {data_volume_gb_per_day} "
                f"GB/day with no strict latency requirements. Sets up in "
                f"minutes, provides encrypted IPsec tunnels over the internet, "
                f"and supports up to 1.25 Gbps per tunnel."
            )
    else:
        result["onprem_connectivity"] = "None needed"
        result["reasoning"].append("No on-premises connectivity required.")

    return result


def exercise_1() -> None:
    print("=" * 70)
    print("EXERCISE 1: Connectivity Decision Tree")
    print("=" * 70)
    print()
    print("Given architecture requirements, the decision tree recommends")
    print("the right connectivity options. This models the thought process")
    print("you should go through when designing a new data platform.")
    print()

    scenarios = [
        {
            "name": "Startup Data Team",
            "description": "Single VPC, Redshift + Airflow + S3, no on-prem",
            "params": {
                "num_vpcs": 1,
                "needs_s3_access": True,
                "needs_onprem": False,
                "data_volume_gb_per_day": 50,
                "needs_transitive": False,
                "latency_sensitive": False,
            },
        },
        {
            "name": "Growing Team with Staging",
            "description": "Prod + Staging VPCs, S3 data lake, no on-prem",
            "params": {
                "num_vpcs": 2,
                "needs_s3_access": True,
                "needs_onprem": False,
                "data_volume_gb_per_day": 200,
                "needs_transitive": False,
                "latency_sensitive": False,
            },
        },
        {
            "name": "Enterprise Data Platform",
            "description": "Dev + Staging + Prod + Shared Services + Security VPCs, "
                           "S3, on-prem data warehouse migration",
            "params": {
                "num_vpcs": 5,
                "needs_s3_access": True,
                "needs_onprem": True,
                "data_volume_gb_per_day": 1000,
                "needs_transitive": True,
                "latency_sensitive": True,
            },
        },
        {
            "name": "Hybrid Batch Processing",
            "description": "2 VPCs, nightly batch from on-prem Oracle, moderate volume",
            "params": {
                "num_vpcs": 2,
                "needs_s3_access": True,
                "needs_onprem": True,
                "data_volume_gb_per_day": 100,
                "needs_transitive": False,
                "latency_sensitive": False,
            },
        },
    ]

    for scenario in scenarios:
        print(f"--- Scenario: {scenario['name']} ---")
        print(f"  {scenario['description']}")
        print()

        result = recommend_connectivity(**scenario["params"])

        print(f"  VPC Connectivity:   {result['vpc_connectivity']}")
        print(f"  S3 Access:          {result['s3_access']}")
        print(f"  On-Prem:            {result['onprem_connectivity']}")
        print()
        print("  Reasoning:")
        for i, reason in enumerate(result["reasoning"], 1):
            # Wrap long lines for readability
            words = reason.split()
            line = f"    {i}. "
            for word in words:
                if len(line) + len(word) + 1 > 72:
                    print(line)
                    line = "       " + word
                else:
                    line += (" " if not line.endswith(". ") and not line.endswith("       ") else "") + word
            print(line)
        print()


# ---------------------------------------------------------------------------
# Exercise 2: Peering Relationship Modeler
# ---------------------------------------------------------------------------

def validate_peering(vpcs: list[dict]) -> dict:
    """
    Given a list of VPCs (each with 'name' and 'cidr'), validate whether
    peering is possible between all pairs.

    Returns a dict with:
      - "valid_pairs": list of (vpc_a, vpc_b) tuples that can peer
      - "invalid_pairs": list of (vpc_a, vpc_b, reason) tuples
      - "non_transitive_gaps": list of (vpc_a, vpc_c) that can't reach
        each other transitively through vpc_b
      - "total_connections": number of peering connections needed for full mesh
    """
    networks = {}
    for vpc in vpcs:
        networks[vpc["name"]] = ipaddress.IPv4Network(vpc["cidr"], strict=False)

    valid_pairs = []
    invalid_pairs = []

    names = [vpc["name"] for vpc in vpcs]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            net_a, net_b = networks[a], networks[b]

            if net_a.overlaps(net_b):
                invalid_pairs.append(
                    (a, b, f"CIDRs overlap: {net_a} and {net_b}")
                )
            else:
                valid_pairs.append((a, b))

    # Demonstrate non-transitive limitation
    # If A peers with B and B peers with C, A still can't reach C
    non_transitive_gaps = []
    peered = set()
    for a, b in valid_pairs:
        peered.add((a, b))
        peered.add((b, a))

    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, c = names[i], names[j]
            if (a, c) not in peered:
                # Check if there's a path through an intermediate VPC
                for k in range(len(names)):
                    b = names[k]
                    if b != a and b != c:
                        if (a, b) in peered and (b, c) in peered:
                            non_transitive_gaps.append(
                                (a, c, b)
                            )

    total = len(names) * (len(names) - 1) // 2

    return {
        "valid_pairs": valid_pairs,
        "invalid_pairs": invalid_pairs,
        "non_transitive_gaps": non_transitive_gaps,
        "total_connections": total,
    }


def exercise_2() -> None:
    print("=" * 70)
    print("EXERCISE 2: VPC Peering Relationship Modeler")
    print("=" * 70)
    print()
    print("VPC Peering has two hard constraints:")
    print("  1. No overlapping CIDRs between peered VPCs")
    print("  2. Non-transitive: A<->B and B<->C does NOT mean A<->C")
    print()
    print("This modeler validates peering feasibility and highlights")
    print("the non-transitive limitation that trips up many architects.")
    print()

    # --- Test Case 1: Clean peering (no overlaps) ---
    print("--- Test Case 1: Three VPCs with unique CIDRs ---")
    vpcs_clean = [
        {"name": "Production",      "cidr": "10.0.0.0/16"},
        {"name": "Staging",          "cidr": "10.1.0.0/16"},
        {"name": "Shared-Services",  "cidr": "10.2.0.0/16"},
    ]
    for vpc in vpcs_clean:
        print(f"  {vpc['name']:20s} {vpc['cidr']}")
    print()

    result = validate_peering(vpcs_clean)
    print(f"  Total connections for full mesh: {result['total_connections']}")
    print(f"  Valid peering pairs:")
    for a, b in result["valid_pairs"]:
        print(f"    {a} <--> {b}")
    if result["invalid_pairs"]:
        print(f"  Invalid pairs:")
        for a, b, reason in result["invalid_pairs"]:
            print(f"    {a} <--> {b}: {reason}")
    else:
        print(f"  Invalid pairs: None (all CIDRs are unique)")
    print()

    # --- Test Case 2: Overlapping CIDRs ---
    print("--- Test Case 2: VPCs with CIDR overlap ---")
    vpcs_overlap = [
        {"name": "VPC-A",  "cidr": "10.0.0.0/16"},
        {"name": "VPC-B",  "cidr": "10.0.0.0/16"},   # Same as A!
        {"name": "VPC-C",  "cidr": "10.1.0.0/16"},
    ]
    for vpc in vpcs_overlap:
        print(f"  {vpc['name']:20s} {vpc['cidr']}")
    print()

    result = validate_peering(vpcs_overlap)
    print(f"  Valid peering pairs:")
    for a, b in result["valid_pairs"]:
        print(f"    {a} <--> {b}")
    print(f"  Invalid pairs (CIDR overlap):")
    for a, b, reason in result["invalid_pairs"]:
        print(f"    {a} <--> {b}: {reason}")
    print()

    # --- Test Case 3: Non-transitive demonstration ---
    print("--- Test Case 3: Non-Transitive Limitation ---")
    print()
    print("  Suppose we ONLY set up these peering connections:")
    print("    Production <--> Staging")
    print("    Staging <--> Shared-Services")
    print()
    print("  Can Production reach Shared-Services?")
    print()
    print("  Production <--> Staging <--> Shared-Services")
    print("       |                            |")
    print("       +--- NO DIRECT PEERING ------+")
    print()
    print("  Answer: NO. VPC Peering is non-transitive.")
    print("  Traffic from Production CANNOT hop through Staging")
    print("  to reach Shared-Services, even though both are peered")
    print("  with Staging.")
    print()
    print("  Solutions:")
    print("    1. Add a direct peering: Production <--> Shared-Services")
    print("    2. Use Transit Gateway instead (transitive by design)")
    print()

    # --- Test Case 4: Scaling problem ---
    print("--- Test Case 4: The Scaling Problem ---")
    print()
    print("  Full-mesh peering connections grow quadratically:")
    print()
    print(f"  {'VPCs':>6s}  {'Peering Connections':>20s}  {'Manageable?':>12s}")
    print(f"  {'─' * 6}  {'─' * 20}  {'─' * 12}")
    for n in [2, 3, 5, 10, 15, 20, 50]:
        connections = n * (n - 1) // 2
        manageable = "Yes" if connections <= 10 else ("Painful" if connections <= 50 else "No")
        print(f"  {n:>6d}  {connections:>20d}  {manageable:>12s}")
    print()
    print("  This is why Transit Gateway exists. With TGW, you need")
    print("  only N attachments instead of N*(N-1)/2 peering connections.")
    print()


# ---------------------------------------------------------------------------
# Exercise 3: Cost Comparison Calculator
# ---------------------------------------------------------------------------

# Pricing constants (us-east-1 approximate, as of 2024)
NAT_GW_HOURLY = 0.045         # per hour
NAT_GW_PER_GB = 0.045         # per GB processed
S3_GW_ENDPOINT_HOURLY = 0.0   # free
S3_GW_ENDPOINT_PER_GB = 0.0   # free
INTERFACE_ENDPOINT_HOURLY = 0.01  # per hour per AZ
INTERFACE_ENDPOINT_PER_GB = 0.01  # per GB processed
HOURS_PER_MONTH = 730


def calculate_s3_access_costs(
    monthly_gb: float,
    num_azs: int = 2,
) -> dict:
    """
    Calculate monthly costs for different S3 access methods.

    Args:
        monthly_gb: GB of data transferred to/from S3 per month
        num_azs: Number of AZs for interface endpoint (default 2)

    Returns dict with cost breakdowns for each method.
    """
    # NAT Gateway (required if no endpoint and instances are in private subnets)
    nat_gw_base = NAT_GW_HOURLY * HOURS_PER_MONTH
    nat_gw_data = NAT_GW_PER_GB * monthly_gb
    nat_gw_total = nat_gw_base + nat_gw_data

    # S3 Gateway Endpoint (free)
    gw_endpoint_total = 0.0

    # S3 Interface Endpoint (for cross-region or specific use cases)
    iface_base = INTERFACE_ENDPOINT_HOURLY * HOURS_PER_MONTH * num_azs
    iface_data = INTERFACE_ENDPOINT_PER_GB * monthly_gb
    iface_total = iface_base + iface_data

    return {
        "nat_gateway": {
            "base_cost": nat_gw_base,
            "data_cost": nat_gw_data,
            "total": nat_gw_total,
            "description": "NAT Gateway (no endpoint)",
        },
        "gateway_endpoint": {
            "base_cost": 0.0,
            "data_cost": 0.0,
            "total": gw_endpoint_total,
            "description": "S3 Gateway Endpoint (FREE)",
        },
        "interface_endpoint": {
            "base_cost": iface_base,
            "data_cost": iface_data,
            "total": iface_total,
            "description": f"S3 Interface Endpoint ({num_azs} AZs)",
        },
    }


def exercise_3() -> None:
    print("=" * 70)
    print("EXERCISE 3: S3 Access Cost Comparison Calculator")
    print("=" * 70)
    print()
    print("This is the exercise that will make you immediately go check")
    print("whether your VPCs have S3 Gateway Endpoints configured.")
    print()
    print("Without a VPC endpoint, traffic from private subnets to S3")
    print("routes through a NAT Gateway at $0.045/GB. With a Gateway")
    print("Endpoint, it's free. The math is stark.")
    print()

    data_volumes = [100, 500, 1_000, 5_000, 10_000, 50_000]

    # Print comparison table
    print(f"  {'Monthly GB':>12s}  {'NAT Gateway':>14s}  {'GW Endpoint':>14s}  "
          f"{'Interface EP':>14s}  {'Savings (GW)':>14s}")
    print(f"  {'─' * 12}  {'─' * 14}  {'─' * 14}  {'─' * 14}  {'─' * 14}")

    for gb in data_volumes:
        costs = calculate_s3_access_costs(gb, num_azs=2)
        nat = costs["nat_gateway"]["total"]
        gw = costs["gateway_endpoint"]["total"]
        iface = costs["interface_endpoint"]["total"]
        savings = nat - gw

        print(
            f"  {gb:>10,d} GB  ${nat:>12,.2f}  ${gw:>12,.2f}  "
            f"${iface:>12,.2f}  ${savings:>12,.2f}"
        )

    print()

    # Detailed breakdown for a common scenario
    print("--- Detailed Breakdown: 10 TB/month (common for Redshift COPY) ---")
    print()
    costs = calculate_s3_access_costs(10_000, num_azs=2)

    for method, details in costs.items():
        print(f"  {details['description']}:")
        print(f"    Base cost (hourly):   ${details['base_cost']:>10,.2f}/month")
        print(f"    Data processing:      ${details['data_cost']:>10,.2f}/month")
        print(f"    Total:                ${details['total']:>10,.2f}/month")
        print(f"    Annual:               ${details['total'] * 12:>10,.2f}/year")
        print()

    nat_annual = costs["nat_gateway"]["total"] * 12
    print(f"  Annual savings with S3 Gateway Endpoint vs NAT Gateway:")
    print(f"    ${nat_annual:,.2f}/year --> $0.00/year")
    print(f"    You save ${nat_annual:,.2f}/year")
    print()

    # Real-world scenario
    print("--- Real-World Scenario: Data Engineering Team ---")
    print()
    print("  Your team runs:")
    print("    - Redshift COPY jobs:    5 TB/month from S3")
    print("    - Glue ETL jobs:         3 TB/month read + 2 TB/month write")
    print("    - EMR Spark processing:  8 TB/month from S3")
    print("    - Airflow logs:          50 GB/month to CloudWatch")
    print()

    total_s3_gb = 5_000 + 3_000 + 2_000 + 8_000
    cloudwatch_gb = 50

    s3_costs = calculate_s3_access_costs(total_s3_gb)
    nat_s3 = s3_costs["nat_gateway"]["total"]

    # CloudWatch needs an interface endpoint (not available as gateway)
    cw_nat_cost = NAT_GW_PER_GB * cloudwatch_gb  # Just the data portion
    cw_iface_cost = (INTERFACE_ENDPOINT_HOURLY * HOURS_PER_MONTH * 2) + (
        INTERFACE_ENDPOINT_PER_GB * cloudwatch_gb
    )

    print(f"  Without any VPC endpoints:")
    print(f"    S3 traffic via NAT GW:         ${nat_s3:>10,.2f}/month")
    print(f"    CloudWatch via NAT GW (data):  ${cw_nat_cost:>10,.2f}/month")
    print(f"    NAT GW base cost:              ${NAT_GW_HOURLY * HOURS_PER_MONTH:>10,.2f}/month")
    total_without = nat_s3 + cw_nat_cost
    print(f"    Total:                         ${total_without:>10,.2f}/month")
    print()

    print(f"  With VPC endpoints:")
    print(f"    S3 Gateway Endpoint:           $      0.00/month (FREE)")
    print(f"    CloudWatch Interface Endpoint: ${cw_iface_cost:>10,.2f}/month")
    total_with = cw_iface_cost
    print(f"    Total:                         ${total_with:>10,.2f}/month")
    print()

    monthly_savings = total_without - total_with
    annual_savings = monthly_savings * 12
    print(f"  Monthly savings: ${monthly_savings:>10,.2f}")
    print(f"  Annual savings:  ${annual_savings:>10,.2f}")
    print()
    print("  The S3 Gateway Endpoint alone saves the vast majority of this.")
    print("  It takes about 2 minutes to set up. Do it now.")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("###################################################################")
    print("#  Module 13: AWS Connectivity -- Python Exercises               #")
    print("###################################################################")
    print()

    exercise_1()
    exercise_2()
    exercise_3()

    print("=" * 70)
    print("All exercises complete.")
    print()
    print("Key takeaways:")
    print("  - Use the decision tree: number of VPCs, data volume, and")
    print("    on-prem needs determine your connectivity options.")
    print("  - VPC Peering is simple but non-transitive and doesn't scale.")
    print("  - Transit Gateway solves the scaling and transitivity problems.")
    print("  - S3 Gateway Endpoint is free and should be in EVERY VPC.")
    print("  - NAT Gateway data processing fees are the silent budget killer")
    print("    in data engineering -- always check for VPC endpoints first.")
    print("=" * 70)


if __name__ == "__main__":
    main()
