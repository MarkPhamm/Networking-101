# Module 14: AWS Data Engineering Networking (Capstone)

## What You'll Learn

This module ties together everything from Modules 00-13 by walking through real data engineering scenarios on AWS. For each scenario, you'll see the architecture, the networking components involved, and the exact configuration needed.

By the end, you'll be able to:
- Design a complete network architecture for any data engineering platform on AWS
- Diagnose "I can't connect" problems by systematically checking each networking layer
- Know which modules to revisit when something breaks

---

## Why This Module Exists

Every data engineer eventually faces the same moment: you deploy a Glue job, a Redshift cluster, or an Airflow DAG, and it can't reach something. The error message is vague. The logs say "connection timed out" or "no route to host." You start guessing.

This module eliminates the guessing. Each scenario maps directly to the modules where you learned the underlying concepts. When Redshift can't COPY from S3, you'll know it's a Module 13 problem (VPC endpoint) or a Module 12 problem (security group) -- not a mystery.

### How the Modules Connect

```
Module 01-02: SSH & Keys           → Bastion host access
Module 03: IP/DNS                  → Private DNS, endpoint resolution
Module 04: Ports                   → Service ports (5432, 5439, 443)
Module 05: Subnets/Routing         → VPC subnet design, route tables
Module 06: Firewalls/NAT           → NAT Gateway, NACLs
Module 07: LAN/WAN                 → VPC as a virtual LAN
Module 08: TCP/IP                  → Connection debugging
Module 09: Troubleshooting         → Systematic diagnosis
Module 10: VPC Fundamentals        → VPC, IGW, AZs
Module 11: AWS Subnets/Routing     → Public/private subnets, route tables
Module 12: Security Groups/NACLs   → Inbound/outbound rules
Module 13: Connectivity            → VPC endpoints, peering, TGW
```

---

## Scenario 1: SSH to EC2 (Bastion Host Pattern)

**Modules involved:** 01 (SSH), 02 (Keys), 08 (TCP/IP), 11 (Subnets)

You need to SSH into a private EC2 instance to debug a running pipeline. The instance has no public IP.

### Architecture

```
┌─── VPC: 10.0.0.0/16 ────────────────────────────────────┐
│                                                           │
│  ┌─── Public Subnet: 10.0.1.0/24 ──────┐                │
│  │                                       │                │
│  │  ┌─────────────┐   ┌──────────────┐  │                │
│  │  │ Bastion Host│   │ NAT Gateway  │  │                │
│  │  │ 10.0.1.10   │   │ 10.0.1.20    │  │                │
│  │  │ (public IP) │   │ (public IP)  │  │                │
│  │  └──────┬──────┘   └──────────────┘  │                │
│  │         │                             │                │
│  └─────────┼─────────────────────────────┘                │
│            │                                              │
│  ┌─────────┼─── Private Subnet: 10.0.2.0/24 ───┐        │
│  │         ▼                                     │        │
│  │  ┌─────────────┐   ┌──────────────┐          │        │
│  │  │ App Server  │   │ Worker Node  │          │        │
│  │  │ 10.0.2.50   │   │ 10.0.2.51    │          │        │
│  │  │ (no pub IP) │   │ (no pub IP)  │          │        │
│  │  └─────────────┘   └──────────────┘          │        │
│  └───────────────────────────────────────────────┘        │
│                                                           │
│  Internet Gateway                                        │
└──────────┬───────────────────────────────────────────────┘
           │
      Your Laptop
```

### Required Configuration

**Security Groups:**

| SG Name | Rule | Protocol | Port | Source/Destination |
|---------|------|----------|------|--------------------|
| bastion-sg | Inbound | TCP | 22 | Your IP (`x.x.x.x/32`) |
| private-sg | Inbound | TCP | 22 | bastion-sg |

**Route Tables:**

| Route Table | Destination | Target |
|-------------|-------------|--------|
| Public subnet | 0.0.0.0/0 | Internet Gateway |
| Private subnet | 0.0.0.0/0 | NAT Gateway |

**SSH Command:**

```bash
# Single command using jump host
ssh -J ec2-user@bastion-public-ip ec2-user@10.0.2.50

# Or configure in ~/.ssh/config:
Host bastion
    HostName <bastion-public-ip>
    User ec2-user
    IdentityFile ~/.ssh/bastion-key.pem

Host private-server
    HostName 10.0.2.50
    User ec2-user
    IdentityFile ~/.ssh/app-key.pem
    ProxyJump bastion
```

---

## Scenario 2: Redshift in a Private Subnet

**Modules involved:** 04 (Ports), 05 (Subnets), 11 (Subnets/Routing), 12 (Security Groups), 13 (Connectivity)

