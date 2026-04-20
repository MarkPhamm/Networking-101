#!/usr/bin/env python3
"""
Module 12: Security Group + NACL Rule Evaluator

Exercises:
  1. SecurityGroup class -- stateful firewall, allow rules only, all rules evaluated
  2. NACL class -- stateless firewall, allow/deny, first match wins (by rule number)
  3. Test scenarios for common data engineering setups
  4. Pre-built rule templates for data services

Run: python3 exercises.py
No external dependencies required.
"""

import ipaddress


# ---------------------------------------------------------------------------
# SecurityGroup class (stateful)
# ---------------------------------------------------------------------------

class SecurityGroup:
    """
    Simulates an AWS Security Group.

    Properties:
    - Stateful: if outbound is allowed, return traffic is auto-allowed
    - Allow rules only (no deny rules)
    - All rules are evaluated (no ordering / first-match-wins)
    - Default: deny all inbound, allow all outbound
    """

    def __init__(self, name, sg_id):
        self.name = name
        self.sg_id = sg_id
        self.inbound_rules = []
        self.outbound_rules = []
        # Track active connections for stateful behavior
        self._active_connections = set()

    def add_inbound_rule(self, protocol, port_start, port_end, source, description=""):
        """
        Add an inbound allow rule.
        source can be a CIDR string or a SecurityGroup instance (SG reference).
        """
        self.inbound_rules.append({
            "protocol": protocol.upper(),
            "port_start": port_start,
            "port_end": port_end,
            "source": source,
            "description": description,
        })

    def add_outbound_rule(self, protocol, port_start, port_end, destination, description=""):
        """Add an outbound allow rule."""
        self.outbound_rules.append({
            "protocol": protocol.upper(),
            "port_start": port_start,
            "port_end": port_end,
            "destination": destination,
            "description": description,
        })

    def _match_source(self, rule_source, packet_source_ip, packet_source_sg=None):
        """Check if a packet source matches a rule's source."""
        if isinstance(rule_source, SecurityGroup):
            # SG reference: packet must come from an instance with that SG
            return packet_source_sg is not None and packet_source_sg.sg_id == rule_source.sg_id
        elif isinstance(rule_source, str):
            # CIDR match
            try:
                network = ipaddress.IPv4Network(rule_source, strict=False)
                return ipaddress.IPv4Address(packet_source_ip) in network
            except ValueError:
                return False
        return False

    def evaluate_inbound(self, protocol, dest_port, source_ip, source_sg=None):
        """
        Evaluate if an inbound packet is allowed.

        Returns (allowed, reason) tuple.
        """
        # Check if this is return traffic from an active outbound connection (stateful)
        conn_key = (source_ip, dest_port, "outbound")
        if conn_key in self._active_connections:
            return True, "ALLOWED (stateful: return traffic for active outbound connection)"

        # Check all inbound rules (all rules evaluated, any match = allow)
        for rule in self.inbound_rules:
            if rule["protocol"] != "ALL" and rule["protocol"] != protocol.upper():
                continue
            if rule["port_start"] <= dest_port <= rule["port_end"]:
                if self._match_source(rule["source"], source_ip, source_sg):
                    # Track connection for stateful return traffic
                    self._active_connections.add((source_ip, dest_port, "inbound"))
                    source_desc = (
                        rule["source"].sg_id
                        if isinstance(rule["source"], SecurityGroup)
                        else rule["source"]
                    )
                    return True, (
                        f"ALLOWED by rule: {rule['protocol']} port "
                        f"{rule['port_start']}-{rule['port_end']} "
                        f"from {source_desc}"
                        + (f" ({rule['description']})" if rule["description"] else "")
                    )

        return False, "DENIED (no matching inbound rule -- default deny)"

    def evaluate_outbound(self, protocol, dest_port, dest_ip, dest_sg=None):
        """
        Evaluate if an outbound packet is allowed.
        Default SG allows all outbound, but custom rules can restrict this.
        """
        if not self.outbound_rules:
            # Default: allow all outbound
            self._active_connections.add((dest_ip, dest_port, "outbound"))
            return True, "ALLOWED (default: all outbound traffic allowed)"

        for rule in self.outbound_rules:
            if rule["protocol"] != "ALL" and rule["protocol"] != protocol.upper():
                continue
            if rule["port_start"] <= dest_port <= rule["port_end"]:
                if self._match_source(rule["destination"], dest_ip, dest_sg):
                    self._active_connections.add((dest_ip, dest_port, "outbound"))
                    return True, f"ALLOWED by outbound rule: {rule['description']}"

        return False, "DENIED (no matching outbound rule)"

    def print_rules(self):
        print(f"  Security Group: {self.name} ({self.sg_id})")
        print(f"  Inbound Rules:")
        if not self.inbound_rules:
            print(f"    (none -- all inbound denied)")
        for rule in self.inbound_rules:
            source_str = (
                rule["source"].sg_id
                if isinstance(rule["source"], SecurityGroup)
                else rule["source"]
            )
            print(
                f"    ALLOW {rule['protocol']:4s} "
                f"port {rule['port_start']}-{rule['port_end']:<5d}  "
                f"from {source_str:<20s}  "
                f"{rule['description']}"
            )
        print(f"  Outbound Rules:")
        if not self.outbound_rules:
            print(f"    (default: allow all outbound)")
        for rule in self.outbound_rules:
            dest_str = (
                rule["destination"].sg_id
                if isinstance(rule["destination"], SecurityGroup)
                else rule["destination"]
            )
            print(
                f"    ALLOW {rule['protocol']:4s} "
                f"port {rule['port_start']}-{rule['port_end']:<5d}  "
                f"to   {dest_str:<20s}  "
                f"{rule['description']}"
            )
        print()


