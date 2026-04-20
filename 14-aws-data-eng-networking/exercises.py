#!/usr/bin/env python3
"""
Module 14: AWS Data Engineering Networking (Capstone) -- Python Exercises

Run with: python3 exercises.py

Covers:
  - End-to-end architecture designer: given pipeline components, produce
    a complete network design with VPC, subnets, SGs, routes, and endpoints
  - Pre-built scenarios: Basic ETL, Data Warehouse, Full Platform
  - ASCII architecture diagrams for each design
"""

import ipaddress
import textwrap


# ---------------------------------------------------------------------------
# Component Definitions
# ---------------------------------------------------------------------------

# Each component defines its networking requirements
COMPONENTS = {
    "airflow": {
        "display_name": "Airflow (MWAA)",
        "subnet_type": "private-app",
        "port": 8080,
        "protocol": "TCP",
        "needs_multi_az": True,
        "needs_self_ref_sg": True,
        "outbound_rules": [],  # Filled dynamically based on other components
        "endpoints_needed": ["s3"],
        "notes": [
            "MWAA requires 2 private subnets in different AZs",
            "Self-referencing SG rule for worker communication",
            "Needs NAT Gateway for PyPI package installs",
        ],
    },
    "rds_postgres": {
        "display_name": "RDS PostgreSQL",
        "subnet_type": "private-data",
        "port": 5432,
        "protocol": "TCP",
        "needs_multi_az": True,
        "needs_self_ref_sg": False,
        "outbound_rules": [],
        "endpoints_needed": [],
        "notes": [
            "Publicly Accessible must be set to No",
            "RDS subnet group spans 2+ AZs",
            "DNS endpoint auto-updates on failover",
        ],
    },
    "redshift": {
        "display_name": "Redshift",
        "subnet_type": "private-data",
        "port": 5439,
        "protocol": "TCP",
        "needs_multi_az": True,
        "needs_self_ref_sg": False,
        "outbound_rules": [("TCP", 443, "S3 prefix list (COPY/UNLOAD)")],
        "endpoints_needed": ["s3"],
        "notes": [
            "Enable Enhanced VPC Routing (required for VPC endpoint usage)",
            "Redshift subnet group needs subnets in 2+ AZs",
            "S3 Gateway Endpoint eliminates NAT GW fees for COPY/UNLOAD",
        ],
    },
    "s3": {
        "display_name": "S3 (via VPC Endpoint)",
        "subnet_type": None,  # S3 is not deployed in a subnet
        "port": 443,
        "protocol": "TCP",
        "needs_multi_az": False,
        "needs_self_ref_sg": False,
        "outbound_rules": [],
        "endpoints_needed": ["s3"],
        "notes": [
            "S3 Gateway Endpoint is FREE -- always configure it",
            "Associate with ALL private subnet route tables",
            "Without it, S3 traffic goes through NAT GW at $0.045/GB",
        ],
    },
    "glue": {
        "display_name": "AWS Glue",
        "subnet_type": "private-app",
        "port": None,  # Glue doesn't listen on a port; it connects outbound
        "protocol": "TCP",
        "needs_multi_az": False,
        "needs_self_ref_sg": True,
        "outbound_rules": [("TCP", 443, "S3 prefix list"), ("TCP", 443, "Glue service endpoint")],
        "endpoints_needed": ["s3", "glue", "cloudwatch_logs"],
        "notes": [
            "Glue creates ENIs in your subnet -- needs free IPs",
            "Self-referencing SG rule required (workers shuffle data)",
            "Needs VPC Connection configured for JDBC targets",
            "DNS resolution must be enabled on the VPC",
        ],
    },
    "emr": {
        "display_name": "EMR Cluster",
        "subnet_type": "private-compute",
        "port": 8088,
        "protocol": "TCP",
        "needs_multi_az": False,
        "needs_self_ref_sg": True,
        "outbound_rules": [("TCP", 443, "S3 prefix list")],
        "endpoints_needed": ["s3"],
        "notes": [
            "EMR creates managed SGs -- do not modify them",
            "Use Additional SGs for custom rules (e.g., SSH from bastion)",
            "S3 Gateway Endpoint critical for cost (TB-scale I/O)",
            "Master + Core nodes need all-port inter-node communication",
        ],
    },
}