Your Redshift cluster is in a private subnet. Airflow runs COPY/UNLOAD commands that move data between Redshift and S3.

### Architecture

```
┌─── VPC: 10.0.0.0/16 ──────────────────────────────────────────┐
│                                                                 │
│  ┌─── Private Subnet AZ-a: 10.0.10.0/24 ──┐                   │
│  │                                          │                   │
│  │  ┌──────────────────┐                   │                   │
│  │  │ Redshift Cluster  │                   │                   │
│  │  │ Leader: 10.0.10.5 │ Port 5439        │                   │
│  │  │ (Enhanced VPC     │                   │                   │
│  │  │  Routing: ON)     │                   │                   │
│  │  └────────┬──────────┘                   │                   │
│  │           │                              │                   │
│  └───────────┼──────────────────────────────┘                   │
│              │                                                   │
│              │  S3 Gateway Endpoint (FREE)                       │
│              │  Route: pl-xxxxxxxx → vpce-xxxxxxxx              │
│              │                                                   │
│  ┌───────────┼─── Private Subnet AZ-b: 10.0.20.0/24 ──┐       │
│  │           │                                          │       │
│  │  ┌────────▼─────────┐                               │       │
│  │  │ Airflow (MWAA)   │                               │       │
│  │  │ 10.0.20.100      │                               │       │
│  │  │                   │                               │       │
│  │  └───────────────────┘                               │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
│                         ┌─────────┐                             │
│                         │   S3    │                              │
│                         │  Bucket │                              │
│                         └─────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### Required Configuration

**Security Groups:**

| SG Name | Rule | Protocol | Port | Source/Destination |
|---------|------|----------|------|--------------------|
| redshift-sg | Inbound | TCP | 5439 | airflow-sg |
| redshift-sg | Outbound | TCP | 443 | pl-xxxxxxxx (S3 prefix list) |
| airflow-sg | Outbound | TCP | 5439 | redshift-sg |

**Critical: Enhanced VPC Routing**

Enable Enhanced VPC Routing on the Redshift cluster. Without it, COPY/UNLOAD traffic goes over the public internet even if you have a VPC endpoint. With it enabled, traffic is forced through your VPC networking -- meaning it uses the S3 Gateway Endpoint.

**S3 VPC Endpoint:**

- Type: Gateway
- Service: `com.amazonaws.<region>.s3`
- Associated route tables: the private subnet route tables where Redshift lives

**Redshift Subnet Group:**

Must include subnets in at least 2 AZs. Even for a single-node cluster, the subnet group needs multi-AZ subnets.

### Common Failures

| Symptom | Likely Cause | Module |
|---------|-------------|--------|
| COPY command hangs | No S3 endpoint + no NAT GW | 13 |
| "Connection refused" from Airflow | SG doesn't allow 5439 from Airflow | 12 |
| UNLOAD writes nothing, no error | S3 bucket policy blocks VPC endpoint | 13 |
| Cluster unreachable from BI tool | No bastion/VPN to private subnet | 11 |

---

## Scenario 3: Airflow to RDS

**Modules involved:** 04 (Ports), 05 (Subnets), 11 (Subnets/Routing), 12 (Security Groups)

Airflow (on EC2 or MWAA) connects to RDS PostgreSQL to run pipeline metadata queries and trigger SQL-based transformations.

### Architecture

```
┌─── VPC: 10.0.0.0/16 ──────────────────────────────────────────┐
│                                                                 │
│  ┌─── Private Subnet AZ-a: 10.0.10.0/24 ──┐                   │
│  │                                          │                   │
│  │  ┌──────────────────┐                   │                   │
│  │  │ Airflow EC2 /    │                   │                   │
│  │  │ MWAA Worker      │                   │                   │
│  │  │ 10.0.10.100      │                   │                   │
│  │  └────────┬──────────┘                   │                   │
│  └───────────┼──────────────────────────────┘                   │
│              │ TCP 5432                                          │
│  ┌───────────┼─── Private Subnet AZ-b: 10.0.20.0/24 ──┐       │
│  │           ▼                                          │       │
│  │  ┌──────────────────┐                               │       │
│  │  │ RDS PostgreSQL   │                               │       │
│  │  │ Primary          │                               │       │
│  │  │ 10.0.20.50       │ Port 5432                     │       │
│  │  └──────────────────┘                               │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
│  ┌─── Private Subnet AZ-b: 10.0.21.0/24 (RDS Multi-AZ) ──┐   │
│  │                                                          │   │
│  │  ┌──────────────────┐                                   │   │
│  │  │ RDS PostgreSQL   │                                   │   │
│  │  │ Standby          │ (automatic failover)              │   │
│  │  │ 10.0.21.50       │                                   │   │
│  │  └──────────────────┘                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Required Configuration

