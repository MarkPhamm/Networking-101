# Module 12: Cheatsheet -- Security Groups and NACLs

---

## Security Group vs NACL Comparison

| Feature | Security Group | NACL |
|---------|---------------|------|
| Operates at | Resource (ENI) level | Subnet level |
| State | **Stateful** (return traffic automatic) | **Stateless** (must allow return traffic explicitly) |
| Rule types | Allow only | Allow and Deny |
| Rule evaluation | All rules checked (any match = allow) | Rules processed in order by number (first match wins) |
| Default behavior | Deny all inbound, allow all outbound | Default NACL: allow all. Custom NACL: deny all. |
| Scope | Per instance/resource | All resources in the subnet |
| Rule limit | 60 inbound + 60 outbound (default) | 20 inbound + 20 outbound (default) |
| Source/dest | CIDR or **security group reference** | CIDR only |
| Rule numbering | No numbering (order irrelevant) | Numbered (100, 200, etc.) |
| Changes | Take effect immediately | Take effect immediately |
| Association | 1 or more SGs per ENI | 1 NACL per subnet |

---

## Security Group Rules for Data Services

### Amazon Redshift (port 5439)

| Direction | Protocol | Port | Source/Dest | Purpose |
|-----------|----------|------|-------------|---------|
| Inbound | TCP | 5439 | sg-airflow | ETL orchestration queries |
| Inbound | TCP | 5439 | sg-glue | Glue job data loading |
| Inbound | TCP | 5439 | sg-bi-tools | BI tool access (Looker, Tableau, Superset) |
| Inbound | TCP | 5439 | sg-bastion | DBA access via bastion host |

### Amazon RDS PostgreSQL (port 5432)

| Direction | Protocol | Port | Source/Dest | Purpose |
|-----------|----------|------|-------------|---------|
| Inbound | TCP | 5432 | sg-application | Application backend queries |
| Inbound | TCP | 5432 | sg-airflow | Airflow metadata database |
| Inbound | TCP | 5432 | sg-glue | Glue catalog/metadata |
| Inbound | TCP | 5432 | sg-bastion | DBA access via bastion host |

### Amazon RDS MySQL (port 3306)

| Direction | Protocol | Port | Source/Dest | Purpose |
|-----------|----------|------|-------------|---------|
| Inbound | TCP | 3306 | sg-application | Application backend |
| Inbound | TCP | 3306 | sg-airflow | Airflow metadata database |
| Inbound | TCP | 3306 | sg-bastion | DBA access via bastion host |

### Amazon EMR

| Direction | Protocol | Port | Source/Dest | Purpose |
|-----------|----------|------|-------------|---------|
| Inbound | TCP | 8088 | sg-bastion | YARN ResourceManager UI |
| Inbound | TCP | 18080 | sg-bastion | Spark History Server |
| Inbound | TCP | 8888 | sg-bastion | Jupyter/Zeppelin notebooks |
| Inbound | ALL | 0-65535 | sg-emr-core | Core/task node communication |
| Inbound | ALL | 0-65535 | sg-emr-master | Master node communication |

### Amazon MSK / Kafka

| Direction | Protocol | Port | Source/Dest | Purpose |
|-----------|----------|------|-------------|---------|
| Inbound | TCP | 9092 | sg-producers | Plaintext producer access |
| Inbound | TCP | 9094 | sg-producers | TLS producer access |
| Inbound | TCP | 9092 | sg-consumers | Plaintext consumer access |
| Inbound | TCP | 9094 | sg-consumers | TLS consumer access |
| Inbound | TCP | 2181 | sg-admin | ZooKeeper admin access |

### Airflow (MWAA or self-hosted)

| Direction | Protocol | Port | Source/Dest | Purpose |
|-----------|----------|------|-------------|---------|
| Inbound | TCP | 8080 | sg-alb | Web UI via load balancer |
| Inbound | TCP | 8080 | office-cidr | Direct access from office |
| Outbound | TCP | 5432 | sg-rds | Metadata database |
| Outbound | TCP | 5439 | sg-redshift | Query Redshift |
| Outbound | TCP | 443 | 0.0.0.0/0 | HTTPS to AWS APIs |

### Bastion Host

| Direction | Protocol | Port | Source/Dest | Purpose |
|-----------|----------|------|-------------|---------|
| Inbound | TCP | 22 | office-cidr | SSH from known IPs only |
| Outbound | TCP | 22 | 10.0.0.0/16 | SSH to VPC resources |
| Outbound | TCP | 5432 | sg-rds | Database admin |
| Outbound | TCP | 5439 | sg-redshift | Redshift admin |

---

## NACL Best Practices

### Standard Public Subnet NACL

| Rule # | Direction | Action | Proto | Port | Source/Dest | Purpose |
|--------|-----------|--------|-------|------|-------------|---------|
| 100 | Inbound | ALLOW | TCP | 443 | 0.0.0.0/0 | HTTPS |
| 110 | Inbound | ALLOW | TCP | 80 | 0.0.0.0/0 | HTTP |
| 120 | Inbound | ALLOW | TCP | 22 | office-cidr | SSH from office |
| 130 | Inbound | ALLOW | TCP | 1024-65535 | 0.0.0.0/0 | Ephemeral (return traffic) |
| * | Inbound | DENY | ALL | ALL | 0.0.0.0/0 | Default deny |
| 100 | Outbound | ALLOW | TCP | 443 | 0.0.0.0/0 | HTTPS |
| 110 | Outbound | ALLOW | TCP | 80 | 0.0.0.0/0 | HTTP |
| 120 | Outbound | ALLOW | TCP | 1024-65535 | 0.0.0.0/0 | Ephemeral (return traffic) |
| 130 | Outbound | ALLOW | ALL | ALL | 10.0.0.0/16 | All traffic to VPC |
| * | Outbound | DENY | ALL | ALL | 0.0.0.0/0 | Default deny |