# VPC endpoint catalog
ENDPOINTS = {
    "s3": {
        "service": "com.amazonaws.<region>.s3",
        "type": "Gateway",
        "cost": "FREE",
        "priority": "MUST HAVE",
    },
    "dynamodb": {
        "service": "com.amazonaws.<region>.dynamodb",
        "type": "Gateway",
        "cost": "FREE",
        "priority": "If needed",
    },
    "glue": {
        "service": "com.amazonaws.<region>.glue",
        "type": "Interface",
        "cost": "~$15/month",
        "priority": "If Glue uses VPC",
    },
    "cloudwatch_logs": {
        "service": "com.amazonaws.<region>.logs",
        "type": "Interface",
        "cost": "~$15/month",
        "priority": "Recommended",
    },
    "secrets_manager": {
        "service": "com.amazonaws.<region>.secretsmanager",
        "type": "Interface",
        "cost": "~$15/month",
        "priority": "If storing creds",
    },
    "kms": {
        "service": "com.amazonaws.<region>.kms",
        "type": "Interface",
        "cost": "~$15/month",
        "priority": "If encrypting",
    },
}


# ---------------------------------------------------------------------------
# Architecture Designer
# ---------------------------------------------------------------------------

def design_architecture(component_names: list[str], vpc_cidr: str = "10.0.0.0/16") -> dict:
    """
    Given a list of component names, produce a complete network design.

    Returns a dict with:
      - vpc: CIDR and settings
      - subnets: list of subnet definitions
      - security_groups: list of SG definitions with rules
      - route_tables: list of route table entries
      - endpoints: list of required VPC endpoints
      - notes: list of important configuration notes
    """
    vpc_network = ipaddress.IPv4Network(vpc_cidr, strict=False)
    components = {name: COMPONENTS[name] for name in component_names if name in COMPONENTS}

    # --- Subnets ---
    subnets = []
    subnet_index = 0

    # Always create public subnets (bastion + NAT GW)
    subnets.append({
        "name": "public-a",
        "cidr": "10.0.1.0/24",
        "az": "AZ-a",
        "type": "Public",
        "purpose": "Bastion host, NAT Gateway",
    })
    subnets.append({
        "name": "public-b",
        "cidr": "10.0.2.0/24",
        "az": "AZ-b",
        "type": "Public",
        "purpose": "NAT Gateway (HA)",
    })

    # Determine which subnet tiers are needed
    subnet_tiers = set()
    for comp in components.values():
        if comp["subnet_type"]:
            subnet_tiers.add(comp["subnet_type"])

    tier_cidrs = {
        "private-app": [("10.0.10.0/24", "AZ-a"), ("10.0.11.0/24", "AZ-b")],
        "private-data": [("10.0.20.0/24", "AZ-a"), ("10.0.21.0/24", "AZ-b")],
        "private-compute": [("10.0.30.0/24", "AZ-a"), ("10.0.31.0/24", "AZ-b")],
    }

    tier_purposes = {
        "private-app": "Application layer",
        "private-data": "Data stores",
        "private-compute": "Compute clusters",
    }

    for tier in sorted(subnet_tiers):
        cidrs = tier_cidrs[tier]
        tier_components = [
            c["display_name"] for c in components.values() if c["subnet_type"] == tier
        ]
        purpose = f"{tier_purposes[tier]} ({', '.join(tier_components)})"
        for cidr, az in cidrs:
            subnets.append({
                "name": f"{tier}-{az.lower().replace('-', '')}",
                "cidr": cidr,
                "az": az,
                "type": "Private",
                "purpose": purpose,
            })

    # --- Security Groups ---
    security_groups = []

    # Bastion SG
    security_groups.append({
        "name": "bastion-sg",
        "description": "Bastion host access",
        "inbound": [("TCP", 22, "Your IP (x.x.x.x/32)")],
        "outbound": [("All", "All", "0.0.0.0/0")],
    })

    # Component SGs
    for name, comp in components.items():
        if comp["subnet_type"] is None:
            continue

        sg = {
            "name": f"{name}-sg",
            "description": comp["display_name"],
            "inbound": [],
            "outbound": [],
        }

        # Self-referencing rules
        if comp["needs_self_ref_sg"]:
            sg["inbound"].append(("TCP", "All", f"{name}-sg (self)"))
            sg["outbound"].append(("TCP", "All", f"{name}-sg (self)"))

        # Inbound from other components (components that need to connect TO this one)
        if comp["port"]:
            for other_name, other_comp in components.items():
                if other_name == name or other_comp["subnet_type"] is None:
                    continue
                # If the other component is an "app" type, it likely connects to "data" types
                if (other_comp["subnet_type"] == "private-app"
                        and comp["subnet_type"] in ("private-data", "private-compute")):
                    sg["inbound"].append(
                        ("TCP", comp["port"], f"{other_name}-sg")
                    )
            # Bastion access
            if comp["port"] in (5432, 5439, 8088):
                sg["inbound"].append(("TCP", comp["port"], "bastion-sg (via SSH tunnel)"))
            elif name == "emr":
                sg["inbound"].append(("TCP", 22, "bastion-sg (SSH)"))

        # Static outbound rules from component definition
        for proto, port, desc in comp["outbound_rules"]:
            sg["outbound"].append((proto, port, desc))

        # Outbound to data stores
        if comp["subnet_type"] == "private-app":
            for other_name, other_comp in components.items():
                if other_comp["subnet_type"] in ("private-data",) and other_comp["port"]:
                    sg["outbound"].append(
                        ("TCP", other_comp["port"], f"{other_name}-sg")
                    )

        # Outbound HTTPS for AWS APIs
        if name in ("airflow", "glue", "emr"):
            sg["outbound"].append(("TCP", 443, "0.0.0.0/0 (AWS APIs)"))

        security_groups.append(sg)

    # --- Route Tables ---
    route_tables = [
        {
            "name": "public-rt",
            "routes": [
                ("10.0.0.0/16", "local", "VPC local traffic"),
                ("0.0.0.0/0", "igw-xxxxxxxx", "Internet access"),
            ],
        },
        {
            "name": "private-rt",
            "routes": [
                ("10.0.0.0/16", "local", "VPC local traffic"),
                ("0.0.0.0/0", "nat-xxxxxxxx", "Outbound internet via NAT"),
            ],
        },
    ]

    # --- VPC Endpoints ---
    needed_endpoints = set()
    for comp in components.values():
        for ep in comp["endpoints_needed"]:
            needed_endpoints.add(ep)

    endpoints = []
    for ep_name in sorted(needed_endpoints):
        if ep_name in ENDPOINTS:
            ep = ENDPOINTS[ep_name]
            endpoints.append({
                "name": ep_name,
                "service": ep["service"],
                "type": ep["type"],
                "cost": ep["cost"],
                "priority": ep["priority"],
            })

    # Add S3 prefix list route if S3 endpoint exists
    if "s3" in needed_endpoints:
        route_tables[1]["routes"].insert(1, (
            "pl-xxxxxxxx (S3)", "vpce-xxxxxxxx", "S3 Gateway Endpoint (FREE)"
        ))

    # --- Notes ---
    notes = []
    for comp in components.values():
        for note in comp["notes"]:
            if note not in notes:
                notes.append(note)

    return {
        "vpc": {"cidr": vpc_cidr, "dns_resolution": True, "dns_hostnames": True},
        "subnets": subnets,
        "security_groups": security_groups,
        "route_tables": route_tables,
        "endpoints": endpoints,
        "notes": notes,
        "components": components,
    }


