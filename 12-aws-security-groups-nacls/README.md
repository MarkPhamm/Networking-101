# Module 12: Security Groups and NACLs

## Overview

In Module 06, you learned about firewalls -- stateful vs stateless, rule ordering, allow/deny decisions. AWS has two firewall mechanisms that map directly to those concepts: **Security Groups** (stateful, attached to individual resources) and **Network ACLs** (stateless, attached to subnets). Understanding when and how to use each one is critical for securing your data infrastructure and debugging connectivity issues.

If you have ever wondered why your Airflow worker cannot connect to your RDS database even though "everything looks right," the answer is almost always a missing or misconfigured security group rule.

---

## Security Groups

A security group acts as a virtual firewall for individual resources. It is attached to an **Elastic Network Interface (ENI)** -- the virtual network card of an EC2 instance, RDS database, Lambda function, or any other VPC resource.

### Key Properties

| Property | Behavior |
|----------|----------|
| **Stateful** | If you allow outbound traffic, the return traffic is automatically allowed (and vice versa). You do not need to write rules for both directions. |
| **Allow rules only** | You can only write rules that ALLOW traffic. There is no way to explicitly DENY. If traffic does not match any rule, it is denied by default. |
| **All rules evaluated** | Every rule is checked. If any rule allows the traffic, it is allowed. There is no rule ordering or "first match wins." |
| **Attached to ENI** | Applied at the resource level, not the subnet level. Different instances in the same subnet can have different security groups. |
| **Default deny** | If no rule matches, traffic is denied. A security group with no rules blocks everything. |

### Security Group Rules

Each rule specifies:

| Field | Description | Example |
|-------|-------------|---------|
| **Type/Protocol** | The protocol (TCP, UDP, ICMP, or All) | TCP |
| **Port range** | The port or range of ports | 5432 (PostgreSQL) |
| **Source/Destination** | What can send (inbound) or receive (outbound) traffic | `10.0.0.0/16`, `sg-abc123`, or `0.0.0.0/0` |

### The Power of Security Group References

Instead of specifying IP ranges, you can reference **another security group** as the source. This is one of the most powerful features in AWS networking.

```
Security Group: sg-airflow
  (attached to Airflow EC2 instances)

Security Group: sg-rds
  Inbound rule: Allow TCP port 5432 from sg-airflow
  (attached to RDS instance)
```

This means: "Allow any instance that has `sg-airflow` attached to connect to this RDS instance on port 5432." If you add a new Airflow worker, it automatically has access -- no IP addresses to update.

**Why this matters for data engineering:** Your infrastructure is dynamic. Auto-scaling groups add and remove instances. EMR clusters spin up and down. Security group references mean you define access by **role** ("Airflow can talk to RDS") rather than by IP ("10.0.1.47 can talk to 10.0.2.100").

---

## Network ACLs (NACLs)

A NACL is a firewall attached to a **subnet**. Every packet entering or leaving the subnet is evaluated against the NACL rules.

### Key Properties

| Property | Behavior |
|----------|----------|
| **Stateless** | Inbound and outbound traffic are evaluated independently. If you allow inbound traffic on port 5432, you must also allow the outbound return traffic (typically on ephemeral ports 1024-65535). |
| **Allow AND deny rules** | You can explicitly ALLOW or DENY traffic. |
| **Rules processed in order** | Rules are numbered. They are evaluated in ascending order. The **first matching rule** determines the outcome. Lower numbers are evaluated first. |
| **Attached to subnet** | Applies to ALL resources in the subnet, regardless of their security groups. |
| **Default allow** | The default NACL allows all inbound and outbound traffic. Custom NACLs deny all by default. |

### NACL Rule Structure

| Field | Description | Example |
|-------|-------------|---------|
| **Rule number** | Priority (lower = evaluated first) | 100 |
| **Type/Protocol** | Protocol (TCP, UDP, ICMP, All) | TCP |
| **Port range** | Port or range | 5432 |
| **Source/Destination** | CIDR block | 10.0.0.0/16 |
| **Action** | ALLOW or DENY | ALLOW |