### Standard Private Subnet NACL

| Rule # | Direction | Action | Proto | Port | Source/Dest | Purpose |
|--------|-----------|--------|-------|------|-------------|---------|
| 100 | Inbound | ALLOW | TCP | 5432 | 10.0.0.0/16 | PostgreSQL from VPC |
| 110 | Inbound | ALLOW | TCP | 5439 | 10.0.0.0/16 | Redshift from VPC |
| 120 | Inbound | ALLOW | TCP | 3306 | 10.0.0.0/16 | MySQL from VPC |
| 130 | Inbound | ALLOW | TCP | 1024-65535 | 0.0.0.0/0 | Ephemeral (return traffic) |
| * | Inbound | DENY | ALL | ALL | 0.0.0.0/0 | Default deny |
| 100 | Outbound | ALLOW | TCP | 443 | 0.0.0.0/0 | HTTPS outbound |
| 110 | Outbound | ALLOW | TCP | 1024-65535 | 0.0.0.0/0 | Ephemeral (return traffic) |
| * | Outbound | DENY | ALL | ALL | 0.0.0.0/0 | Default deny |

### NACL Rule Numbering Convention

| Range | Purpose |
|-------|---------|
| 100-199 | Primary allow rules |
| 200-299 | Specific deny rules (block known bad IPs) |
| 300-399 | Secondary allow rules |
| 900-999 | Catch-all rules before default deny |

Leave gaps between rule numbers (100, 110, 120) so you can insert new rules without renumbering.

---

## Stateful vs Stateless: Quick Reference

### Security Group (Stateful)

```
You configure:           What happens automatically:
  Inbound: Allow 5432  -->  Outbound reply on ephemeral port: AUTO-ALLOWED
  Outbound: Allow 443  -->  Inbound reply from server: AUTO-ALLOWED
```

One rule covers the full connection.

### NACL (Stateless)

```
You must configure BOTH:
  Inbound:  Allow TCP 5432 from 10.0.1.0/24      (the request)
  Outbound: Allow TCP 1024-65535 to 10.0.1.0/24   (the response)
```

Forgetting the outbound ephemeral rule is the most common NACL mistake.

### Ephemeral Port Ranges

| OS | Ephemeral Range |
|----|----------------|
| Linux | 32768-60999 |
| Windows | 49152-65535 |
| AWS recommendation | Allow 1024-65535 (covers all) |

---

## Debugging Checklist

When a connection fails, check these in order:

```
1. SECURITY GROUP (resource level)
   [ ] Inbound rule allows the protocol + port from the source?
   [ ] If using SG reference, does the source have that SG attached?
   [ ] Outbound rule allows traffic to the destination? (default: all allowed)

2. NACL (subnet level)
   [ ] Inbound rule allows the protocol + port from the source CIDR?
   [ ] Outbound rule allows ephemeral ports (1024-65535) to the source?
   [ ] Rules are in the right ORDER? (lower number = higher priority)
   [ ] No DENY rule with a lower number blocking the traffic?

3. ROUTE TABLE
   [ ] Source subnet has a route to the destination network?
   [ ] Destination subnet has a route back to the source?
   [ ] If crossing VPCs: peering route exists?

4. SUBNET / VPC
   [ ] Both resources in the same VPC? Or connected via peering/TGW?
   [ ] Private subnet has NAT GW route for internet-bound traffic?
   [ ] Public subnet has IGW route?

5. RESOURCE
   [ ] Instance/service is running?
   [ ] Correct port is listening?
   [ ] Elastic IP or public IP assigned (if needed)?
   [ ] DNS name resolves to correct IP?
```

### Common Error Messages

| Error | Likely Cause |
|-------|-------------|
| Connection timed out | SG or NACL blocking, or no route to host |
| Connection refused | Port not listening, service not running, or host firewall |
| No route to host | Missing route in route table |
| Network unreachable | No route, or IGW/NAT GW not configured |
| Host unreachable | Instance down, or wrong IP/subnet |

---

## Security Group Tips

1. **Use SG references over CIDRs** -- dynamic IPs from auto-scaling, EMR, Lambda all handled automatically.
2. **Name your SGs clearly** -- `sg-prod-redshift`, `sg-prod-airflow`, not `sg-12345`.
3. **One SG per role** -- separate SGs for bastion, database, application, ETL.
4. **Avoid 0.0.0.0/0 inbound** -- except for public-facing ALBs on 443/80.
5. **Review SGs regularly** -- remove stale rules from decommissioned services.

## NACL Tips

1. **Keep NACLs simple** -- use them for broad subnet-level guardrails, not fine-grained control.
2. **Always allow ephemeral ports** -- both inbound and outbound (1024-65535).
3. **Leave gaps in rule numbers** -- 100, 110, 120 lets you insert 105 later.
4. **Do not rely on NACLs alone** -- they are a backup layer. SGs are your primary control.
5. **The default NACL allows everything** -- custom NACLs deny everything. Know which you are using.