# ---------------------------------------------------------------------------
# NACL class (stateless)
# ---------------------------------------------------------------------------

class NACL:
    """
    Simulates an AWS Network ACL.

    Properties:
    - Stateless: inbound and outbound evaluated independently
    - Allow AND deny rules
    - Rules processed in order by rule number (lowest first)
    - First matching rule wins
    - Default rule (*) denies all if no other rule matches
    """

    def __init__(self, name):
        self.name = name
        self.inbound_rules = []
        self.outbound_rules = []

    def add_inbound_rule(self, rule_number, action, protocol, port_start, port_end,
                         source, description=""):
        self.inbound_rules.append({
            "rule_number": rule_number,
            "action": action.upper(),  # ALLOW or DENY
            "protocol": protocol.upper(),
            "port_start": port_start,
            "port_end": port_end,
            "source": source,
            "description": description,
        })
        # Keep sorted by rule number
        self.inbound_rules.sort(key=lambda r: r["rule_number"])

    def add_outbound_rule(self, rule_number, action, protocol, port_start, port_end,
                          destination, description=""):
        self.outbound_rules.append({
            "rule_number": rule_number,
            "action": action.upper(),
            "protocol": protocol.upper(),
            "port_start": port_start,
            "port_end": port_end,
            "destination": destination,
            "description": description,
        })
        self.outbound_rules.sort(key=lambda r: r["rule_number"])

    def _matches(self, rule, protocol, port, ip):
        """Check if a packet matches a rule."""
        if rule["protocol"] != "ALL" and rule["protocol"] != protocol.upper():
            return False
        if not (rule["port_start"] <= port <= rule["port_end"]):
            return False
        try:
            network = ipaddress.IPv4Network(rule["source" if "source" in rule else "destination"],
                                            strict=False)
            return ipaddress.IPv4Address(ip) in network
        except (ValueError, KeyError):
            return False

    def evaluate_inbound(self, protocol, dest_port, source_ip):
        """
        Evaluate inbound traffic. Rules processed in order by rule number.
        First match wins. Returns (allowed, reason).
        """
        for rule in self.inbound_rules:
            if rule["protocol"] != "ALL" and rule["protocol"] != protocol.upper():
                continue
            if not (rule["port_start"] <= dest_port <= rule["port_end"]):
                continue
            try:
                network = ipaddress.IPv4Network(rule["source"], strict=False)
                if ipaddress.IPv4Address(source_ip) in network:
                    allowed = rule["action"] == "ALLOW"
                    return allowed, (
                        f"{'ALLOWED' if allowed else 'DENIED'} by rule "
                        f"#{rule['rule_number']}: {rule['action']} "
                        f"{rule['protocol']} port {rule['port_start']}-{rule['port_end']} "
                        f"from {rule['source']}"
                        + (f" ({rule['description']})" if rule["description"] else "")
                    )
            except ValueError:
                continue

        return False, "DENIED by default rule (*) -- no matching rule found"

    def evaluate_outbound(self, protocol, source_port, dest_ip):
        """
        Evaluate outbound traffic. Same logic as inbound but checks destination.
        """
        for rule in self.outbound_rules:
            if rule["protocol"] != "ALL" and rule["protocol"] != protocol.upper():
                continue
            if not (rule["port_start"] <= source_port <= rule["port_end"]):
                continue
            try:
                network = ipaddress.IPv4Network(rule["destination"], strict=False)
                if ipaddress.IPv4Address(dest_ip) in network:
                    allowed = rule["action"] == "ALLOW"
                    return allowed, (
                        f"{'ALLOWED' if allowed else 'DENIED'} by rule "
                        f"#{rule['rule_number']}: {rule['action']} "
                        f"{rule['protocol']} port {rule['port_start']}-{rule['port_end']} "
                        f"to {rule['destination']}"
                        + (f" ({rule['description']})" if rule["description"] else "")
                    )
            except ValueError:
                continue

        return False, "DENIED by default rule (*) -- no matching outbound rule"

    def print_rules(self):
        print(f"  NACL: {self.name}")
        print(f"  Inbound Rules (processed in order):")
        print(f"    {'Rule#':<7s} {'Action':<7s} {'Proto':<6s} "
              f"{'Ports':<12s} {'Source':<20s} Description")
        print(f"    {'-'*7} {'-'*7} {'-'*6} {'-'*12} {'-'*20} {'-'*25}")
        for rule in self.inbound_rules:
            print(
                f"    {rule['rule_number']:<7d} {rule['action']:<7s} "
                f"{rule['protocol']:<6s} "
                f"{rule['port_start']}-{rule['port_end']:<5d}  "
                f"{rule['source']:<20s} {rule['description']}"
            )
        print(f"    {'*':<7s} {'DENY':<7s} {'ALL':<6s} {'0-65535':<12s} "
              f"{'0.0.0.0/0':<20s} Default deny")

        print(f"  Outbound Rules (processed in order):")
        print(f"    {'Rule#':<7s} {'Action':<7s} {'Proto':<6s} "
              f"{'Ports':<12s} {'Dest':<20s} Description")
        print(f"    {'-'*7} {'-'*7} {'-'*6} {'-'*12} {'-'*20} {'-'*25}")
        for rule in self.outbound_rules:
            print(
                f"    {rule['rule_number']:<7d} {rule['action']:<7s} "
                f"{rule['protocol']:<6s} "
                f"{rule['port_start']}-{rule['port_end']:<5d}  "
                f"{rule['destination']:<20s} {rule['description']}"
            )
        print(f"    {'*':<7s} {'DENY':<7s} {'ALL':<6s} {'0-65535':<12s} "
              f"{'0.0.0.0/0':<20s} Default deny")
        print()


