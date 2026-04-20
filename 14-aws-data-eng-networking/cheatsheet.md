# Module 14: Cheatsheet -- AWS Data Engineering Networking Troubleshooting

---

## "I Can't Connect To..." Quick Reference

### Redshift

| Symptom | Check | Fix |
|---------|-------|-----|
| Connection timed out from Airflow | Security Group | Add inbound TCP 5439 from airflow-sg to redshift-sg |
| COPY from S3 hangs forever | VPC Endpoint | Create S3 Gateway Endpoint, associate with Redshift subnet route table |
| COPY from S3 still hangs | Enhanced VPC Routing | Enable Enhanced VPC Routing on the Redshift cluster |
| UNLOAD writes nothing | S3 Bucket Policy | Check bucket policy allows access from the VPC endpoint |
| Can't connect from BI tool | Network path | Need bastion SSH tunnel or VPN to private subnet |
| "No route to host" | Route table | Check Redshift subnet has route to source network |
| IAM auth fails on COPY | IAM Role | Attach IAM role with S3 read to the Redshift cluster |

**Key port:** 5439

---

### RDS (PostgreSQL / MySQL)

| Symptom | Check | Fix |
|---------|-------|-----|
| Connection timed out | Security Group | Add inbound TCP 5432 (PG) or 3306 (MySQL) from source SG |
| "Could not translate hostname" | DNS | Ensure VPC DNS resolution is enabled |
| Timeout from private subnet | Publicly Accessible | Set to "No" -- when "Yes", DNS returns public IP unreachable from private subnet |
| Can't connect after failover | DNS TTL | Wait for DNS cache to expire (RDS endpoint auto-updates) |
| Connection refused | Subnet group | Ensure RDS subnet group includes subnets reachable from source |

**Key ports:** 5432 (PostgreSQL), 3306 (MySQL), 1433 (SQL Server), 1521 (Oracle)

---

### EMR

| Symptom | Check | Fix |
|---------|-------|-----|
| S3 reads are slow/expensive | VPC Endpoint | Create S3 Gateway Endpoint on EMR subnet route table |
| Can't SSH to master | Security Group | Add SSH (22) inbound from bastion-sg to EMR additional SG |
| Nodes can't communicate | Managed SGs | Do NOT delete or restrict EMR managed security group rules |
| Spark jobs fail with S3 timeout | Route table | Ensure S3 Gateway Endpoint is on EMR subnet route table |
| Can't access Spark UI | SSH tunnel | Forward port 18080 through bastion: `ssh -L 18080:master-ip:18080 bastion` |

**Key ports:** 8443 (EMR managed), 8088 (YARN), 18080 (Spark History), 8888 (Jupyter)

---

### Glue

| Symptom | Check | Fix |
|---------|-------|-----|
| JDBC connection timeout | VPC Connection | Create a Glue Connection with correct VPC, subnet, SG |
| Job fails immediately | Self-ref SG | Add self-referencing inbound/outbound on all ports in glue-sg |
| Can't reach S3 | VPC Endpoint | Create S3 Gateway Endpoint on Glue subnet route table |
| Can't resolve RDS hostname | DNS | Enable DNS resolution on VPC; enable DNS hostnames |
| "No private IP" error | Subnet IPs | Use a subnet with enough free IPs (Glue creates multiple ENIs) |
| Timeout on Glue API calls | Glue endpoint | Create Interface endpoint for Glue service |

**Key requirement:** Self-referencing SG rules (Glue workers must communicate with each other)

---

### MWAA (Managed Airflow)

| Symptom | Check | Fix |
|---------|-------|-----|
| Environment creation fails | Subnets | Need 2 private subnets in different AZs |
| Workers can't reach internet | NAT Gateway | Private subnets need NAT GW route (for PyPI, etc.) |
| Can't connect to RDS | Security Group | Add outbound TCP 5432 to airflow-sg, inbound on rds-sg |
| DAGs not syncing | S3 access | Check S3 Gateway Endpoint or NAT GW path to S3 |
| Workers can't communicate | Self-ref SG | Add self-referencing inbound rule on MWAA SG |
| Web UI not accessible | Access mode | Use "Public" web server access mode, or set up VPN |

**Key requirement:** 2 private subnets in different AZs, self-referencing SG

---

### S3

| Symptom | Check | Fix |
|---------|-------|-----|
| Timeout from private subnet | VPC Endpoint | Create S3 Gateway Endpoint |
| Slow access, high NAT costs | NAT Gateway | S3 Gateway Endpoint eliminates NAT GW fees |
| "Access Denied" with endpoint | Endpoint policy | Check VPC endpoint policy allows the bucket |
| "Access Denied" from Glue | Bucket policy | Check bucket policy allows principal / VPC endpoint |
| Cross-region S3 access needed | Interface endpoint | Use S3 Interface Endpoint for cross-region |

**Key cost:** NAT Gateway charges $0.045/GB for S3 traffic. Gateway Endpoint is FREE.

---

## Common Port Numbers for Data Services

