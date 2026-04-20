# Module 11: AWS Subnets and Routing

## Overview

In Module 05, you learned how subnets divide an IP address space and how routing tables forward packets between them. AWS subnets and route tables work exactly the same way -- the difference is that in AWS, you also decide whether a subnet is **public** (can reach the internet directly) or **private** (hidden behind a NAT gateway). This distinction is one of the most important architectural decisions you make when deploying data infrastructure.

If your Redshift cluster is in a private subnet and your BI tool is on the internet, the connection path goes through specific components in a specific order. Understanding that path is the key to debugging "I can't connect to my database" problems.

---

## Public vs Private Subnets

There is no AWS setting called "public" or "private." A subnet's public/private status is determined entirely by its route table.

### Public Subnet

A subnet whose route table has a route sending `0.0.0.0/0` (all internet-bound traffic) to an **Internet Gateway (IGW)**.

Resources in a public subnet **can** have public IP addresses and communicate directly with the internet.

```
Route table for public subnet:
  Destination        Target
  10.0.0.0/16        local          (traffic within the VPC)
  0.0.0.0/0          igw-abc123     (everything else goes to the internet gateway)
```

**What belongs here:** Bastion hosts, load balancers (ALB/NLB), NAT gateways, public-facing web servers.

### Private Subnet

A subnet whose route table sends `0.0.0.0/0` to a **NAT Gateway** (or has no internet route at all).

Resources in a private subnet **cannot** be reached directly from the internet. They can reach the internet outbound (through the NAT gateway) but inbound connections from the internet are not possible.

```
Route table for private subnet:
  Destination        Target
  10.0.0.0/16        local          (traffic within the VPC)
  0.0.0.0/0          nat-xyz789     (outbound internet goes through NAT gateway)
```

**What belongs here:** Databases (RDS, Redshift), EMR clusters, Glue connections, internal microservices, Kafka brokers.

### Why This Matters for Data Engineering

Your data infrastructure should almost always be in private subnets:

| Service | Subnet Type | Reason |
|---------|------------|--------|
| Redshift cluster | Private | No reason for the internet to reach your data warehouse directly |
| RDS PostgreSQL | Private | Database should only be accessible from within the VPC |
| EMR cluster | Private | Processing nodes do not need public IPs |
| Glue connection | Private | Connects to your data sources via ENI in your VPC |
| Bastion host | Public | The jump box you SSH through to reach private resources |
| ALB for Airflow UI | Public | Accepts HTTPS from authorized users, forwards to private Airflow instances |
| NAT Gateway | Public | Must be in a public subnet to route private subnet traffic to the internet |

---

## Internet Gateway (IGW)

An Internet Gateway is a horizontally scaled, redundant, highly available VPC component that enables communication between your VPC and the internet. Think of it as the front door of your VPC.

Key facts:

- One IGW per VPC (you cannot attach multiple)
- No bandwidth constraints -- AWS manages scaling
- It performs 1:1 NAT for instances with public IPs (maps private IP to public IP)
- Without an IGW, nothing in your VPC can reach the internet

```
Internet  <-->  [Internet Gateway]  <-->  [Public Subnet]
                                              |
                                         [NAT Gateway]
                                              |
                                         [Private Subnet]
```

---

## NAT Gateway

A NAT Gateway lets instances in private subnets initiate outbound connections to the internet without being reachable from the internet. This is the same NAT concept from Module 06.

**Why private instances need outbound internet access:**
- Download OS patches and security updates
- Pull packages from PyPI, Maven, npm
- Call external APIs (Slack notifications, third-party data sources)
- Push metrics to external monitoring services

Key facts:

- Lives in a **public subnet** (it needs internet access to forward traffic)
- Has an Elastic IP (a static public IP)
- Managed by AWS -- no patching or scaling needed
- Costs money: per-hour charge plus per-GB data processing charge
- Create one per AZ for high availability

### NAT Gateway vs NAT Instance

| Feature | NAT Gateway | NAT Instance |
|---------|------------|--------------|
| Managed by | AWS | You |
| Availability | Highly available in an AZ | Single EC2 instance (you manage HA) |
| Bandwidth | Up to 100 Gbps | Depends on instance type |
| Cost | Higher per-hour, but less operational overhead | Lower per-hour, but you manage everything |
| Maintenance | None | You patch, monitor, replace |

**Recommendation:** Use NAT Gateway unless you have a strong cost reason to use a NAT instance (e.g., tiny dev environment).

---

## Multi-AZ Subnet Design

For high availability, you spread your subnets across multiple Availability Zones. A typical production VPC has public and private subnets in each AZ:

```
VPC: 10.0.0.0/16
|
+-- AZ: us-east-1a
|   +-- Public Subnet:  10.0.1.0/24   (bastion, NAT GW, ALB)
|   +-- Private Subnet: 10.0.10.0/24  (RDS primary, EMR core nodes)
|
+-- AZ: us-east-1b
|   +-- Public Subnet:  10.0.2.0/24   (NAT GW, ALB)
|   +-- Private Subnet: 10.0.20.0/24  (RDS replica, EMR core nodes)
|
+-- AZ: us-east-1c
    +-- Public Subnet:  10.0.3.0/24   (NAT GW, ALB)
    +-- Private Subnet: 10.0.30.0/24  (EMR task nodes, Redshift)
```

### Why Three AZs?