# ---------------------------------------------------------------------------
# Test Scenarios
# ---------------------------------------------------------------------------

def build_data_eng_security():
    """
    Build a realistic data engineering security setup with security groups
    and NACLs for common services.
    """
    # Security Groups
    sg_bastion = SecurityGroup("Bastion Host", "sg-bastion")
    sg_bastion.add_inbound_rule("TCP", 22, 22, "203.0.113.0/24", "SSH from office IP range")

    sg_airflow = SecurityGroup("Airflow", "sg-airflow")
    sg_airflow.add_inbound_rule("TCP", 8080, 8080, "203.0.113.0/24", "Web UI from office")
    sg_airflow.add_inbound_rule("TCP", 8080, 8080, sg_bastion, "Web UI via bastion")

    sg_rds = SecurityGroup("RDS PostgreSQL", "sg-rds")
    sg_rds.add_inbound_rule("TCP", 5432, 5432, sg_airflow, "Airflow metadata DB")
    sg_rds.add_inbound_rule("TCP", 5432, 5432, sg_bastion, "DBA access via bastion")

    sg_redshift = SecurityGroup("Redshift", "sg-redshift")
    sg_redshift.add_inbound_rule("TCP", 5439, 5439, sg_airflow, "Airflow queries")
    sg_redshift.add_inbound_rule("TCP", 5439, 5439, "10.0.3.0/24", "Glue subnet")
    sg_redshift.add_inbound_rule("TCP", 5439, 5439, sg_bastion, "DBA access via bastion")

    sg_glue = SecurityGroup("Glue Jobs", "sg-glue")
    # Glue needs outbound to Redshift and RDS, plus HTTPS for AWS APIs
    sg_glue.add_outbound_rule("TCP", 5439, 5439, "10.0.2.0/24", "To Redshift subnet")
    sg_glue.add_outbound_rule("TCP", 5432, 5432, "10.0.2.0/24", "To RDS subnet")
    sg_glue.add_outbound_rule("TCP", 443, 443, "0.0.0.0/0", "HTTPS to AWS APIs")

    # NACLs
    nacl_public = NACL("Public Subnet NACL")
    nacl_public.add_inbound_rule(100, "ALLOW", "TCP", 22, 22, "203.0.113.0/24",
                                 "SSH from office")
    nacl_public.add_inbound_rule(110, "ALLOW", "TCP", 8080, 8080, "203.0.113.0/24",
                                 "Airflow UI from office")
    nacl_public.add_inbound_rule(120, "ALLOW", "TCP", 443, 443, "0.0.0.0/0",
                                 "HTTPS inbound")
    nacl_public.add_inbound_rule(130, "ALLOW", "TCP", 1024, 65535, "0.0.0.0/0",
                                 "Ephemeral ports (return traffic)")
    nacl_public.add_outbound_rule(100, "ALLOW", "TCP", 0, 65535, "10.0.0.0/16",
                                  "All TCP to VPC")
    nacl_public.add_outbound_rule(110, "ALLOW", "TCP", 443, 443, "0.0.0.0/0",
                                  "HTTPS outbound")
    nacl_public.add_outbound_rule(120, "ALLOW", "TCP", 1024, 65535, "0.0.0.0/0",
                                  "Ephemeral ports (return traffic)")

    nacl_private = NACL("Private Subnet NACL")
    nacl_private.add_inbound_rule(100, "ALLOW", "TCP", 5432, 5432, "10.0.0.0/16",
                                  "PostgreSQL from VPC")
    nacl_private.add_inbound_rule(110, "ALLOW", "TCP", 5439, 5439, "10.0.0.0/16",
                                  "Redshift from VPC")
    nacl_private.add_inbound_rule(120, "ALLOW", "TCP", 1024, 65535, "0.0.0.0/0",
                                  "Ephemeral ports (return traffic)")
    nacl_private.add_inbound_rule(200, "DENY", "ALL", 0, 65535, "0.0.0.0/0",
                                  "Deny everything else")
    nacl_private.add_outbound_rule(100, "ALLOW", "TCP", 443, 443, "0.0.0.0/0",
                                   "HTTPS outbound (AWS APIs, updates)")
    nacl_private.add_outbound_rule(110, "ALLOW", "TCP", 1024, 65535, "10.0.0.0/16",
                                   "Ephemeral ports to VPC")
    nacl_private.add_outbound_rule(120, "ALLOW", "TCP", 1024, 65535, "0.0.0.0/0",
                                   "Ephemeral ports (return traffic)")

    return {
        "sg_bastion": sg_bastion,
        "sg_airflow": sg_airflow,
        "sg_rds": sg_rds,
        "sg_redshift": sg_redshift,
        "sg_glue": sg_glue,
        "nacl_public": nacl_public,
        "nacl_private": nacl_private,
    }