def print_design(design: dict, scenario_name: str) -> None:
    """Pretty-print a network design."""
    print(f"  VPC: {design['vpc']['cidr']}")
    print(f"  DNS Resolution: {design['vpc']['dns_resolution']}")
    print(f"  DNS Hostnames:  {design['vpc']['dns_hostnames']}")
    print()

    # Subnets
    print("  SUBNETS:")
    print(f"  {'Name':<24s} {'CIDR':<18s} {'AZ':<8s} {'Type':<10s} Purpose")
    print(f"  {'─' * 24} {'─' * 18} {'─' * 8} {'─' * 10} {'─' * 35}")
    for s in design["subnets"]:
        print(f"  {s['name']:<24s} {s['cidr']:<18s} {s['az']:<8s} {s['type']:<10s} {s['purpose']}")
    print()

    # Security Groups
    print("  SECURITY GROUPS:")
    for sg in design["security_groups"]:
        print(f"    {sg['name']} ({sg['description']})")
        if sg["inbound"]:
            print(f"      Inbound:")
            for proto, port, source in sg["inbound"]:
                print(f"        {proto:<6s} {str(port):<8s} from {source}")
        if sg["outbound"]:
            print(f"      Outbound:")
            for proto, port, dest in sg["outbound"]:
                print(f"        {proto:<6s} {str(port):<8s} to   {dest}")
        print()

    # Route Tables
    print("  ROUTE TABLES:")
    for rt in design["route_tables"]:
        print(f"    {rt['name']}:")
        for dest, target, note in rt["routes"]:
            print(f"      {dest:<28s} → {target:<20s} ({note})")
        print()

    # VPC Endpoints
    if design["endpoints"]:
        print("  VPC ENDPOINTS:")
        print(f"  {'Service':<20s} {'Type':<12s} {'Cost':<12s} Priority")
        print(f"  {'─' * 20} {'─' * 12} {'─' * 12} {'─' * 12}")
        for ep in design["endpoints"]:
            print(f"  {ep['name']:<20s} {ep['type']:<12s} {ep['cost']:<12s} {ep['priority']}")
        print()

    # Notes
    if design["notes"]:
        print("  IMPORTANT NOTES:")
        for i, note in enumerate(design["notes"], 1):
            print(f"    {i}. {note}")
        print()


