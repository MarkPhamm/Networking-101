# Module 10: AWS VPC Fundamentals

## Overview

Everything you built in Modules 01-09 -- IP addressing, subnets, routing, firewalls, NAT -- all of it exists inside AWS. The difference is that instead of physical routers, switches, and cables, AWS gives you software-defined versions of the same components. The Amazon VPC (Virtual Private Cloud) is your own isolated network inside AWS, and it follows the exact same networking rules you already know.

If your Redshift cluster cannot reach your Airflow scheduler, the debugging process is the same: check the IP ranges, check the route tables, check the firewall rules. The concepts are identical. Only the interface has changed -- from `ifconfig` and `pfctl` to the AWS console and CLI.

---

## What Is a VPC?

A VPC is a logically isolated virtual network within AWS. When you create a VPC, you are essentially creating your own private data center network -- except it lives in AWS's infrastructure and you define it with API calls instead of rack-mounting hardware.

Every VPC has:

- **A CIDR block** -- the IP address range for the entire VPC (e.g., `10.0.0.0/16`)
- **Subnets** -- smaller slices of that CIDR, placed in specific Availability Zones
- **Route tables** -- rules that control where traffic goes (same as Module 05)
- **Security groups and NACLs** -- firewalls at the instance and subnet level (same as Module 06)
- **An internet gateway** (optional) -- the "door" to the public internet
- **A NAT gateway** (optional) -- lets private instances reach the internet without being reachable from it

If you have worked through Modules 03 (IP addressing), 05 (subnets and routing), and 06 (firewalls and NAT), you already understand every component of a VPC. AWS just gives them different names.

### Mapping to What You Already Know

| Concept from Modules 01-09 | AWS VPC Equivalent |
|---|---|
| A private network (e.g., `10.0.0.0/16`) | VPC with a CIDR block |
| Subnets (`10.0.1.0/24`, `10.0.2.0/24`) | VPC subnets |
| Routing table (`netstat -rn`) | VPC route table |
| Firewall rules (`pfctl`, `iptables`) | Security groups + NACLs |
| NAT / port forwarding | NAT gateway / internet gateway |
| A physical switch connecting devices | Implicit -- AWS handles L2 within a subnet |

---

## Regions and Availability Zones

AWS infrastructure is organized into a physical hierarchy:

### Regions

A **region** is a geographic area (e.g., `us-east-1` in Northern Virginia, `eu-west-1` in Ireland). Each region is completely independent. A VPC exists within a single region.

### Availability Zones (AZs)

Each region has multiple **Availability Zones** (typically 3-6). An AZ is one or more physical data centers with independent power, cooling, and networking. AZs within a region are connected by high-bandwidth, low-latency private fiber.

```
Region: us-east-1
  |
  +-- AZ: us-east-1a  (Data center cluster A)
  +-- AZ: us-east-1b  (Data center cluster B)
  +-- AZ: us-east-1c  (Data center cluster C)
  +-- AZ: us-east-1d  ...
  +-- AZ: us-east-1e  ...
  +-- AZ: us-east-1f  ...
```

**Why this matters for you:** When you create a subnet, you place it in a specific AZ. For high availability, you spread subnets across multiple AZs. If `us-east-1a` has an outage, your resources in `us-east-1b` keep running.

**Data engineering example:** Your RDS PostgreSQL primary is in `us-east-1a`, with a read replica in `us-east-1b`. Your EMR cluster spans `us-east-1a` and `us-east-1c`. If one AZ goes down, you still have database access and compute capacity.

---

## VPC CIDR Blocks

When you create a VPC, you choose a CIDR block -- the IP address range for the entire network. This is the same CIDR notation from Module 05.

### Rules for VPC CIDRs

- Must be between `/16` (65,536 addresses) and `/28` (16 addresses)
- Should use RFC 1918 private ranges (Module 03):
  - `10.0.0.0/8` (10.0.0.0 -- 10.255.255.255)
  - `172.16.0.0/12` (172.16.0.0 -- 172.31.255.255)
  - `192.168.0.0/16` (192.168.0.0 -- 192.168.255.255)
