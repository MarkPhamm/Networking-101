# Module 11: Cheatsheet -- AWS Subnets and Routing

---

## Public vs Private Subnet Comparison

| Feature | Public Subnet | Private Subnet |
|---------|--------------|----------------|
| Default route (0.0.0.0/0) | Internet Gateway (IGW) | NAT Gateway or none |
| Public IP | Instances can have public IPs | No public IPs |
| Reachable from internet | Yes (if SG/NACL allows) | No |
| Can reach internet | Yes (directly via IGW) | Yes (outbound only, via NAT GW) |
| Typical resources | Bastion hosts, ALB, NAT GW | RDS, Redshift, EMR, Glue, Kafka |
| Cost consideration | No extra cost for IGW | NAT GW has per-hour and per-GB cost |

---

## Route Table Patterns

### Public Subnet Route Table

```
Destination        Target              Description
10.0.0.0/16        local               VPC internal traffic (auto-created, cannot delete)
0.0.0.0/0          igw-xxxxxxxx        All other traffic to Internet Gateway
```

### Private Subnet Route Table

```
Destination        Target              Description
10.0.0.0/16        local               VPC internal traffic (auto-created, cannot delete)
0.0.0.0/0          nat-xxxxxxxx        All other traffic to NAT Gateway
```

### Private Subnet with VPC Peering

```
Destination        Target              Description
10.0.0.0/16        local               VPC internal traffic
172.16.0.0/16      pcx-xxxxxxxx        Traffic to peered VPC (shared services)
0.0.0.0/0          nat-xxxxxxxx        All other traffic to NAT Gateway
```

### Private Subnet with VPC Endpoint

```
Destination        Target              Description
10.0.0.0/16        local               VPC internal traffic
pl-xxxxxxxx        vpce-xxxxxxxx       S3 traffic via Gateway Endpoint (prefix list)
0.0.0.0/0          nat-xxxxxxxx        All other traffic to NAT Gateway
```

---

## Route Priority: Longest Prefix Match

Routes are evaluated by specificity. The most specific (longest prefix) match wins.

```
Example route table:
  10.0.0.0/16        local
  10.0.99.0/24       pcx-peer01
  0.0.0.0/0          igw-abc123

Packet to 10.0.99.50:
  Matches /16 and /24  -->  /24 wins  -->  pcx-peer01

Packet to 10.0.1.50:
  Matches /16 only     -->  local

Packet to 8.8.8.8:
  Matches /0 only      -->  igw-abc123
```

---

## Subnet Sizing Guide

### AWS-Reserved IPs (5 per subnet)

| IP | Purpose |
|----|---------|
| x.x.x.0 | Network address |
| x.x.x.1 | VPC router |
| x.x.x.2 | DNS server |
| x.x.x.3 | Reserved for future use |
| x.x.x.255 | Broadcast (not used, but reserved) |

### Usable IPs by Prefix

| Prefix | Total IPs | AWS Reserved | Usable IPs | Good For |
|--------|-----------|-------------|------------|----------|
| /20 | 4,096 | 5 | 4,091 | Large EMR/EKS clusters |
| /21 | 2,048 | 5 | 2,043 | Large deployments |
| /22 | 1,024 | 5 | 1,019 | Medium clusters |
| /23 | 512 | 5 | 507 | Medium deployments |
| /24 | 256 | 5 | 251 | Standard subnet (most common) |
| /25 | 128 | 5 | 123 | Smaller deployments |
| /26 | 64 | 5 | 59 | Small clusters |
| /27 | 32 | 5 | 27 | Very small, specific use |
| /28 | 16 | 5 | 11 | Minimum. Single-purpose only. |

### IP Consumption by Service

| Service | IPs Per Unit | Notes |
|---------|-------------|-------|
| EC2 instance | 1 | One primary private IP per ENI |
| RDS instance | 1-2 | Multi-AZ needs IP in standby subnet too |
| EMR node | 1 | Core/task nodes each need an IP |
| Lambda (VPC) | 1 per concurrent execution | Can spike quickly; use /20 or larger |
| Glue job | 1+ per DPU | Each DPU gets an ENI |
| EKS pod | 1 per pod | With VPC CNI, each pod gets an IP |
| NAT Gateway | 1 | Plus 1 Elastic IP |
| ALB | 1+ per AZ | AWS manages, but consumes IPs |