**Security Groups:**

| SG Name | Rule | Protocol | Port | Source/Destination |
|---------|------|----------|------|--------------------|
| rds-sg | Inbound | TCP | 5432 | airflow-sg |
| airflow-sg | Outbound | TCP | 5432 | rds-sg |

**RDS Subnet Group:**

- Must span at least 2 AZs
- Use private subnets only
- Set "Publicly Accessible" to **No**

**MWAA-Specific Requirements:**

- MWAA requires **2 private subnets** in different AZs
- MWAA creates ENIs in your subnets
- The MWAA security group needs outbound access to RDS

**Connection String:**

```
postgresql://airflow_user:password@rds-endpoint.region.rds.amazonaws.com:5432/pipeline_db
```

The RDS endpoint is a DNS name that resolves to the current primary's private IP. On failover, DNS updates automatically.

---

## Scenario 4: AWS Glue Networking

**Modules involved:** 04 (Ports), 10 (VPC), 13 (VPC Endpoints)

Glue jobs run in a managed environment, but when they need to access resources in your VPC (RDS, Redshift, Elasticsearch), they need an ENI in your VPC.

### Architecture

```
┌─── VPC: 10.0.0.0/16 ──────────────────────────────────────────┐
│                                                                 │
│  ┌─── Private Subnet: 10.0.30.0/24 ───────────────────┐       │
│  │                                                      │       │
│  │  ┌──────────────────┐   ┌──────────────────┐       │       │
│  │  │ Glue ENI         │   │ Glue ENI         │       │       │
│  │  │ (auto-created)   │   │ (auto-created)   │       │       │
│  │  │ 10.0.30.10       │   │ 10.0.30.11       │       │       │
│  │  └────────┬──────────┘   └────────┬──────────┘       │       │
│  │           │                       │                  │       │
│  └───────────┼───────────────────────┼──────────────────┘       │
│              │                       │                           │
│              │  ┌────────────────────┘                           │
│              ▼  ▼                                                │
│  ┌─── Private Subnet: 10.0.20.0/24 ──┐                         │
│  │                                     │                         │
│  │  ┌──────────────────┐              │                         │
│  │  │ RDS PostgreSQL   │ Port 5432   │                         │
│  │  │ 10.0.20.50       │              │                         │
│  │  └──────────────────┘              │    S3 Gateway Endpoint  │
│  └─────────────────────────────────────┘    (Route table entry) │
│                                                    │             │
│                                              ┌─────┴─────┐      │
│                                              │    S3      │      │
│                                              └───────────┘      │
└──────────────────────────────────────────────────────────────────┘
```

### Required Configuration

**Glue Connection (VPC Type):**

- VPC: your VPC
- Subnet: a private subnet with enough free IPs (Glue creates ENIs)
- Security Group: a SG that allows access to your data sources

**Security Groups:**

| SG Name | Rule | Protocol | Port | Source/Destination |
|---------|------|----------|------|--------------------|
| glue-sg | Inbound | TCP | 0-65535 | glue-sg (self-referencing!) |
| glue-sg | Outbound | TCP | 0-65535 | glue-sg (self-referencing!) |
| glue-sg | Outbound | TCP | 5432 | rds-sg |
| glue-sg | Outbound | TCP | 443 | pl-xxxxxxxx (S3) |
| rds-sg | Inbound | TCP | 5432 | glue-sg |

**Why the self-referencing rule?** Glue creates multiple ENIs for parallel processing. These ENIs need to communicate with each other for shuffle operations (like Spark shuffles). The self-referencing SG rule allows all Glue ENIs to talk to each other.

**VPC Endpoints Needed:**

| Endpoint | Type | Why |
|----------|------|-----|
| S3 | Gateway | Read/write data lake (FREE) |
| Glue | Interface | API calls to Glue service |
| CloudWatch Logs | Interface | Ship job logs |
| KMS | Interface | If data is encrypted |

**DNS Resolution:**

Glue must resolve JDBC endpoint hostnames. If using RDS, the `*.rds.amazonaws.com` DNS name must resolve to the private IP. This works automatically within the VPC if "DNS Resolution" is enabled on the VPC (it is by default).

---

## Scenario 5: EMR Cluster

**Modules involved:** 05 (Subnets), 12 (Security Groups), 13 (Connectivity)

EMR runs a Spark cluster across multiple nodes. The master node orchestrates, core nodes store HDFS data and run tasks, and all nodes need S3 access.