def print_ascii_diagram(component_names: list[str], scenario_name: str) -> None:
    """Print an ASCII architecture diagram for the given components."""
    has_airflow = "airflow" in component_names
    has_rds = "rds_postgres" in component_names
    has_redshift = "redshift" in component_names
    has_glue = "glue" in component_names
    has_emr = "emr" in component_names
    has_s3 = "s3" in component_names

    print(f"  ARCHITECTURE DIAGRAM: {scenario_name}")
    print()
    print("  ┌─── VPC: 10.0.0.0/16 ─────────────────────────────────────────┐")
    print("  │                                                                │")
    print("  │  ┌─ Public Subnets ─────────────────────────────────┐         │")
    print("  │  │  [Bastion]          [NAT Gateway]                │         │")
    print("  │  └──────────────────────────────────────────────────┘         │")

    # App tier
    app_components = []
    if has_airflow:
        app_components.append("Airflow/MWAA")
    if has_glue:
        app_components.append("Glue ENIs")
    if app_components:
        apps_str = "  ".join(f"[{c}]" for c in app_components)
        print("  │                                                                │")
        print("  │  ┌─ Private App Subnets ────────────────────────┐         │")
        print(f"  │  │  {apps_str:<52s}│         │")
        print("  │  └──────────────────────────────────────────────┘         │")

    # Data tier
    data_components = []
    if has_redshift:
        data_components.append("Redshift :5439")
    if has_rds:
        data_components.append("RDS PG :5432")
    if data_components:
        data_str = "  ".join(f"[{c}]" for c in data_components)
        print("  │                                                                │")
        print("  │  ┌─ Private Data Subnets ───────────────────────┐         │")
        print(f"  │  │  {data_str:<52s}│         │")
        print("  │  └──────────────────────────────────────────────┘         │")

    # Compute tier
    if has_emr:
        print("  │                                                                │")
        print("  │  ┌─ Private Compute Subnets ────────────────────┐         │")
        print("  │  │  [EMR Master]  [EMR Core]  [EMR Core]        │         │")
        print("  │  └──────────────────────────────────────────────┘         │")

    # Endpoints and S3
    if has_s3:
        print("  │                                                                │")
        print("  │  S3 Gateway Endpoint (FREE) ─── route table entry             │")
        print("  │              │                                                 │")
        print("  │         ┌────┴────┐                                           │")
        print("  │         │   S3    │                                            │")
        print("  │         └─────────┘                                           │")

    print("  └────────────────────────────────────────────────────────────────┘")
    print()


