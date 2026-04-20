# Module 10: Cheatsheet -- AWS VPC Fundamentals

---

## VPC CIDR Ranges

### RFC 1918 Private Ranges (use these for VPCs)

| Range | CIDR | Total Addresses | Typical VPC Use |
|-------|------|-----------------|-----------------|
| 10.0.0.0 -- 10.255.255.255 | 10.0.0.0/8 | 16,777,216 | Most common. Carve /16 blocks for each VPC. |
| 172.16.0.0 -- 172.31.255.255 | 172.16.0.0/12 | 1,048,576 | Alternative when 10.x is taken by on-prem. |
| 192.168.0.0 -- 192.168.255.255 | 192.168.0.0/16 | 65,536 | Small environments. Often conflicts with home networks. |

### VPC CIDR Size Limits

| Prefix | Addresses | Good For | Notes |
|--------|-----------|----------|-------|
| /16 | 65,536 | Production VPC | Recommended starting size. 256 possible /24 subnets. |
| /17 | 32,768 | Large environment | 128 possible /24 subnets. |
| /18 | 16,384 | Medium environment | 64 possible /24 subnets. |
| /20 | 4,096 | Small environment | 16 possible /24 subnets. |
| /24 | 256 | Tiny test VPC | Only 1 subnet possible. Too small for real use. |
| /28 | 16 | Minimum allowed | 11 usable IPs. Only for isolated single-purpose VPCs. |

---

## VPC Limits (per region, default)

| Resource | Default Limit | Can Increase? |
|----------|--------------|---------------|
| VPCs per region | 5 | Yes |
| Subnets per VPC | 200 | Yes |
| Route tables per VPC | 200 | Yes |
| Routes per route table | 50 | Yes (up to 1,000) |
| Internet gateways per VPC | 1 | No |
| NAT gateways per AZ | 5 | Yes |
| Elastic IPs per region | 5 | Yes |
| Security groups per VPC | 2,500 | Yes |
| Rules per security group | 60 inbound + 60 outbound | Yes |
| Network ACLs per VPC | 200 | Yes |
| Rules per NACL | 20 inbound + 20 outbound | Yes (up to 40) |
| VPC peering connections per VPC | 50 | Yes (up to 125) |

---

## Key VPC Components

| Component | What It Does | Analogy |
|-----------|-------------|---------|
| **VPC** | Isolated virtual network | Your private data center network |
| **Subnet** | IP range within a VPC, placed in one AZ | A floor/wing of the data center |
| **Route Table** | Rules for where traffic goes | Directory signs in the building |
| **Internet Gateway (IGW)** | Connects VPC to internet | The building's front door |
| **NAT Gateway** | Lets private resources reach internet outbound | One-way exit door (can leave, cannot enter) |
| **Security Group** | Stateful firewall per resource | Lock on each individual room |
| **NACL** | Stateless firewall per subnet | Security checkpoint at each floor |
| **VPC Peering** | Connects two VPCs | A hallway between two buildings |
| **Transit Gateway** | Hub connecting multiple VPCs | Central lobby connecting many buildings |
| **VPC Endpoint** | Private connection to AWS services | Internal mail system (no need to go outside) |
| **Elastic IP** | Static public IP | A permanent mailing address |
| **ENI** | Virtual network interface | A network port on a device |

---

## Default VPC vs Custom VPC

| Feature | Default VPC | Custom VPC |
|---------|------------|------------|
| CIDR | 172.31.0.0/16 (fixed) | You choose (/16 to /28) |
| Subnets | One public per AZ (auto-created) | You create and place them |
| Internet Gateway | Attached by default | You attach if needed |
| Public IPs | Auto-assigned in default subnets | You control per subnet |
| Security | Overly permissive defaults | You define from scratch |
| Use case | Quick experiments only | All real workloads |

---

## Common VPC Architectures

### Single VPC (simple)

```
VPC: 10.0.0.0/16
  Public subnets:   10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24
  Private subnets:  10.0.10.0/24, 10.0.20.0/24, 10.0.30.0/24
  IGW + NAT Gateway
```

Best for: Small teams, single application, getting started.

### Multi-VPC (per environment)

```
VPC-Dev:     10.0.0.0/16
VPC-Staging: 10.1.0.0/16
VPC-Prod:    10.2.0.0/16
VPC-Shared:  10.10.0.0/16  (shared services: CI/CD, monitoring, bastion)

Connected via: VPC Peering or Transit Gateway
```

Best for: Isolating environments, compliance requirements, larger teams.

### Hub-and-Spoke (enterprise)

```
Transit Gateway (hub)
  |-- VPC-Prod:    10.0.0.0/16
  |-- VPC-Dev:     10.1.0.0/16
  |-- VPC-Staging: 10.2.0.0/16
  |-- VPC-Shared:  10.10.0.0/16
  |-- On-prem:     172.16.0.0/12 (via VPN or Direct Connect)
```

Best for: Many VPCs, on-prem connectivity, centralized networking.

---

## CIDR Planning Checklist

1. **Start with /16 for production.** You can always subdivide, but you cannot expand.
2. **Assign non-overlapping ranges.** Use a spreadsheet or IP address management (IPAM) tool.
3. **Reserve ranges for future VPCs.** Do not use all of 10.0.0.0/8 immediately.
4. **Account for on-prem overlap.** Check what ranges your corporate network uses before choosing VPC CIDRs.
5. **Use consistent naming.** `10.0.0.0/16` for prod, `10.1.0.0/16` for dev, etc.
6. **Document everything.** Future you will thank present you.

---

## Quick Reference: Regions and AZs

### Major Regions

| Region Code | Location | AZs | Common Use |
|-------------|----------|-----|------------|
| us-east-1 | N. Virginia | 6 | Default for many services, largest region |
| us-west-2 | Oregon | 4 | Popular alternative, good for DR |
| eu-west-1 | Ireland | 3 | Europe primary |
| ap-southeast-1 | Singapore | 3 | Asia Pacific |

### AZ Naming

- AZ names (e.g., `us-east-1a`) are mapped differently per AWS account
- `us-east-1a` in your account may be a different physical data center than `us-east-1a` in another account
- Use AZ IDs (e.g., `use1-az1`) for consistent cross-account references

---

## Data Services and VPC Placement

| Service | VPC Required? | Typical Subnet | Key Port |
|---------|--------------|----------------|----------|
| Amazon Redshift | Yes | Private | 5439 |
| Amazon RDS | Yes | Private | 5432 (PG), 3306 (MySQL) |
| Amazon EMR | Yes | Private | 8088 (YARN), 18080 (Spark) |
| AWS Glue | Uses managed VPC + your VPC via ENI | Private | N/A (managed) |
| Amazon MSK (Kafka) | Yes | Private | 9092, 9094 |
| Amazon MWAA (Airflow) | Yes | Private (web server can be public) | 8080 |
| Amazon ElastiCache | Yes | Private | 6379 (Redis), 11211 (Memcached) |
| Amazon OpenSearch | Yes (VPC mode) | Private | 443 |
| AWS Lambda | Optional (VPC mode for private resources) | Private | N/A |
| Amazon S3 | No (but use VPC Endpoint) | N/A | 443 (HTTPS) |
| Amazon DynamoDB | No (but use VPC Endpoint) | N/A | 443 (HTTPS) |