- You can add secondary CIDR blocks later, but you cannot change the primary one

### Common VPC CIDR Choices

| CIDR | Addresses | Good For |
|------|-----------|----------|
| `10.0.0.0/16` | 65,536 | Standard production VPC -- plenty of room |
| `10.1.0.0/16` | 65,536 | Second VPC (dev, staging) -- non-overlapping |
| `172.16.0.0/16` | 65,536 | Alternative range to avoid conflicts |
| `10.0.0.0/24` | 256 | Tiny test VPC -- too small for real use |

### The Golden Rule: Do Not Overlap

If two VPCs have overlapping CIDR blocks, they **cannot** be peered (connected). This is the number one VPC planning mistake.

```
BAD -- these overlap:
  VPC-Dev:   10.0.0.0/16   (10.0.0.0 -- 10.0.255.255)
  VPC-Prod:  10.0.0.0/16   (10.0.0.0 -- 10.0.255.255)  <-- same range!

GOOD -- these don't overlap:
  VPC-Dev:   10.0.0.0/16   (10.0.0.0 -- 10.0.255.255)
  VPC-Prod:  10.1.0.0/16   (10.1.0.0 -- 10.1.255.255)
  VPC-Stage: 10.2.0.0/16   (10.2.0.0 -- 10.2.255.255)
```

This also applies when connecting to on-premise networks via VPN. If your office network uses `10.0.0.0/16` and your VPC also uses `10.0.0.0/16`, the VPN will have routing conflicts.

---

## Default VPC vs Custom VPC

### Default VPC

Every AWS account comes with a default VPC in each region. It has:

- CIDR block `172.31.0.0/16`
- One public subnet per AZ (with auto-assign public IP enabled)
- An internet gateway already attached
- A default security group and NACL

The default VPC is convenient for quick experimentation, but you should **not** use it for production workloads. It has overly permissive defaults and a fixed CIDR that may conflict with other networks.

### Custom VPC

A VPC you create yourself. You choose:

- The CIDR block
- How many subnets and where they go
- Which subnets are public vs private
- The security rules

**Best practice:** Always create custom VPCs for real workloads. Use the default VPC only for quick tests.

---

## VPC Components Overview

Here is a summary of every major component in a VPC. Each will be covered in detail in Modules 11-14.

### Subnets (Module 11)

A subnet is a range of IP addresses within your VPC, placed in a single AZ. You split your VPC CIDR into subnets, just like you split `10.0.0.0/16` into smaller `/24` blocks in Module 05.

- **Public subnet:** Has a route to the internet gateway. Resources here can have public IPs.
- **Private subnet:** No direct internet access. Resources here are shielded from the public internet.

### Route Tables (Module 11)

Every subnet is associated with a route table. The route table determines where traffic is sent -- exactly like the routing tables from Module 05.

### Internet Gateway (IGW) (Module 11)

The IGW is a VPC component that allows communication between your VPC and the internet. Think of it as the "front door" of your VPC. Without an IGW, nothing in your VPC can reach the internet (and vice versa).

### NAT Gateway (Module 11)

A NAT gateway lets instances in private subnets initiate outbound connections to the internet (e.g., to download packages or call external APIs) without being directly reachable from the internet. Same concept as the NAT from Module 06.

### Security Groups (Module 12)

A security group is a **stateful** firewall attached to individual resources (EC2 instances, RDS databases, etc.). Just like the stateful firewalls from Module 06: if you allow outbound traffic, the return traffic is automatically allowed.

### Network ACLs (NACLs) (Module 12)

A NACL is a **stateless** firewall attached to a subnet. Rules are processed in order (numbered). You must explicitly allow both inbound and outbound traffic. This is the "first match wins" behavior from Module 06.

### VPC Peering and Transit Gateway (Module 13)

Connect VPCs to each other (peering) or build hub-and-spoke topologies (Transit Gateway).

### VPC Endpoints (Module 14)