# ---------------------------------------------------------------------------
# Pre-built Scenarios
# ---------------------------------------------------------------------------

SCENARIOS = {
    "Basic ETL": {
        "description": "Simple ETL pipeline: Airflow orchestrates, RDS source, S3 data lake",
        "components": ["airflow", "rds_postgres", "s3"],
    },
    "Data Warehouse": {
        "description": "Analytical platform: Airflow orchestrates, Redshift warehouse, "
                       "Glue for ETL, S3 data lake",
        "components": ["airflow", "redshift", "s3", "glue"],
    },
    "Full Platform": {
        "description": "Enterprise data platform: everything connected",
        "components": ["airflow", "rds_postgres", "redshift", "emr", "s3", "glue"],
    },
}


# ---------------------------------------------------------------------------
# Exercises
# ---------------------------------------------------------------------------

def exercise_1() -> None:
    print("=" * 70)
    print("EXERCISE 1: Pre-Built Architecture Designs")
    print("=" * 70)
    print()
    print("Three common data engineering architectures on AWS, each with")
    print("a complete network design. These are the patterns you'll see")
    print("(and build) in production.")
    print()

    for scenario_name, scenario in SCENARIOS.items():
        print(f"{'─' * 70}")
        print(f"  SCENARIO: {scenario_name}")
        print(f"  {scenario['description']}")
        print(f"  Components: {', '.join(scenario['components'])}")
        print(f"{'─' * 70}")
        print()

        design = design_architecture(scenario["components"])
        print_ascii_diagram(scenario["components"], scenario_name)
        print_design(design, scenario_name)


def exercise_2() -> None:
    print("=" * 70)
    print("EXERCISE 2: Security Group Connectivity Matrix")
    print("=" * 70)
    print()
    print("For each scenario, this matrix shows which components can")
    print("talk to which, on what port, and why. This is the view your")
    print("security team will ask for during architecture review.")
    print()

    for scenario_name, scenario in SCENARIOS.items():
        print(f"--- {scenario_name} ---")
        print()

        components = {
            name: COMPONENTS[name]
            for name in scenario["components"]
            if name in COMPONENTS and COMPONENTS[name]["subnet_type"]
        }

        # Build connectivity matrix
        names = list(components.keys())
        print(f"  {'Source':<16s} {'Destination':<16s} {'Port':<8s} {'Purpose'}")
        print(f"  {'─' * 16} {'─' * 16} {'─' * 8} {'─' * 30}")

        for src in names:
            src_comp = components[src]
            for dst in names:
                if src == dst:
                    continue
                dst_comp = components[dst]

                # App → Data connections
                if (src_comp["subnet_type"] == "private-app"
                        and dst_comp["subnet_type"] in ("private-data", "private-compute")
                        and dst_comp["port"]):
                    purpose = f"{src_comp['display_name']} queries {dst_comp['display_name']}"
                    print(
                        f"  {src:<16s} {dst:<16s} {str(dst_comp['port']):<8s} {purpose}"
                    )

                # Glue → Data connections
                if (src == "glue"
                        and dst_comp["subnet_type"] == "private-data"
                        and dst_comp["port"]):
                    if src_comp["subnet_type"] == dst_comp["subnet_type"]:
                        continue  # Skip if already handled
                    purpose = f"Glue JDBC to {dst_comp['display_name']}"
                    print(
                        f"  {src:<16s} {dst:<16s} {str(dst_comp['port']):<8s} {purpose}"
                    )

        # S3 access
        for name in names:
            comp = components[name]
            if "s3" in comp["endpoints_needed"]:
                print(
                    f"  {name:<16s} {'s3':<16s} {'443':<8s} "
                    f"{comp['display_name']} → S3 via Gateway Endpoint"
                )

        print()