### Architecture

```
┌─── VPC: 10.0.0.0/16 ──────────────────────────────────────────┐
│                                                                 │
│  ┌─── Private Subnet AZ-a: 10.0.40.0/24 ──────────────┐       │
│  │                                                      │       │
│  │  ┌──────────────┐                                   │       │
│  │  │ EMR Master   │ Port 8443 (EMR managed)           │       │
│  │  │ 10.0.40.10   │ Port 8088 (YARN ResourceManager) │       │
│  │  │              │ Port 18080 (Spark History)        │       │
│  │  └──────┬───────┘                                   │       │
│  │         │                                            │       │
│  │  ┌──────┴───────┐  ┌──────────────┐                 │       │
│  │  │ EMR Core     │  │ EMR Core     │                 │       │
│  │  │ 10.0.40.20   │  │ 10.0.40.21   │                 │       │
│  │  │ (HDFS + Task)│  │ (HDFS + Task)│                 │       │
│  │  └──────────────┘  └──────────────┘                 │       │
│  │                                                      │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                 │
│  S3 Gateway Endpoint (FREE)                                     │
│  Route: pl-xxxxxxxx → vpce-xxxxxxxx                            │
│                                                                 │
│                    ┌─────────┐                                  │
│                    │   S3    │ (replaces HDFS for most jobs)    │
│                    └─────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Required Configuration

**Security Groups (EMR creates two managed SGs):**

| SG Name | Rule | Protocol | Port | Source/Destination |
|---------|------|----------|------|--------------------|
| EMR-Master-SG | Inbound | TCP | All | EMR-Core-SG |
| EMR-Master-SG | Inbound | TCP | All | EMR-Master-SG (self) |
| EMR-Core-SG | Inbound | TCP | All | EMR-Master-SG |
| EMR-Core-SG | Inbound | TCP | All | EMR-Core-SG (self) |
| EMR-Additional-SG | Inbound | TCP | 22 | bastion-sg (SSH access) |

**Why so many open ports?** EMR nodes communicate over many dynamic ports for HDFS replication, YARN task assignment, Spark shuffle, and more. The managed SGs allow all traffic between master and core nodes.

**S3 VPC Endpoint:** Required. Without it, every S3 read/write goes through NAT Gateway. EMR jobs processing terabytes of S3 data will generate massive NAT fees.

---

## Scenario 6: S3 Access Patterns

**Modules involved:** 13 (VPC Endpoints)

Not all S3 access is the same. The right endpoint depends on your use case.

### Gateway Endpoint (Most Common)

```
Use case: Redshift COPY, Glue ETL, EMR Spark, any S3 access within the same region

How it works:
  Route table entry → S3 prefix list → AWS backbone

Cost: FREE
Limitation: Same region only
```

### Interface Endpoint (PrivateLink)

```
Use case: Cross-region S3 access, on-prem access via Direct Connect/VPN,
          applications that need DNS-based endpoint resolution

How it works:
  ENI in your subnet → Private DNS → S3 over AWS backbone

Cost: ~$0.01/hr per AZ + $0.01/GB
Advantage: Works cross-region and from on-prem
```

### Decision

```
Is S3 in the same region as your VPC?
├── YES → Gateway Endpoint (FREE, always use this)
└── NO → Interface Endpoint (costs money, but keeps traffic private)

Accessing S3 from on-prem via DX/VPN?
├── YES → Interface Endpoint (provides a private IP to route to)
└── NO → Gateway Endpoint
```

---

## Scenario 7: Common "I Can't Connect" Problems

This is the troubleshooting map. When something can't connect, work through this list:

### Systematic Debugging Order

```
1. Security Group (Module 12)
   └── Is the port allowed inbound on the destination?
   └── Is the source SG or CIDR in the inbound rule?

2. Network ACL (Module 12)
   └── Are both inbound AND outbound rules allowing the traffic?
   └── Check ephemeral port range (1024-65535) for return traffic

3. Route Table (Module 11)
   └── Does the source subnet have a route to the destination?
   └── For private subnets: is there a NAT GW route for internet access?

4. VPC Endpoint (Module 13)
   └── For AWS services: is the right endpoint configured?
   └── Is the endpoint associated with the correct route table?

5. DNS Resolution (Module 03)
   └── Does the hostname resolve to the right IP?
   └── Is VPC DNS resolution enabled?

6. Subnet Placement (Module 11)
   └── Is the resource in a public or private subnet?
   └── Does it need a public IP?

7. Service-Specific Config
   └── RDS: "Publicly Accessible" setting
   └── Redshift: Enhanced VPC Routing
   └── Glue: VPC Connection configured
   └── MWAA: requires 2 private subnets