---

## Internet Gateway vs NAT Gateway vs NAT Instance

| Feature | Internet Gateway | NAT Gateway | NAT Instance |
|---------|-----------------|------------|--------------|
| Direction | Bidirectional | Outbound only | Outbound only |
| Managed by | AWS | AWS | You |
| Bandwidth | Unlimited | Up to 100 Gbps | Instance-dependent |
| HA | Built-in | Per-AZ (deploy one per AZ) | You manage (failover scripts) |
| Cost | Free | ~$0.045/hr + $0.045/GB | EC2 instance cost |
| Public IP | 1:1 NAT for instances | Elastic IP | Elastic IP |
| Use case | Public subnet internet access | Private subnet outbound | Cost-sensitive dev environments |
| Lives in | Attached to VPC (not a subnet) | Public subnet | Public subnet |

---

## Standard Multi-AZ Layout

### 3-AZ Production Layout (/16 VPC)

```
VPC: 10.0.0.0/16

AZ-a:
  Public:  10.0.1.0/24   (251 IPs)  -- NAT GW, Bastion, ALB
  Private: 10.0.10.0/24  (251 IPs)  -- RDS primary, EMR core

AZ-b:
  Public:  10.0.2.0/24   (251 IPs)  -- NAT GW, ALB
  Private: 10.0.20.0/24  (251 IPs)  -- RDS standby, EMR core

AZ-c:
  Public:  10.0.3.0/24   (251 IPs)  -- NAT GW, ALB
  Private: 10.0.30.0/24  (251 IPs)  -- Redshift, EMR task nodes

Reserved for future:
  10.0.4.0/24 through 10.0.9.0/24    (public expansion)
  10.0.40.0/24 through 10.0.255.0/24 (private expansion)
```

### 3-AZ Layout with Larger Private Subnets

For EMR/EKS workloads that need many IPs:

```
VPC: 10.0.0.0/16

AZ-a:
  Public:  10.0.0.0/24     (251 IPs)
  Private: 10.0.16.0/20    (4,091 IPs)  -- Large EMR clusters

AZ-b:
  Public:  10.0.1.0/24     (251 IPs)
  Private: 10.0.32.0/20    (4,091 IPs)

AZ-c:
  Public:  10.0.2.0/24     (251 IPs)
  Private: 10.0.48.0/20    (4,091 IPs)
```

---

## Common Data Workload Architectures

### ETL Pipeline (Airflow + Glue + Redshift)

```
Internet
  |
[IGW]
  |
Public Subnet:   ALB (HTTPS) --> Airflow Web Server
  |
[NAT GW]
  |
Private Subnet:  Airflow Workers --> Glue Jobs --> Redshift
                                 --> RDS (metadata)
                                 --> S3 (via VPC Endpoint)
```

### Streaming Pipeline (MSK + Flink + S3)

```
Private Subnet AZ-a:  MSK Broker 1, Flink TaskManager
Private Subnet AZ-b:  MSK Broker 2, Flink TaskManager
Private Subnet AZ-c:  MSK Broker 3, Flink JobManager
All subnets:          S3 access via VPC Gateway Endpoint
```

### Analytics Platform (Redshift + BI)

```
Internet
  |
[IGW]
  |
Public Subnet:   ALB --> Looker/Superset
  |
[NAT GW]
  |
Private Subnet:  Redshift Cluster
                 RDS (Looker metadata)
```

---

## Quick Debugging: Subnet and Routing Issues

| Symptom | Check |
|---------|-------|
| Instance cannot reach internet | Route table has 0.0.0.0/0 -> IGW (public) or NAT GW (private)? |
| Instance has no public IP | Subnet has "auto-assign public IP" enabled? Or attach an Elastic IP. |
| Cannot reach resource in same VPC | Both in same VPC? The `local` route should handle it. Check SG/NACL. |
| Cannot reach peered VPC | Route table has route to peered CIDR -> pcx-xxx? Peering accepted? DNS resolution enabled? |
| NAT Gateway not working | NAT GW in a public subnet? NAT GW's subnet has route to IGW? Private subnet routes to NAT GW? |
| "No route to host" | Check route table for destination. Missing route = packet dropped (blackhole). |
| Intermittent connectivity | AZ-specific issue? Check if NAT GW is in the same AZ as the failing instance. |