def exercise_3() -> None:
    print("=" * 70)
    print("EXERCISE 3: Cost Impact Analysis")
    print("=" * 70)
    print()
    print("The financial impact of proper networking configuration.")
    print("This exercise calculates the cost difference between a")
    print("well-configured VPC and a naive one.")
    print()

    nat_gw_hourly = 0.045
    nat_gw_per_gb = 0.045
    hours_per_month = 730
    iface_hourly_per_az = 0.01
    iface_per_gb = 0.01

    for scenario_name, scenario in SCENARIOS.items():
        print(f"--- {scenario_name} ---")

        # Estimate monthly S3 data volume by component
        s3_volumes = {
            "airflow": 10,       # Logs, DAG reads
            "rds_postgres": 0,   # Doesn't access S3 directly
            "redshift": 5000,    # COPY/UNLOAD
            "glue": 3000,        # ETL reads/writes
            "emr": 8000,         # Spark I/O
            "s3": 0,             # S3 itself
        }

        total_s3_gb = sum(
            s3_volumes.get(c, 0) for c in scenario["components"]
        )

        # Count interface endpoints needed
        all_iface_endpoints = set()
        for comp_name in scenario["components"]:
            if comp_name in COMPONENTS:
                for ep in COMPONENTS[comp_name]["endpoints_needed"]:
                    if ep in ENDPOINTS and ENDPOINTS[ep]["type"] == "Interface":
                        all_iface_endpoints.add(ep)

        num_iface_endpoints = len(all_iface_endpoints)

        # Cost WITHOUT endpoints (everything through NAT GW)
        nat_base = nat_gw_hourly * hours_per_month
        nat_data = nat_gw_per_gb * total_s3_gb
        cost_without = nat_base + nat_data

        # Cost WITH endpoints
        gw_cost = 0  # S3 Gateway is free
        iface_cost = num_iface_endpoints * iface_hourly_per_az * hours_per_month * 2  # 2 AZs
        cost_with = iface_cost  # NAT GW still needed for internet, but S3 traffic is free

        savings_monthly = cost_without - cost_with
        savings_annual = savings_monthly * 12

        print(f"  Estimated monthly S3 data: {total_s3_gb:,} GB")
        print(f"  Interface endpoints needed: {num_iface_endpoints} ({', '.join(sorted(all_iface_endpoints)) or 'none'})")
        print()
        print(f"  WITHOUT VPC endpoints (all via NAT GW):")
        print(f"    NAT GW base:         ${nat_base:>10,.2f}/month")
        print(f"    NAT GW data ({total_s3_gb:,} GB): ${nat_data:>10,.2f}/month")
        print(f"    Total:               ${cost_without:>10,.2f}/month")
        print()
        print(f"  WITH VPC endpoints:")
        print(f"    S3 Gateway Endpoint: $      0.00/month (FREE)")
        print(f"    Interface endpoints: ${iface_cost:>10,.2f}/month")
        print(f"    Total:               ${cost_with:>10,.2f}/month")
        print()
        print(f"  SAVINGS: ${savings_monthly:>10,.2f}/month | ${savings_annual:>10,.2f}/year")
        print()