```

### Per-Service Quick Diagnosis

**Redshift won't COPY from S3:**
1. Check Enhanced VPC Routing is ON
2. Check S3 Gateway Endpoint exists and is associated with Redshift's subnet route table
3. Check Redshift SG allows outbound to S3 prefix list on port 443
4. Check IAM role attached to Redshift has S3 read permissions

**Airflow can't connect to RDS:**
1. Check RDS SG allows inbound TCP 5432 from Airflow SG
2. Check RDS is not set to "Publicly Accessible: Yes" while Airflow is in a private subnet (DNS resolves to public IP, which is unreachable from private subnet)
3. Check route table: Airflow subnet can route to RDS subnet
4. Check RDS subnet group includes the correct subnets

**Glue job fails with connection timeout:**
1. Check Glue connection has correct VPC, subnet, SG
2. Check SG has self-referencing rules (Glue ENIs need to talk to each other)
3. Check S3 Gateway Endpoint exists (Glue needs S3 for reading data and writing logs)
4. Check the subnet has enough free IP addresses for Glue ENIs
5. Check DNS resolution is enabled on the VPC

**EMR can't read from S3:**
1. Check S3 Gateway Endpoint exists and is on EMR's subnet route table
2. Check EMR security groups allow outbound HTTPS (443) to S3 prefix list
3. Check IAM role (EMR_EC2_DefaultRole) has S3 permissions

**MWAA environment creation fails:**
1. Check you have 2 private subnets in different AZs
2. Check subnets have NAT Gateway route for internet access
3. Check SG allows outbound HTTPS (443)
4. Check SG has self-referencing inbound rule (MWAA workers communicate)

---

## The Complete Picture

Here's how a full data engineering platform looks when all the networking is properly configured:

```
┌─── VPC: 10.0.0.0/16 ──────────────────────────────────────────────────────┐
│                                                                             │
│  ┌─── Public Subnets ─────────────────────────────────────┐                │
│  │  Bastion (10.0.1.0/24)    NAT GW (10.0.2.0/24)        │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                             │
│  ┌─── Private App Subnets ────────────────────────────────┐                │
│  │  Airflow/MWAA (10.0.10.0/24, 10.0.11.0/24)            │                │
│  │  Glue ENIs   (10.0.12.0/24, 10.0.13.0/24)             │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                             │
│  ┌─── Private Data Subnets ───────────────────────────────┐                │
│  │  Redshift    (10.0.20.0/24, 10.0.21.0/24)             │                │
│  │  RDS         (10.0.22.0/24, 10.0.23.0/24)             │                │
│  │  EMR         (10.0.24.0/24, 10.0.25.0/24)             │                │
│  └────────────────────────────────────────────────────────┘                │
│                                                                             │
│  VPC Endpoints:                                                             │
│    - S3 Gateway (FREE) ─── route table entry                               │
│    - Glue Interface ─── ENI in private subnet                              │
│    - CloudWatch Logs Interface ─── ENI in private subnet                   │
│    - Secrets Manager Interface ─── ENI in private subnet                   │
│    - KMS Interface ─── ENI in private subnet                               │
│                                                                             │
│  Security Groups:                                                           │
│    bastion-sg:   22 from your IP                                           │
│    airflow-sg:   443 outbound, 5432 → rds-sg, 5439 → redshift-sg          │
│    redshift-sg:  5439 from airflow-sg, 443 → S3                           │
│    rds-sg:       5432 from airflow-sg, 5432 from glue-sg                   │
│    glue-sg:      self-ref all ports, 5432 → rds-sg, 443 → S3              │
│    emr-master:   all from emr-core, self-ref                               │
│    emr-core:     all from emr-master, self-ref                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

1. **Every "I can't connect" problem maps to a specific networking layer.** Security groups, route tables, VPC endpoints, DNS -- check them in order.
2. **S3 Gateway Endpoints should be in every VPC.** They're free. Redshift, Glue, and EMR all benefit.
3. **Security groups are the most common cause of connection failures.** Always check the port, protocol, and source SG/CIDR.
4. **Glue and MWAA both need self-referencing SG rules.** Their workers communicate with each other.
5. **Enhanced VPC Routing on Redshift** is required for VPC endpoints to work with COPY/UNLOAD.
6. **RDS "Publicly Accessible" is a trap.** Set it to No for private subnets. If set to Yes, DNS resolves to the public IP, which is unreachable from within a private subnet.
7. **When in doubt, trace the packet path.** Source → SG outbound → route table → (NAT/endpoint/peering) → destination route table → destination SG inbound.