def run_scenario(label, steps):
    """Run a test scenario and print results."""
    print(f"  Scenario: {label}")
    for step_desc, allowed, reason in steps:
        status = "ALLOW" if allowed else "DENY"
        icon = " [+]" if allowed else " [X]"
        print(f"  {icon} {step_desc}")
        print(f"       {reason}")
    print()


def exercise_scenarios():
    """Run through data engineering connectivity scenarios."""
    print("=" * 70)
    print("EXERCISE: Data Engineering Security Scenarios")
    print("=" * 70)
    print()

    sec = build_data_eng_security()

    # Print all rules first
    print("--- SECURITY GROUP RULES ---")
    print()
    sec["sg_bastion"].print_rules()
    sec["sg_airflow"].print_rules()
    sec["sg_rds"].print_rules()
    sec["sg_redshift"].print_rules()
    sec["sg_glue"].print_rules()

    print("--- NACL RULES ---")
    print()
    sec["nacl_public"].print_rules()
    sec["nacl_private"].print_rules()

    print("=" * 70)
    print("TEST SCENARIOS")
    print("=" * 70)
    print()

    # Scenario 1: Airflow -> RDS on port 5432
    print("-" * 70)
    print("  SCENARIO 1: Airflow (10.0.1.50) -> RDS (10.0.2.100) on port 5432")
    print("-" * 70)
    print()
    print("  Step 1: Check Airflow SG outbound (port 5432 to 10.0.2.100)")
    allowed, reason = sec["sg_airflow"].evaluate_outbound("TCP", 5432, "10.0.2.100")
    status = "[+] PASS" if allowed else "[X] BLOCKED"
    print(f"    {status}: {reason}")

    print("  Step 2: Check Public Subnet NACL outbound")
    allowed_nacl, reason_nacl = sec["nacl_public"].evaluate_outbound("TCP", 5432, "10.0.2.100")
    status = "[+] PASS" if allowed_nacl else "[X] BLOCKED"
    print(f"    {status}: {reason_nacl}")

    print("  Step 3: Check Private Subnet NACL inbound (port 5432 from 10.0.1.50)")
    allowed_nacl2, reason_nacl2 = sec["nacl_private"].evaluate_inbound("TCP", 5432, "10.0.1.50")
    status = "[+] PASS" if allowed_nacl2 else "[X] BLOCKED"
    print(f"    {status}: {reason_nacl2}")

    print("  Step 4: Check RDS SG inbound (port 5432 from sg-airflow)")
    allowed_sg, reason_sg = sec["sg_rds"].evaluate_inbound(
        "TCP", 5432, "10.0.1.50", source_sg=sec["sg_airflow"]
    )
    status = "[+] PASS" if allowed_sg else "[X] BLOCKED"
    print(f"    {status}: {reason_sg}")

    final = allowed and allowed_nacl and allowed_nacl2 and allowed_sg
    print(f"\n  RESULT: {'CONNECTION ALLOWED' if final else 'CONNECTION BLOCKED'}")
    print(f"  Airflow can {'successfully query' if final else 'NOT query'} the RDS metadata database.")
    print()

    # Scenario 2: Laptop -> Bastion on port 22
    print("-" * 70)
    print("  SCENARIO 2: Laptop (203.0.113.10) -> Bastion (10.0.0.50) on port 22")
    print("-" * 70)
    print()

    print("  Step 1: Check Public Subnet NACL inbound (port 22 from 203.0.113.10)")
    allowed1, reason1 = sec["nacl_public"].evaluate_inbound("TCP", 22, "203.0.113.10")
    status = "[+] PASS" if allowed1 else "[X] BLOCKED"
    print(f"    {status}: {reason1}")

    print("  Step 2: Check Bastion SG inbound (port 22 from 203.0.113.10)")
    allowed2, reason2 = sec["sg_bastion"].evaluate_inbound("TCP", 22, "203.0.113.10")
    status = "[+] PASS" if allowed2 else "[X] BLOCKED"
    print(f"    {status}: {reason2}")

    print("  Step 3: Return traffic -- SG is stateful (automatic)")
    print(f"    [+] PASS: Security group automatically allows return traffic (stateful)")

    print("  Step 4: Return traffic -- NACL outbound (ephemeral port to 203.0.113.10)")
    allowed4, reason4 = sec["nacl_public"].evaluate_outbound("TCP", 49152, "203.0.113.10")
    status = "[+] PASS" if allowed4 else "[X] BLOCKED"
    print(f"    {status}: {reason4}")

    final = allowed1 and allowed2 and allowed4
    print(f"\n  RESULT: {'CONNECTION ALLOWED' if final else 'CONNECTION BLOCKED'}")
    print(f"  You can {'SSH into' if final else 'NOT SSH into'} the bastion host from the office.")
    print()

    # Scenario 3: Glue -> Redshift on port 5439
    print("-" * 70)
    print("  SCENARIO 3: Glue (10.0.3.25) -> Redshift (10.0.2.200) on port 5439")
    print("-" * 70)
    print()

    print("  Step 1: Check Glue SG outbound (port 5439 to 10.0.2.200)")
    allowed1, reason1 = sec["sg_glue"].evaluate_outbound("TCP", 5439, "10.0.2.200")
    status = "[+] PASS" if allowed1 else "[X] BLOCKED"
    print(f"    {status}: {reason1}")

    print("  Step 2: Check Redshift SG inbound (port 5439 from Glue subnet 10.0.3.0/24)")
    allowed2, reason2 = sec["sg_redshift"].evaluate_inbound("TCP", 5439, "10.0.3.25")
    status = "[+] PASS" if allowed2 else "[X] BLOCKED"
    print(f"    {status}: {reason2}")

    final = allowed1 and allowed2
    print(f"\n  RESULT: {'CONNECTION ALLOWED' if final else 'CONNECTION BLOCKED'}")
    print(f"  Glue can {'load data into' if final else 'NOT reach'} Redshift.")
    print()

    # Scenario 4: Internet -> private instance (should be blocked)
    print("-" * 70)
    print("  SCENARIO 4: Internet (198.51.100.50) -> Private RDS (10.0.2.100) on port 5432")
    print("-" * 70)
    print()

    print("  Step 1: Check Private Subnet NACL inbound (port 5432 from 198.51.100.50)")
    allowed1, reason1 = sec["nacl_private"].evaluate_inbound("TCP", 5432, "198.51.100.50")
    status = "[+] PASS" if allowed1 else "[X] BLOCKED"
    print(f"    {status}: {reason1}")

    if allowed1:
        print("  Step 2: Check RDS SG inbound (port 5432 from 198.51.100.50)")
        allowed2, reason2 = sec["sg_rds"].evaluate_inbound("TCP", 5432, "198.51.100.50")
        status = "[+] PASS" if allowed2 else "[X] BLOCKED"
        print(f"    {status}: {reason2}")
        final = allowed1 and allowed2
    else:
        print("  Step 2: Skipped -- NACL already blocked the traffic")
        final = False

    print(f"\n  RESULT: {'CONNECTION ALLOWED' if final else 'CONNECTION BLOCKED'}")
    print(f"  Internet traffic {'CAN reach' if final else 'CANNOT reach'} the private RDS instance.")
    if not final:
        print("  This is the correct behavior! Databases should not be reachable from the internet.")
    print()

    # Scenario 5: Unauthorized IP trying SSH
    print("-" * 70)
    print("  SCENARIO 5: Attacker (198.51.100.99) -> Bastion (10.0.0.50) on port 22")
    print("-" * 70)
    print()

    print("  Step 1: Check Public Subnet NACL inbound (port 22 from 198.51.100.99)")
    allowed1, reason1 = sec["nacl_public"].evaluate_inbound("TCP", 22, "198.51.100.99")
    status = "[+] PASS" if allowed1 else "[X] BLOCKED"
    print(f"    {status}: {reason1}")

    if allowed1:
        print("  Step 2: Check Bastion SG inbound (port 22 from 198.51.100.99)")
        allowed2, reason2 = sec["sg_bastion"].evaluate_inbound("TCP", 22, "198.51.100.99")
        status = "[+] PASS" if allowed2 else "[X] BLOCKED"
        print(f"    {status}: {reason2}")
        final = allowed1 and allowed2
    else:
        final = False

    print(f"\n  RESULT: {'CONNECTION ALLOWED' if final else 'CONNECTION BLOCKED'}")
    if not final:
        print("  The attacker is blocked. Only the office IP range (203.0.113.0/24) can SSH in.")
    print()