def exercise_4() -> None:
    print("=" * 70)
    print("EXERCISE 4: Troubleshooting Simulator")
    print("=" * 70)
    print()
    print("Common 'I can't connect' scenarios mapped to their root causes")
    print("and the module where you learned to fix them.")
    print()

    problems = [
        {
            "scenario": "Redshift COPY from S3 hangs indefinitely",
            "symptoms": [
                "COPY command never completes",
                "No error message, just hangs",
            ],
            "checks": [
                ("S3 Gateway Endpoint exists?", "Module 13", "Most likely cause"),
                ("Enhanced VPC Routing enabled?", "Module 13", "Required for endpoint usage"),
                ("Redshift SG allows outbound 443 to S3 prefix list?", "Module 12", ""),
                ("IAM role attached with S3 read permissions?", "IAM (not networking)", ""),
            ],
            "fix": "Create S3 Gateway Endpoint and enable Enhanced VPC Routing",
        },
        {
            "scenario": "Airflow can't connect to RDS PostgreSQL",
            "symptoms": [
                "Connection timed out after 30 seconds",
                "psycopg2.OperationalError: could not connect to server",
            ],
            "checks": [
                ("RDS SG allows inbound TCP 5432 from airflow-sg?", "Module 12", "Most common cause"),
                ("RDS 'Publicly Accessible' set to No?", "Module 11", "If Yes, DNS returns public IP"),
                ("Airflow and RDS in routable subnets?", "Module 11", "Check route tables"),
                ("RDS subnet group includes correct subnets?", "Module 11", ""),
            ],
            "fix": "Add inbound rule: TCP 5432 from airflow-sg on rds-sg",
        },
        {
            "scenario": "Glue job fails with connection timeout to RDS",
            "symptoms": [
                "Job fails after 10 minutes",
                "java.net.ConnectException: Connection timed out",
            ],
            "checks": [
                ("Glue Connection configured with correct VPC/subnet/SG?", "Module 13", "First check"),
                ("Glue SG has self-referencing rules?", "Module 12", "Workers need to communicate"),
                ("RDS SG allows inbound TCP 5432 from glue-sg?", "Module 12", ""),
                ("Subnet has enough free IPs?", "Module 11", "Glue creates multiple ENIs"),
                ("S3 Gateway Endpoint exists?", "Module 13", "Glue reads data from S3"),
            ],
            "fix": "Configure Glue VPC Connection and add self-referencing SG rules",
        },
        {
            "scenario": "EMR Spark job has very high costs but runs fine",
            "symptoms": [
                "Job completes successfully",
                "NAT Gateway bill is unexpectedly high",
                "CloudWatch shows high NAT GW data processing",
            ],
            "checks": [
                ("S3 Gateway Endpoint exists?", "Module 13", "This is almost certainly it"),
                ("Endpoint associated with EMR subnet route table?", "Module 13", "Common miss"),
            ],
            "fix": "Create S3 Gateway Endpoint and associate with EMR subnet route table",
        },
        {
            "scenario": "MWAA environment creation fails",
            "symptoms": [
                "Environment stuck in 'Creating' then fails",
                "Error: network configuration is invalid",
            ],
            "checks": [
                ("2 private subnets in different AZs?", "Module 11", "MWAA hard requirement"),
                ("Subnets have NAT GW route?", "Module 11", "MWAA needs outbound internet"),
                ("SG allows outbound HTTPS (443)?", "Module 12", "For AWS API calls"),
                ("SG has self-referencing inbound rule?", "Module 12", "Worker communication"),
            ],
            "fix": "Ensure 2 private subnets in different AZs with NAT GW routes",
        },
    ]

    for i, problem in enumerate(problems, 1):
        print(f"  PROBLEM {i}: {problem['scenario']}")
        print()
        print(f"  Symptoms:")
        for s in problem["symptoms"]:
            print(f"    - {s}")
        print()
        print(f"  Diagnostic checklist:")
        for check, module, note in problem["checks"]:
            note_str = f" *** {note}" if note else ""
            print(f"    [ ] {check}")
            print(f"        Reference: {module}{note_str}")
        print()
        print(f"  Most likely fix: {problem['fix']}")
        print()
        print(f"  {'─' * 66}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("###################################################################")
    print("#  Module 14: AWS Data Engineering Networking -- Capstone         #")
    print("###################################################################")
    print()
    print("This capstone exercise designs complete network architectures for")
    print("real data engineering scenarios on AWS. It combines VPC design,")
    print("subnet layout, security groups, route tables, and VPC endpoints")
    print("into production-ready configurations.")
    print()

    exercise_1()
    exercise_2()
    exercise_3()
    exercise_4()

    print("=" * 70)
    print("All exercises complete.")
    print()
    print("Key takeaways:")
    print("  - Every data engineering component has specific networking needs:")
    print("    ports, subnets, security groups, and endpoints.")
    print("  - S3 Gateway Endpoint is the single highest-ROI configuration.")
    print("    It is free and saves hundreds to thousands per month.")
    print("  - Glue and MWAA need self-referencing SG rules. This is the")
    print("    most commonly missed configuration.")
    print("  - When debugging, work systematically: SG → NACL → Route Table")
    print("    → Endpoint → DNS → Service Config → IAM.")
    print("  - The cost of getting networking wrong is measured in real")
    print("    dollars (NAT GW fees) and real hours (debugging timeouts).")
    print("=" * 70)


if __name__ == "__main__":
    main()