Private connections to AWS services (S3, DynamoDB, etc.) without going through the internet.

---

## Why Data Engineers Care About VPCs

Almost every AWS data service lives inside a VPC:

| Service | VPC Relationship |
|---------|-----------------|
| **Amazon Redshift** | Cluster runs inside a VPC subnet. You control which IPs/services can reach port 5439. |
| **Amazon RDS** | Database instances live in VPC subnets. Multi-AZ deployments span subnets. |
| **Amazon EMR** | Cluster nodes (master, core, task) are EC2 instances in VPC subnets. |
| **AWS Glue** | Glue jobs run in a managed VPC, but can connect to your VPC via ENI (elastic network interface). |
| **Amazon MSK (Kafka)** | Brokers run in your VPC subnets. |
| **Amazon Airflow (MWAA)** | Runs in your VPC. Web server can be public or private. |

**If you cannot connect to your database from your ETL job, it is almost certainly a VPC networking issue:** wrong subnet, missing route, restrictive security group, or NACL blocking the port.

---

## Data Engineering Analogy

A VPC is like a **dedicated database cluster** (think a private Redshift or Postgres cluster):

| VPC Concept | Database Cluster Analogy |
|---|---|
| VPC CIDR block | The cluster's address space -- you define the boundaries |
| Subnets | Schemas or databases within the cluster -- organized partitions of the space |
| Route tables | Connection routing rules -- which clients can reach which schemas |
| Security groups | Row-level security / user privileges -- who can access each specific resource |
| NACLs | Network-level firewall -- which IPs can even attempt to connect |
| Internet gateway | The public endpoint of the cluster (if enabled) |
| NAT gateway | Outbound-only access -- the cluster can reach external APIs but outsiders cannot connect in |
| VPC peering | Database links / federated queries between separate clusters |

---

## Common Mistakes

### 1. CIDR Block Too Small

Choosing `/24` (256 addresses) for a VPC that will host multiple environments. You run out of IPs quickly once you account for subnets, AWS-reserved addresses, and growth.

**Fix:** Start with `/16` for production VPCs. You can always subdivide, but you cannot expand the primary CIDR.

### 2. Overlapping CIDR Ranges

Using `10.0.0.0/16` for every VPC. When you need to peer them or connect via VPN, you discover they cannot communicate because the ranges overlap.

**Fix:** Plan your CIDR ranges upfront. Use a spreadsheet or the planning tool in this module's exercises. Allocate non-overlapping ranges for dev, staging, prod, and shared services.

### 3. Everything in Public Subnets

Putting databases and data warehouses in public subnets because "it's easier." This exposes them to the internet.

**Fix:** Databases, clusters, and internal services belong in private subnets. Only load balancers, bastion hosts, and public APIs belong in public subnets.

### 4. Ignoring Multi-AZ

Putting all subnets in a single AZ. When that AZ has an outage, everything goes down.

**Fix:** Spread subnets across at least 2 (preferably 3) AZs. AWS services like RDS Multi-AZ and EMR can leverage this automatically.

### 5. Not Planning for VPC Peering or VPN

Picking CIDR ranges without considering future connectivity to other VPCs, on-premise networks, or partner networks.

**Fix:** Maintain a central CIDR allocation registry. Treat IP space like a shared resource.

---

## Key Takeaways

1. A VPC is your isolated network in AWS. It uses the same concepts you learned in Modules 01-09: CIDR blocks, subnets, route tables, firewalls, and NAT.
2. Regions are geographic areas; Availability Zones are isolated data center clusters within a region.
3. Choose your VPC CIDR carefully -- use RFC 1918 ranges, size between `/16` and `/28`, and never overlap with other VPCs you might need to connect.
4. Use custom VPCs for real workloads, not the default VPC.
5. Almost every AWS data service (Redshift, RDS, EMR, Glue, MSK, MWAA) lives inside a VPC. VPC networking issues are the most common cause of "cannot connect" errors in data engineering.
6. Plan for multi-AZ deployments, non-overlapping CIDRs, and private subnets for data services from day one.