### Rule Processing Example

```
NACL Inbound Rules:
  Rule 100: ALLOW TCP port 443 from 0.0.0.0/0
  Rule 200: DENY  TCP port 443 from 198.51.100.0/24
  Rule 300: ALLOW TCP port 22  from 10.0.0.0/8
  Rule  *:  DENY  all (default rule, always last)

Packet: TCP port 443 from 198.51.100.50
  Rule 100: ALLOW TCP port 443 from 0.0.0.0/0  --> MATCH! --> ALLOWED
  (Rule 200 is never evaluated, even though it would deny this source)
```

**Order matters.** If you want to deny a specific IP range on port 443 while allowing everyone else, the DENY rule must have a lower number than the ALLOW rule:

```
Corrected:
  Rule 100: DENY  TCP port 443 from 198.51.100.0/24   <-- deny first
  Rule 200: ALLOW TCP port 443 from 0.0.0.0/0         <-- then allow the rest
```

---

## Stateful vs Stateless: The Critical Difference

This is the single most important concept in this module.

### Security Group (Stateful)

```
You add one rule:
  Inbound: Allow TCP port 5432 from sg-airflow

What happens:
  1. Airflow sends a packet to RDS on port 5432  --> ALLOWED (matches inbound rule)
  2. RDS replies on ephemeral port (e.g., 49152)  --> AUTOMATICALLY ALLOWED
     (SG remembers the connection and allows the return traffic)
```

You only need to think about the initial direction of the connection.

### NACL (Stateless)

```
You add one rule:
  Inbound: Rule 100, Allow TCP port 5432 from 10.0.1.0/24

What happens:
  1. Airflow sends a packet to RDS on port 5432  --> ALLOWED (matches inbound rule)
  2. RDS replies on ephemeral port (e.g., 49152)  --> DENIED!
     (NACL does NOT remember the connection. There is no outbound rule for this.)
```

You must add an explicit outbound rule:

```
  Outbound: Rule 100, Allow TCP ports 1024-65535 to 10.0.1.0/24
```

Now the response packets can leave the subnet.

**This is the number one NACL gotcha.** People add inbound rules and forget that the response traffic needs an outbound rule too. Security groups handle this automatically; NACLs do not.

---

## Security Groups vs NACLs: When to Use Each

| Aspect | Security Group | NACL |
|--------|---------------|------|
| Layer | Resource (ENI) | Subnet |
| State | Stateful | Stateless |
| Rules | Allow only | Allow and Deny |
| Evaluation | All rules evaluated | First match wins (numbered) |
| Default | Deny all inbound, allow all outbound | Default NACL allows all; custom NACLs deny all |
| Use case | Fine-grained per-resource access control | Subnet-level guardrails, blocking specific IPs |

**Best practice:** Use security groups as your primary access control mechanism. Use NACLs as a coarse-grained second layer of defense.

Think of it as defense in depth:
- **NACL** = the bouncer at the door of the building (subnet). Checks IDs, blocks known troublemakers.
- **Security Group** = the lock on each individual office (resource). Only people with the right key get in.

---

## Common Security Group Patterns for Data Services

### Redshift Cluster

```
Security Group: sg-redshift
  Inbound:
    TCP 5439 from sg-airflow        (Airflow DAGs query Redshift)
    TCP 5439 from sg-glue           (Glue jobs load data into Redshift)
    TCP 5439 from sg-bi-tools       (Looker/Tableau connect to Redshift)
    TCP 5439 from 10.0.0.0/16      (Allow from entire VPC -- less restrictive option)
```

### RDS PostgreSQL

```
Security Group: sg-rds
  Inbound:
    TCP 5432 from sg-airflow        (Airflow reads/writes metadata)
    TCP 5432 from sg-application    (Application backend)
    TCP 5432 from sg-bastion        (DBA access via bastion host)
```

### EMR Cluster