# ---------------------------------------------------------------------------
# Rule Templates
# ---------------------------------------------------------------------------

def print_rule_templates():
    """Print pre-built security group rule templates for common data services."""
    print("=" * 70)
    print("REFERENCE: Security Group Rule Templates for Data Services")
    print("=" * 70)
    print()

    templates = [
        {
            "service": "Amazon Redshift",
            "port": 5439,
            "rules": [
                ("Inbound", "TCP", "5439", "sg-airflow", "ETL/orchestration access"),
                ("Inbound", "TCP", "5439", "sg-glue", "Glue job access"),
                ("Inbound", "TCP", "5439", "sg-bi-tools", "BI tool access (Looker, Tableau)"),
                ("Inbound", "TCP", "5439", "sg-bastion", "DBA access via bastion"),
            ],
        },
        {
            "service": "Amazon RDS (PostgreSQL)",
            "port": 5432,
            "rules": [
                ("Inbound", "TCP", "5432", "sg-application", "Application backend"),
                ("Inbound", "TCP", "5432", "sg-airflow", "Airflow metadata DB"),
                ("Inbound", "TCP", "5432", "sg-bastion", "DBA access via bastion"),
            ],
        },
        {
            "service": "Amazon RDS (MySQL)",
            "port": 3306,
            "rules": [
                ("Inbound", "TCP", "3306", "sg-application", "Application backend"),
                ("Inbound", "TCP", "3306", "sg-airflow", "Airflow metadata DB"),
                ("Inbound", "TCP", "3306", "sg-bastion", "DBA access via bastion"),
            ],
        },
        {
            "service": "Amazon EMR (Master Node)",
            "port": "multiple",
            "rules": [
                ("Inbound", "TCP", "8088", "sg-bastion", "YARN ResourceManager UI"),
                ("Inbound", "TCP", "18080", "sg-bastion", "Spark History Server UI"),
                ("Inbound", "TCP", "8888", "sg-bastion", "Jupyter/Zeppelin notebook"),
                ("Inbound", "ALL", "0-65535", "sg-emr-core", "Core/task node communication"),
            ],
        },
        {
            "service": "Amazon MSK (Kafka)",
            "port": "multiple",
            "rules": [
                ("Inbound", "TCP", "9092", "sg-producers", "Plaintext Kafka producer access"),
                ("Inbound", "TCP", "9094", "sg-producers", "TLS Kafka producer access"),
                ("Inbound", "TCP", "9092", "sg-consumers", "Plaintext Kafka consumer access"),
                ("Inbound", "TCP", "9094", "sg-consumers", "TLS Kafka consumer access"),
                ("Inbound", "TCP", "2181", "sg-kafka-admin", "ZooKeeper access"),
            ],
        },
        {
            "service": "Airflow (self-hosted / MWAA)",
            "port": 8080,
            "rules": [
                ("Inbound", "TCP", "8080", "sg-alb", "Web UI via ALB"),
                ("Inbound", "TCP", "8080", "203.0.113.0/24", "Direct access from office"),
                ("Outbound", "TCP", "5432", "sg-rds", "To metadata database"),
                ("Outbound", "TCP", "5439", "sg-redshift", "To Redshift for queries"),
                ("Outbound", "TCP", "443", "0.0.0.0/0", "HTTPS to AWS APIs / external"),
            ],
        },
    ]

    for tmpl in templates:
        print(f"  {tmpl['service']} (port {tmpl['port']}):")
        print(f"    {'Direction':<10s} {'Proto':<6s} {'Port':<10s} "
              f"{'Source/Dest':<20s} Description")
        print(f"    {'-'*10} {'-'*6} {'-'*10} {'-'*20} {'-'*30}")
        for direction, proto, port, source, desc in tmpl["rules"]:
            print(f"    {direction:<10s} {proto:<6s} {port:<10s} {source:<20s} {desc}")
        print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print()
    print("*" * 70)
    print("  Module 12: Security Group + NACL Rule Evaluator")
    print("  AWS Security Groups and NACLs -- Hands-on Exercises")
    print("*" * 70)
    print()
    print("These exercises simulate AWS security groups (stateful) and")
    print("NACLs (stateless) in pure Python. No AWS account needed.")
    print()
    print("Network layout:")
    print("  VPC:             10.0.0.0/16")
    print("  Public subnet:   10.0.0.0/24  and  10.0.1.0/24")
    print("  Private subnet:  10.0.2.0/24  and  10.0.3.0/24")
    print("  Office IP range: 203.0.113.0/24")
    print()
    print("  Bastion host:    10.0.0.50   (public subnet, sg-bastion)")
    print("  Airflow:         10.0.1.50   (public subnet, sg-airflow)")
    print("  RDS PostgreSQL:  10.0.2.100  (private subnet, sg-rds)")
    print("  Redshift:        10.0.2.200  (private subnet, sg-redshift)")
    print("  Glue ENI:        10.0.3.25   (private subnet, sg-glue)")
    print()

    exercise_scenarios()
    print_rule_templates()

    print("=" * 70)
    print("KEY LESSONS:")
    print("=" * 70)
    print()
    print("  1. Security Groups are STATEFUL: allow a connection in one direction")
    print("     and return traffic is automatic. No need for ephemeral port rules.")
    print("  2. NACLs are STATELESS: you MUST allow return traffic explicitly")
    print("     (ephemeral ports 1024-65535).")
    print("  3. Security Groups evaluate ALL rules (any match = allow).")
    print("     NACLs evaluate rules IN ORDER (first match wins).")
    print("  4. Use SG references (sg-xxx) instead of IPs when possible -- this")
    print("     handles dynamic IPs from auto-scaling and new deployments.")
    print("  5. Defense in depth: SGs for per-resource control, NACLs for")
    print("     subnet-level guardrails.")
    print("  6. When debugging: check SG -> NACL -> route table -> subnet -> IGW/NAT.")
    print()


if __name__ == "__main__":
    main()
