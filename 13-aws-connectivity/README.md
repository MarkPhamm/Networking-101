# Module 13: AWS Connectivity

## What You'll Learn

- VPC Peering: how two VPCs communicate directly (and why it's non-transitive)
- Transit Gateway: hub-and-spoke architecture for connecting many VPCs
- VPC Endpoints: keeping traffic off the public internet (and saving money)
- Gateway endpoints vs Interface endpoints (PrivateLink): when to use which
- VPN: encrypted tunnels over the internet to on-premises networks
- Direct Connect: dedicated physical connections to AWS
- A decision matrix for choosing the right connectivity option

---

## Why This Module Exists

You have built VPCs with subnets, routing, and security groups. Now comes the question every data engineer eventually faces: how do I connect VPC A to VPC B? How does my Redshift cluster access S3 without traffic leaving the AWS network? How does my on-prem data center push files into an S3 bucket?

These are connectivity problems. Getting them wrong doesn't just break your pipelines -- it costs you real money. A single misconfigured NAT Gateway can silently add thousands of dollars to your monthly bill when your Glue jobs process terabytes through it.

### Data engineering analogy

Think of connectivity options like data integration patterns:
- **VPC Peering** is like database federation -- two databases talk directly, but the relationship is point-to-point and doesn't chain.
- **Transit Gateway** is like a central data hub -- everything connects through a single routing center, and any spoke can reach any other spoke.
- **VPC Endpoints** are like direct internal API access -- you skip the public internet entirely, the way a database's internal connection pool skips the load balancer.

---

## VPC Peering

VPC Peering creates a **direct network route** between two VPCs. Traffic travels over the AWS backbone, never touching the public internet.

### How It Works

```
┌──────────────────┐         ┌──────────────────┐
│   VPC A           │  Peering │   VPC B           │
│   10.0.0.0/16     │◄───────►│   10.1.0.0/16     │
│                    │         │                    │
│  ┌──────────────┐ │         │ ┌──────────────┐  │
│  │ Redshift     │ │         │ │ Airflow      │  │
│  │ 10.0.1.50    │─┼─────────┼─│ 10.1.2.100   │  │
│  └──────────────┘ │         │ └──────────────┘  │
└──────────────────┘         └──────────────────┘
```

### Key Rules

1. **No overlapping CIDRs.** If both VPCs use `10.0.0.0/16`, you cannot peer them. AWS would have no way to route traffic -- the same IP range exists in both places.

2. **Non-transitive.** If VPC A peers with VPC B, and VPC B peers with VPC C, VPC A **cannot** reach VPC C through VPC B. You need a separate peering connection between A and C.

```
A ◄──► B ◄──► C

A can reach B?  YES
B can reach C?  YES
A can reach C?  NO  (non-transitive!)

To fix: A ◄──► C  (separate peering needed)
```

3. **Cross-region and cross-account supported.** Peering works across AWS regions and between different AWS accounts.

4. **Route table entries required.** Both VPCs need route table entries pointing to the peering connection for the other VPC's CIDR.

### When to Use VPC Peering

- You have **2-3 VPCs** that need to communicate
- The relationship is simple and static
- You want the lowest latency and simplest setup
- Example: your production VPC talks to a shared services VPC

### When NOT to Use VPC Peering

- You have **many VPCs** (peering connections grow as n*(n-1)/2)
- You need transitive routing
- 10 VPCs fully meshed = 45 peering connections. That's unmanageable.

---

## Transit Gateway (TGW)

Transit Gateway is a **regional network hub**. You attach VPCs (and VPN/Direct Connect connections) to it, and the TGW handles routing between all of them.

### How It Works

```
                    ┌─────────────────┐
                    │ Transit Gateway  │
                    │   (Regional Hub) │
                    └────┬───┬───┬────┘
                         │   │   │
              ┌──────────┘   │   └──────────┐
              ▼              ▼              ▼
       ┌────────────┐ ┌────────────┐ ┌────────────┐
       │  VPC A      │ │  VPC B      │ │  VPC C      │
       │ 10.0.0.0/16 │ │ 10.1.0.0/16│ │ 10.2.0.0/16│
       │ (Airflow)   │ │ (Redshift)  │ │ (Data Lake) │
       └────────────┘ └────────────┘ └────────────┘
```

### Key Features

| Feature | VPC Peering | Transit Gateway |
|---------|-------------|-----------------|
| Topology | Point-to-point | Hub-and-spoke |
| Transitive routing | No | Yes |
| Max connections | ~125 per VPC | 5,000 attachments |
| Cost | Free (data transfer only) | Hourly + data processing |
| Complexity at scale | Grows quadratically | Grows linearly |
| Cross-region | Yes (inter-region peering) | Yes (TGW peering) |
| Bandwidth | No limit | Up to 50 Gbps per attachment |

### Transitive Routing Solved

With Transit Gateway, if VPC A and VPC C are both attached, they can reach each other through the TGW. No separate connection needed.

```
A ──► TGW ◄── B
       ▲
       │
       C

A can reach B?  YES (through TGW)
A can reach C?  YES (through TGW)
B can reach C?  YES (through TGW)
```

### When to Use Transit Gateway

- You have **4+ VPCs** that need to communicate
- You need transitive routing
- You connect on-premises networks alongside VPCs
- You want centralized routing management
- Example: your organization has separate VPCs for dev, staging, prod, shared services, and security

---

## VPC Endpoints

VPC Endpoints let resources in your VPC access AWS services **without traversing the public internet**. Traffic stays on the AWS network.

This is the section that will save you the most money as a data engineer.

### The Problem Without Endpoints

Without a VPC endpoint, a Redshift cluster in a private subnet that needs to COPY data from S3 must route traffic like this:

```
Redshift (private subnet)
    │
    ▼
NAT Gateway (public subnet)     ← $0.045/GB data processing!
    │
    ▼
Internet Gateway
    │
    ▼
Public Internet
    │
    ▼
S3 (public endpoint)
```

If your Redshift cluster loads 10 TB/month from S3, you pay **$450/month** just in NAT Gateway data processing fees. That's $5,400/year for the privilege of routing traffic through the public internet to reach a service that's already inside AWS.

### The Solution: VPC Endpoints

```
Redshift (private subnet)
    │
    ▼
S3 Gateway Endpoint            ← FREE!
    │
    ▼
S3 (private, on AWS backbone)
```

Zero data processing fees. Traffic never leaves the AWS network.

### Two Types of VPC Endpoints

#### Gateway Endpoints

| Feature | Details |
|---------|---------|
| Supported services | **S3** and **DynamoDB** only |
| Cost | **Free** (no hourly charge, no data processing charge) |
| How it works | Adds a route table entry pointing to a prefix list |
| Availability | Highly available by default |
| Configuration | Associate with route tables |

A gateway endpoint is a route table entry. When your route table has a rule that says "traffic for S3 prefix list goes to endpoint vpce-xxxx," packets destined for S3 IP ranges get routed directly to S3 over the AWS backbone.

```
Route Table:
Destination          Target
10.0.0.0/16          local
pl-xxxxxxxx (S3)     vpce-xxxxxxxx (Gateway Endpoint)
0.0.0.0/0            nat-xxxxxxxx
```

#### Interface Endpoints (PrivateLink)

| Feature | Details |
|---------|---------|
| Supported services | Most AWS services (SQS, SNS, KMS, Secrets Manager, CloudWatch, etc.) |
| Cost | ~$0.01/hr per AZ + $0.01/GB data processed |
| How it works | Creates an ENI (Elastic Network Interface) in your subnet |
| Availability | Deploy in multiple AZs for HA |
| Configuration | Gets a private DNS name that resolves to the ENI's private IP |

An interface endpoint places a network interface inside your subnet. When your application calls the AWS service, DNS resolves to the private IP of the ENI instead of the public endpoint.

```
Before (without PrivateLink):
  Your app → public DNS → Internet → AWS service

After (with PrivateLink):
  Your app → private DNS → ENI in your subnet → AWS service
```

### Why Data Engineers MUST Know VPC Endpoints

Every major data engineering service on AWS benefits from VPC endpoints:

| Scenario | Without Endpoint | With Endpoint | Monthly Savings (10 TB) |
|----------|-----------------|---------------|------------------------|
| Redshift COPY/UNLOAD from S3 | NAT GW: $450/mo | S3 Gateway: $0 | **$450** |
| Glue jobs reading/writing S3 | NAT GW: $450/mo | S3 Gateway: $0 | **$450** |
| EMR processing S3 data | NAT GW: $450/mo | S3 Gateway: $0 | **$450** |
| Airflow logging to CloudWatch | NAT GW + internet | Interface endpoint: ~$20/mo | **$430** |

The S3 Gateway endpoint is the single highest-ROI networking configuration in AWS data engineering. It costs nothing and can save hundreds or thousands per month.

### Setting Up an S3 Gateway Endpoint

1. Go to VPC Console > Endpoints > Create Endpoint
2. Select "AWS services" as the service category
3. Search for and select `com.amazonaws.<region>.s3` (Gateway type)
4. Select the VPC
5. Select the route tables to associate with
6. (Optional) Add a VPC endpoint policy to restrict access

Once created, any route table you associated automatically gets an entry for the S3 prefix list. Redshift, Glue, EMR, and any other service in those subnets can now reach S3 without a NAT Gateway.

---

## VPN (Virtual Private Network)

AWS VPN creates an **encrypted tunnel over the public internet** between your on-premises network and your VPC.

### Site-to-Site VPN

```
┌──────────────┐       Encrypted Tunnel       ┌──────────────┐
│ On-Premises   │ ◄═══════════════════════════► │   AWS VPC     │
│ Data Center   │      (over public internet)   │               │
│               │                               │               │
│ Customer      │                               │ Virtual       │
│ Gateway (CGW) │                               │ Private       │
│               │                               │ Gateway (VGW) │
└──────────────┘                               └──────────────┘
```

| Feature | Details |
|---------|---------|
| Bandwidth | Up to 1.25 Gbps per tunnel (2 tunnels per connection) |
| Latency | Variable (internet-dependent) |
| Setup time | Minutes to hours |
| Cost | ~$0.05/hr + data transfer |
| Encryption | IPsec |
| Redundancy | Two tunnels per connection (different AZs) |

### When to Use VPN

- You need on-prem to AWS connectivity **quickly**
- Data volumes are moderate (not sustained multi-Gbps)
- You're fine with internet-dependent latency
- Example: nightly batch jobs push data from on-prem databases to S3

---

## Direct Connect (DX)

Direct Connect provides a **dedicated physical connection** from your data center to AWS. No internet involved.

```
┌──────────────┐     Dedicated Fiber      ┌──────────────┐
│ On-Premises   │ ◄══════════════════════► │   AWS         │
│ Data Center   │   (private, no internet) │   Region      │
│               │                          │               │
│               │   via colocation         │               │
│               │   facility (e.g., Equinix)               │
└──────────────┘                          └──────────────┘
```

| Feature | Details |
|---------|---------|
| Bandwidth | 1 Gbps, 10 Gbps, or 100 Gbps (dedicated); 50 Mbps - 10 Gbps (hosted) |
| Latency | Consistent, low (no internet hops) |
| Setup time | Weeks to months (physical installation) |
| Cost | Port hours + data transfer (cheaper than internet transfer at scale) |
| Encryption | Not encrypted by default (add VPN over DX for encryption) |
| Redundancy | Need two connections for HA |

### When to Use Direct Connect

- You transfer **large volumes** of data regularly (multi-TB/day)
- You need **consistent, low latency**
- You have compliance requirements for private connectivity
- Example: streaming real-time data from on-prem Kafka to AWS, or large nightly data warehouse loads

---

## Decision Matrix: Which Connectivity Option?

| Question | VPC Peering | Transit Gateway | VPN | Direct Connect | VPC Endpoint |
|----------|-------------|-----------------|-----|----------------|--------------|
| **Connecting what?** | VPC to VPC | Many VPCs + on-prem | On-prem to VPC | On-prem to VPC | VPC to AWS service |
| **How many connections?** | 2-3 | 4+ | 1-2 | 1-2 | Per service |
| **Data volume** | Any | Any | < 1.25 Gbps | Multi-Gbps | Any |
| **Setup time** | Minutes | Minutes | Minutes-hours | Weeks-months | Minutes |
| **Transitive?** | No | Yes | Via TGW | Via TGW | N/A |
| **Typical monthly cost** | Data transfer only | $36+ hourly + data | $36+ hourly + data | $100s-$1000s+ | Free (GW) or ~$20+ (Interface) |

### Decision Flowchart

```
Need to connect to an AWS service (S3, DynamoDB, SQS, etc.)?
├── YES → Use a VPC Endpoint (Gateway for S3/DynamoDB, Interface for others)
└── NO → Connecting VPCs or on-prem?
    ├── VPC to VPC
    │   ├── 2-3 VPCs, simple topology → VPC Peering
    │   └── 4+ VPCs, need transitive routing → Transit Gateway
    └── On-prem to AWS
        ├── Need it quickly, moderate data → VPN
        ├── High bandwidth, consistent latency → Direct Connect
        └── Both? → Direct Connect + VPN backup
```

---

## Putting It Together: A Data Platform Example

Here's a realistic architecture for a data engineering team:

```
                         ┌─────────────────────┐
                         │   Transit Gateway     │
                         └──┬────┬────┬────┬───┘
                            │    │    │    │
              ┌─────────────┘    │    │    └─────────────┐
              ▼                  ▼    ▼                  ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Prod VPC      │  │ Dev VPC       │  │ Shared Svc   │
     │ 10.0.0.0/16   │  │ 10.1.0.0/16  │  │ 10.2.0.0/16  │
     │               │  │               │  │               │
     │ Redshift      │  │ Dev Redshift  │  │ Airflow       │
     │ EMR           │  │ Glue Dev      │  │ Monitoring    │
     │ Prod Glue     │  │               │  │               │
     └──────┬────────┘  └──────┬────────┘  └──────┬────────┘
            │                  │                   │
            └──────────────────┼───────────────────┘
                               │
                    S3 Gateway Endpoint (FREE)
                               │
                         ┌─────┴─────┐
                         │    S3      │
                         │ Data Lake  │
                         └───────────┘
```

- **Transit Gateway** connects all VPCs (transitive routing, centralized management)
- **S3 Gateway Endpoint** in each VPC for free, fast access to S3
- **Interface Endpoints** for CloudWatch, Secrets Manager, KMS as needed
- **VPN or Direct Connect** from on-prem to Transit Gateway

---

## Key Takeaways

1. **VPC Peering** is simple and free but doesn't scale past a handful of VPCs and is non-transitive.
2. **Transit Gateway** is the hub-and-spoke solution for complex multi-VPC architectures.
3. **S3 Gateway Endpoint** should be in every VPC that touches S3. It's free. There is no reason not to have one.
4. **Interface Endpoints** cost money but keep traffic private and avoid NAT Gateway fees for supported services.
5. **VPN** is the quick way to connect on-prem; **Direct Connect** is the serious way.
6. The choice between these options often comes down to: how many things are connecting, how much data is flowing, and how much latency you can tolerate.

---

## What's Next

In [Module 14](../14-aws-data-eng-networking/), we bring everything together. You'll design complete network architectures for real data engineering scenarios -- Redshift, Glue, EMR, Airflow, RDS -- combining VPCs, subnets, security groups, and connectivity options into production-ready designs.