```
Security Group: sg-emr-master
  Inbound:
    TCP 8088 from sg-bastion        (YARN ResourceManager UI)
    TCP 18080 from sg-bastion       (Spark History Server)
    All traffic from sg-emr-core    (Core nodes talk to master)

Security Group: sg-emr-core
  Inbound:
    All traffic from sg-emr-master  (Master talks to core nodes)
    All traffic from sg-emr-core    (Core nodes talk to each other)
```

### Airflow (MWAA or self-hosted)

```
Security Group: sg-airflow
  Inbound:
    TCP 8080 from sg-alb            (ALB forwards web UI traffic)
    TCP 8080 from 203.0.113.0/24   (Your office IP for direct access)
  Outbound:
    TCP 5432 to sg-rds              (Connect to metadata DB)
    TCP 5439 to sg-redshift         (Run Redshift queries)
    TCP 443  to 0.0.0.0/0          (HTTPS to external APIs)
```

---

## Common Debugging Scenarios

### "I added port 22 to my security group but still can't SSH"

**Checklist:**

1. **Security group inbound rule** -- Is port 22 allowed from your IP? Check the source CIDR.
2. **NACL inbound rule** -- Is the subnet's NACL allowing port 22 inbound?
3. **NACL outbound rule** -- Is the NACL allowing outbound traffic on ephemeral ports (1024-65535)?
4. **Route table** -- Does the subnet's route table have a path to the internet (for public instances) or to your network (for private instances)?
5. **Public IP** -- Does the instance have a public IP or Elastic IP (if connecting from the internet)?
6. **Internet Gateway** -- Is an IGW attached to the VPC?

### "Glue job cannot connect to RDS"

1. **Glue connection VPC settings** -- Is the Glue connection configured with the correct VPC, subnet, and security group?
2. **Security group** -- Does the RDS security group allow inbound on the database port from the Glue security group?
3. **Subnet** -- Is the Glue connection's subnet in the same VPC as RDS? Does it have a route?
4. **NACL** -- Are NACLs on both the Glue subnet and RDS subnet allowing the traffic?

### "Redshift is unreachable from my BI tool"

1. **Public vs private** -- Is Redshift in a private subnet? If so, the BI tool must connect via VPN, Direct Connect, or a bastion/proxy.
2. **Security group** -- Does `sg-redshift` allow port 5439 from the BI tool's IP or security group?
3. **Enhanced VPC routing** -- If using Redshift enhanced VPC routing, all traffic goes through the VPC. Check route tables.

---

## Data Engineering Analogy

| AWS Concept | Data Engineering Equivalent |
|---|---|
| Security groups | **Database user privileges / row-level security** -- fine-grained control over who can access each specific resource. "User `airflow_svc` can SELECT on `analytics.*`" is like "sg-airflow can access sg-redshift on port 5439." |
| NACLs | **IP allowlists / network-level ACLs** -- coarse-grained control at the zone level. "Only traffic from the 10.0.x.x network can reach the data subnet" is like "only connections from the internal network can reach the database server." |
| SG references | **Role-based access** -- granting access by role rather than by identity. "All members of the `etl_team` role can write to this schema" is like "all instances with sg-etl can reach sg-warehouse." |
| Stateful (SG) | **Connection pooling** -- the system tracks the connection state. You do not re-authenticate every query. |
| Stateless (NACL) | **Stateless API authentication** -- every request must carry its own credentials. Every packet is evaluated independently. |

---

## Key Takeaways

1. Security groups are **stateful** firewalls attached to individual resources. Allow rules only, all rules evaluated. Return traffic is automatic.
2. NACLs are **stateless** firewalls attached to subnets. Allow and deny rules, processed in order by rule number. You must explicitly allow return traffic.
3. Use security groups as your primary access control. Use NACLs as a second layer of defense.
4. Security group references (allowing traffic from another SG) are the preferred way to manage access between AWS services -- no hardcoded IPs.
5. The most common NACL mistake is forgetting outbound rules for return traffic (ephemeral ports 1024-65535).
6. The most common security group mistake is not allowing the right source -- check whether you need a CIDR block or a security group reference.
7. When something cannot connect, check in order: security group, NACL, route table, subnet association, IGW/NAT GW.