- **RDS Multi-AZ:** Primary in one AZ, standby in another. Automatic failover.
- **EMR:** Spread core and task nodes across AZs. If one AZ goes down, you still have compute.
- **Redshift:** RA3 node types support Multi-AZ deployments.
- **ALB:** Distributes traffic across instances in multiple AZs.

---

## Route Tables

Every subnet must be associated with exactly one route table. A route table can be associated with multiple subnets.

### Route Table Structure

Each entry in a route table has:

| Field | Description |
|-------|-------------|
| **Destination** | The CIDR block of the target network (e.g., `10.0.0.0/16`, `0.0.0.0/0`) |
| **Target** | Where to send matching traffic (e.g., `local`, `igw-xxx`, `nat-xxx`, `pcx-xxx`) |

### The `local` Route

Every VPC route table automatically includes a `local` route for the VPC CIDR block. This route enables communication between all subnets within the VPC and **cannot be deleted**.

```
Destination      Target
10.0.0.0/16      local      <-- Always present, cannot be removed
```

This is why an EC2 instance in `10.0.1.0/24` can reach an RDS instance in `10.0.10.0/24` without any additional routing configuration -- they are both within `10.0.0.0/16`, and the `local` route handles it.

### Route Priority: Longest Prefix Match

Just like Module 05, AWS route tables use **longest prefix match**. The most specific route wins.

```
Route table:
  Destination        Target
  10.0.0.0/16        local
  10.0.99.0/24       pcx-abc123    (VPC peering connection)
  0.0.0.0/0          igw-xyz789

Packet to 10.0.99.50:
  Matches 10.0.0.0/16 (prefix /16)
  Matches 10.0.99.0/24 (prefix /24)  <-- WINS (more specific)
  --> Sent to pcx-abc123 (peering connection)

Packet to 8.8.8.8:
  Matches 0.0.0.0/0 (prefix /0)
  --> Sent to igw-xyz789 (internet gateway)
```

---

## Subnet Sizing

When you create a subnet in AWS, you choose a CIDR block that is a subset of the VPC CIDR. AWS reserves **5 IP addresses** in every subnet:

| Reserved Address | Purpose |
|-----------------|---------|
| First IP (e.g., 10.0.1.0) | Network address |
| Second IP (e.g., 10.0.1.1) | VPC router |
| Third IP (e.g., 10.0.1.2) | DNS server |
| Fourth IP (e.g., 10.0.1.3) | Reserved for future use |
| Last IP (e.g., 10.0.1.255) | Broadcast address (not supported in VPC, but reserved) |

### Usable IPs Per Subnet

```
Usable IPs = 2^(32 - prefix) - 5

/24 = 256 - 5 = 251 usable IPs
/25 = 128 - 5 = 123 usable IPs
/26 =  64 - 5 =  59 usable IPs
/27 =  32 - 5 =  27 usable IPs
/28 =  16 - 5 =  11 usable IPs
```

### Sizing Considerations for Data Services

| Service | IPs Consumed | Notes |
|---------|-------------|-------|
| RDS instance | 1+ per instance | Multi-AZ needs IPs in two subnets |
| EMR cluster | 1 per node | A 50-node cluster needs 50 IPs in the subnet |
| Redshift cluster | 1 per node | Plus leader node |
| Lambda in VPC | 1 ENI per concurrent execution | Can consume many IPs quickly |
| Glue job | 1+ ENI per DPU | Scales up, needs available IPs |

**Common mistake:** Using `/28` subnets (11 usable IPs) for EMR or Lambda and running out of IPs. Size your subnets generously -- you can always have unused IPs, but you cannot easily expand a subnet.

---

## Data Engineering Analogy

| AWS Concept | Data Engineering Equivalent |
|---|---|
| Public subnet | **Public-facing API endpoint** -- the part of your system that external users interact with. Your REST API, your Airflow web UI, your Grafana dashboard. |
| Private subnet | **Internal database / processing layer** -- only accessible from within the system. Your Redshift cluster, your Spark workers, your Kafka brokers. No direct external access. |
| Internet Gateway | **Public endpoint / ingress** -- the door through which external requests enter your system. |
| NAT Gateway | **Outbound proxy** -- your internal services can call external APIs (fetch data, send alerts) but the outside world cannot initiate connections to them. |
| Route table | **Data pipeline routing** -- rules that determine where data flows. "Data from source A goes to staging table B via transformation C." |
| Multi-AZ subnets | **Replicated data stores** -- just as you replicate Kafka across brokers or maintain read replicas for your database, multi-AZ subnets give you redundancy. |

---

## Key Takeaways

1. A subnet is public or private based on its route table, not a label. Public subnets route `0.0.0.0/0` to an IGW; private subnets route it to a NAT Gateway.
2. Data services (Redshift, RDS, EMR, Glue) belong in private subnets. Only bastion hosts, load balancers, and NAT gateways belong in public subnets.
3. The Internet Gateway is the front door to your VPC. The NAT Gateway lets private instances make outbound connections.
4. Spread subnets across at least 3 AZs for high availability.
5. AWS reserves 5 IPs per subnet. A `/24` gives you 251 usable IPs, not 254.
6. Size subnets generously. EMR, Lambda, and Glue can consume many IPs. Running out of IPs causes deployment failures.
7. Route tables use longest prefix match, just like traditional routing (Module 05).
