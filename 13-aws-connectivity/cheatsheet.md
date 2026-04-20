# Module 13: Cheatsheet -- AWS Connectivity

---

## Connectivity Options Comparison

| Feature | VPC Peering | Transit Gateway | Site-to-Site VPN | Direct Connect |
|---------|-------------|-----------------|------------------|----------------|
| **Connects** | VPC to VPC | VPCs + on-prem | On-prem to VPC | On-prem to VPC |
| **Topology** | Point-to-point | Hub-and-spoke | Point-to-point | Point-to-point |
| **Transitive** | No | Yes | Via TGW only | Via TGW only |
| **Bandwidth** | No hard limit | 50 Gbps/attachment | 1.25 Gbps/tunnel | 1-100 Gbps |
| **Latency** | Lowest (AWS backbone) | Low (extra hop) | Variable (internet) | Consistent, low |
| **Encryption** | In-transit by default | In-transit by default | IPsec | Not by default |
| **Setup time** | Minutes | Minutes | Minutes-hours | Weeks-months |
| **Cost** | Data transfer only | Hourly + per-GB | Hourly + per-GB | Port-hours + per-GB |
| **Cross-region** | Yes | Yes (TGW peering) | Yes | Yes (via DX Gateway) |
| **Cross-account** | Yes | Yes | Yes | Yes |
| **Max connections** | 125/VPC | 5,000 attachments | 10/VGW | Multiple VIFs |
| **CIDR overlap** | Not allowed | Not allowed | Not allowed | Not allowed |

---

## VPC Endpoint Types

| Feature | Gateway Endpoint | Interface Endpoint (PrivateLink) |
|---------|-----------------|----------------------------------|
| **Services** | S3, DynamoDB | 100+ AWS services (SQS, SNS, KMS, CloudWatch, etc.) |
| **Cost** | FREE | ~$0.01/hr per AZ + $0.01/GB |
| **Mechanism** | Route table entry (prefix list) | ENI in your subnet |
| **DNS** | Uses default S3/DynamoDB endpoints | Private DNS name resolves to ENI IP |
| **Security** | VPC endpoint policy | VPC endpoint policy + Security Groups |
| **HA** | Built-in | Deploy in multiple AZs |
| **Configuration** | Associate with route tables | Select subnets and security groups |

---

## Cost Comparison: S3 Access Paths

All costs are approximate and based on us-east-1 pricing.

| Access Path | Data Processing | Hourly Cost | 1 TB/month | 10 TB/month |
|-------------|----------------|-------------|------------|-------------|
| NAT Gateway | $0.045/GB | $0.045/hr | $46.08 | $450+ |
| S3 Gateway Endpoint | FREE | FREE | $0 | $0 |
| S3 Interface Endpoint | $0.01/GB | $0.01/hr per AZ | ~$17 | ~$107 |
| Public internet (IGW) | FREE | FREE | $0 (but insecure) | $0 (but insecure) |

**Rule of thumb:** Always use the S3 Gateway Endpoint. It is free and there is zero downside.

---

## VPC Peering Quick Reference

### Create Peering Connection

```
VPC A (requester) → Create Peering Connection → VPC B (accepter)
VPC B → Accept Peering Connection
```

### Required Route Table Entries

```
VPC A route table:
  Destination: 10.1.0.0/16 (VPC B CIDR)    Target: pcx-xxxxxxxx

VPC B route table:
  Destination: 10.0.0.0/16 (VPC A CIDR)    Target: pcx-xxxxxxxx
```

### Security Group Reference

Security groups can reference a peered VPC's security group by ID:

```
Inbound rule:  Allow TCP 5432 from sg-xxxxxxxx (SG in peered VPC)
```

---

## Transit Gateway Quick Reference

### Attach VPCs

```
TGW attachment = TGW + VPC + Subnet(s) in the VPC
```

Each VPC attachment requires specifying one subnet per AZ. The TGW creates an ENI in each specified subnet.

### TGW Route Table

```
Route                    Attachment         Type
10.0.0.0/16             vpc-a-attachment    propagated
10.1.0.0/16             vpc-b-attachment    propagated
10.2.0.0/16             vpc-c-attachment    propagated
0.0.0.0/0               vpn-attachment      static
```

### VPC Route Table (for TGW)

```
Destination          Target
10.0.0.0/16          local
10.1.0.0/16          tgw-xxxxxxxx
10.2.0.0/16          tgw-xxxxxxxx
0.0.0.0/0            nat-xxxxxxxx
```

---

## VPC Endpoint Setup Checklist

### S3 Gateway Endpoint

- [ ] Create endpoint (select `com.amazonaws.<region>.s3`, type: Gateway)
- [ ] Associate with all route tables that need S3 access
- [ ] (Optional) Add endpoint policy to restrict to specific buckets
- [ ] Verify: route table shows `pl-xxxxxxxx → vpce-xxxxxxxx`

### Interface Endpoint

- [ ] Create endpoint (select the service, type: Interface)
- [ ] Select VPC and subnets (one per AZ for HA)
- [ ] Assign security group (allow inbound from your resources)
- [ ] Enable private DNS (if available)
- [ ] Verify: `nslookup <service-endpoint>` resolves to private IP

---

## Common Data Engineering Endpoint Needs

| If you use... | You need this endpoint | Type | Why |
|---------------|----------------------|------|-----|
| Redshift COPY/UNLOAD | S3 | Gateway | Loads data from S3 without NAT GW fees |
| Glue ETL jobs | S3 | Gateway | Reads/writes data lake |
| Glue ETL jobs | Glue service | Interface | API calls to Glue service |
| EMR | S3 | Gateway | HDFS replacement, data I/O |
| Airflow (MWAA) | SQS, CloudWatch, KMS | Interface | Internal service communication |
| Secrets Manager access | Secrets Manager | Interface | Retrieve DB credentials |
| CloudWatch logging | CloudWatch Logs | Interface | Ship logs without NAT GW |
| KMS encryption | KMS | Interface | Encrypt/decrypt at rest |

---

## VPN vs Direct Connect Quick Decision

```
Need connectivity today?
├── YES → VPN (sets up in minutes)
└── NO → How much data?
    ├── < 500 GB/day → VPN is probably fine
    └── > 500 GB/day → Direct Connect
        └── Need encryption? → Add VPN over Direct Connect
```

---

## Key Formulas

### Peering Connections for Full Mesh

```
connections = n * (n - 1) / 2

VPCs    Peering Connections
  2          1
  3          3
  5         10
 10         45
 20        190
```

### NAT Gateway Cost

```
monthly_cost = (hours * $0.045) + (gb_processed * $0.045)
             = (730 * $0.045) + (gb_processed * $0.045)
             = $32.85/month base + $0.045/GB data
```

### Interface Endpoint Cost

```
monthly_cost = (hours_per_az * num_azs * $0.01) + (gb_processed * $0.01)

Example (2 AZs, 100 GB/month):
= (730 * 2 * $0.01) + (100 * $0.01)
= $14.60 + $1.00
= $15.60/month
```