| Service | Default Port | Protocol | Notes |
|---------|-------------|----------|-------|
| PostgreSQL (RDS) | 5432 | TCP | Most common DE database |
| MySQL (RDS) | 3306 | TCP | |
| Redshift | 5439 | TCP | Modified PostgreSQL wire protocol |
| SQL Server (RDS) | 1433 | TCP | |
| Oracle (RDS) | 1521 | TCP | |
| SSH | 22 | TCP | Bastion access, EMR |
| HTTPS | 443 | TCP | AWS API calls, S3, all endpoints |
| Kafka (MSK) | 9092 / 9094 | TCP | Plaintext / TLS |
| Elasticsearch/OpenSearch | 443 / 9200 | TCP | AWS uses 443 |
| YARN ResourceManager | 8088 | TCP | EMR |
| Spark History Server | 18080 | TCP | EMR |
| Spark Driver | 4040 | TCP | Active Spark app |
| Jupyter | 8888 | TCP | EMR notebooks |
| Airflow Web UI | 8080 | TCP | Self-hosted Airflow |
| MWAA Web UI | 443 | TCP | Managed Airflow |

---

## Security Group Rule Templates

### Redshift Cluster

```
Inbound:
  TCP 5439  from  airflow-sg          (Airflow connections)
  TCP 5439  from  glue-sg             (Glue JDBC, if needed)
  TCP 5439  from  bastion-sg          (Admin access via tunnel)

Outbound:
  TCP 443   to    pl-xxxxxxxx (S3)    (COPY/UNLOAD via endpoint)
```

### RDS PostgreSQL

```
Inbound:
  TCP 5432  from  airflow-sg          (Pipeline queries)
  TCP 5432  from  glue-sg             (ETL reads)
  TCP 5432  from  bastion-sg          (Admin access via tunnel)

Outbound:
  (Default: allow all outbound)
```

### Glue

```
Inbound:
  All TCP   from  glue-sg (self)      (Worker-to-worker communication)

Outbound:
  All TCP   to    glue-sg (self)      (Worker-to-worker communication)
  TCP 5432  to    rds-sg              (JDBC to PostgreSQL)
  TCP 5439  to    redshift-sg         (JDBC to Redshift)
  TCP 443   to    pl-xxxxxxxx (S3)    (Data lake access)
```

### EMR (Additional Security Group)

```
Inbound:
  TCP 22    from  bastion-sg          (SSH to master for debugging)

(EMR managed SGs handle all inter-node communication -- do not modify them)
```

### MWAA / Airflow

```
Inbound:
  All TCP   from  airflow-sg (self)   (Worker-to-worker, if MWAA)

Outbound:
  TCP 5432  to    rds-sg              (Pipeline metadata DB)
  TCP 5439  to    redshift-sg         (Redshift queries)
  TCP 443   to    0.0.0.0/0           (AWS APIs, PyPI, etc.)
```

---

## Subnet Layout Template

### For a Data Engineering VPC (10.0.0.0/16)

| Subnet | CIDR | AZ | Type | Purpose |
|--------|------|----|------|---------|
| public-a | 10.0.1.0/24 | AZ-a | Public | Bastion, NAT GW |
| public-b | 10.0.2.0/24 | AZ-b | Public | NAT GW (HA) |
| app-a | 10.0.10.0/24 | AZ-a | Private | Airflow, Glue ENIs |
| app-b | 10.0.11.0/24 | AZ-b | Private | Airflow, Glue ENIs |
| data-a | 10.0.20.0/24 | AZ-a | Private | Redshift, RDS |
| data-b | 10.0.21.0/24 | AZ-b | Private | Redshift, RDS |
| compute-a | 10.0.30.0/24 | AZ-a | Private | EMR |
| compute-b | 10.0.31.0/24 | AZ-b | Private | EMR |

### Route Tables

| Route Table | Destination | Target | Used By |
|-------------|-------------|--------|---------|
| public-rt | 0.0.0.0/0 | igw-xxx | public subnets |
| private-rt | 0.0.0.0/0 | nat-xxx | all private subnets |
| private-rt | pl-xxx (S3) | vpce-xxx | all private subnets |

---

## VPC Endpoint Checklist for Data Engineering

| Endpoint | Type | Cost | Priority |
|----------|------|------|----------|
| S3 | Gateway | FREE | MUST HAVE (do this first) |
| DynamoDB | Gateway | FREE | If you use DynamoDB |
| Glue | Interface | ~$15/mo | If Glue jobs use VPC connections |
| CloudWatch Logs | Interface | ~$15/mo | Avoids NAT for logging |
| Secrets Manager | Interface | ~$15/mo | If storing DB creds in Secrets Manager |
| KMS | Interface | ~$15/mo | If using encryption keys |
| SQS | Interface | ~$15/mo | If MWAA or apps use SQS |
| STS | Interface | ~$15/mo | If assuming IAM roles |
| ECR | Interface | ~$15/mo | If pulling container images |

**Rule of thumb:** Start with S3 Gateway (free, biggest impact). Add Interface endpoints as needed based on NAT Gateway cost analysis.

---

## Debugging Checklist (Print This Out)

When something can't connect, check in this order:

```
[ ] 1. Security Group: correct port, protocol, source SG/CIDR?
[ ] 2. Security Group: outbound rule on source allows traffic?
[ ] 3. NACL: both inbound AND outbound allow traffic + ephemeral ports?
[ ] 4. Route Table: source subnet has route to destination?
[ ] 5. VPC Endpoint: needed for AWS service access from private subnet?
[ ] 6. DNS: hostname resolves to correct (private) IP?
[ ] 7. Service config: Publicly Accessible, Enhanced VPC Routing, etc.?
[ ] 8. IAM: role/policy allows the API call?
[ ] 9. Subnet: enough free IPs? (for Glue, MWAA, Lambda)
[ ] 10. AZ: resource and subnet in the same AZ? (for some services)
```
