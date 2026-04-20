# Networking-to-Data-Engineering Rosetta Stone

A reference mapping networking concepts to their data engineering equivalents. When you encounter a networking term you don't have intuition for, find it here and think about the DE concept you already know.

---

| Networking Concept | Data Engineering Equivalent | How the Analogy Works |
|----|----|----|
| SSH connection | JDBC/ODBC connection | Both establish an authenticated, encrypted channel to a remote service. SSH gives you a shell; JDBC gives you a query interface. Same pattern: connect, authenticate, exchange data, disconnect. |
| Public/private SSH keys | Service account credentials / IAM keys | The private key stays with you (like a service account JSON key file). The public key is registered on the server (like adding a service account to IAM roles). Proves identity without transmitting a secret. |
| DNS | Service discovery (Consul, K8s DNS) | DNS maps names to IPs. Service discovery maps service names to endpoints. `dig db.prod.internal` is conceptually identical to a K8s service resolving `postgres.default.svc.cluster.local` to a pod IP. |
| IP address | Database host endpoint | The IP address tells you *where* the machine lives on the network, just like a database hostname/endpoint (`my-db.us-east-1.rds.amazonaws.com`) tells your application where to send queries. |
| Port | Database listener port | Ports identify *which service* on a machine. Port 5432 means PostgreSQL, just like port 22 means SSH. Your connection string's port number is a transport-layer concept. |
| Routing table | Pipeline routing / workflow DAG | A routing table says "traffic for 10.0.0.0/16 goes to gateway X." A DAG says "data from source A goes to transformation B." Both are decision tables that direct traffic (packets or data) to the right destination. |
| Subnet | Data partition / shard | Subnets divide a network into smaller, manageable segments. Partitions divide a table into smaller, queryable chunks. Both use a key (IP prefix / partition key) to determine which segment something belongs to. |
| Firewall rules | GRANT/REVOKE / Security Groups | Firewalls control which traffic can enter or leave a network. `GRANT SELECT ON table TO user` controls which queries can access data. AWS Security Groups are literally firewall rules applied to cloud resources. |
| NAT (Network Address Translation) | Reverse proxy / API gateway | NAT hides internal IPs behind a single public IP. A reverse proxy (nginx, API gateway) hides internal services behind a single public endpoint. Both translate between external-facing and internal addressing. |
| VPN | VPC peering / private link | A VPN securely connects two separate networks so they can communicate. VPC peering connects two cloud VPCs. AWS PrivateLink gives private access to services without internet exposure. Same goal: private connectivity between isolated networks. |
| TCP three-way handshake | Connection pool session setup | SYN = "I want a connection." SYN-ACK = "Connection allocated." ACK = "Confirmed, sending queries." This is what happens inside SQLAlchemy's `create_engine()` pool when establishing each new database session. |
| Packet encapsulation | ETL stages adding metadata | Each TCP/IP layer wraps data in a header, like ETL stages adding audit columns, batch IDs, and lineage tags. The core payload doesn't change; it just accumulates context as it moves through the pipeline. |
| ARP cache | Local DNS cache / connection pool cache | The ARP cache stores recently resolved IP-to-MAC mappings to avoid repeated broadcasts. A connection pool caches open database connections to avoid repeated handshakes. Both are local caches that trade freshness for speed. |
| Load balancer | Distributed query engine routing | A load balancer distributes incoming connections across multiple backend servers. A distributed query engine (Spark, Presto) distributes query fragments across worker nodes. Both optimize throughput by spreading work. |
| Bastion / jump host | Jump server for prod DB access | You SSH into the bastion, then hop to the internal server. In data engineering, you SSH into a jump server in the VPC, then connect to the production RDS instance. Same pattern: controlled entry point into a private environment. |
| TTL (Time to Live) | Job timeout / query timeout | TTL prevents packets from looping forever by decrementing at each hop. Query timeouts prevent runaway queries from consuming resources forever. Both are safety limits that kill something that's taking too long. |
| Packet loss / retransmission | Failed task retry in Airflow | TCP retransmits lost segments automatically. Airflow retries failed tasks according to `retries` and `retry_delay`. Both handle transient failures by trying again, with backoff strategies to avoid overwhelming the system. |
| Port scanning (nmap) | Schema discovery / catalog crawl | `nmap` discovers what services are running on a host by probing ports. A data catalog crawl (Glue, Alation) discovers what tables and schemas exist in a database. Both are exploratory operations to map what's available. |
| MAC address | Hardware serial number / physical node ID | A MAC address is a fixed identifier burned into hardware. In data engineering, this is like a Spark executor's unique ID or a Kafka broker's `broker.id` -- an identifier tied to a specific physical (or virtual) resource. |
| CIDR notation (10.0.0.0/16) | Partition range expression | CIDR defines a range of IPs with a prefix. Partition expressions define a range of keys (`WHERE date BETWEEN '2024-01-01' AND '2024-01-31'`). Both carve a large space into a defined subset. |
| Bandwidth (Mbps/Gbps) | Pipeline throughput (rows/sec, MB/sec) | Bandwidth is the maximum rate of data transfer on a network link. Pipeline throughput is the rate at which your ETL moves data. Both can be bottlenecks, and both are measured in data-per-unit-time. |
| DNS TTL (cache expiry) | Cache invalidation / materialized view refresh | DNS records have a TTL that controls how long resolvers cache them. Materialized views and Redis caches have refresh intervals. Both balance freshness against performance -- shorter TTL means more current data but more load. |
| TCP flow control (receive window) | Backpressure in streaming systems | TCP's receive window tells the sender to slow down when the receiver is overwhelmed. Kafka consumer lag and Flink backpressure do the same thing: signal the upstream to throttle when the downstream can't keep up. |
| Network segmentation (VLANs) | Data lake zones (raw/staging/curated) | VLANs isolate network traffic into logical zones for security and organization. Data lake zones separate raw ingestion from cleaned, production-ready data. Same principle: logical boundaries on shared infrastructure. |

---

## How to Use This Table

When you encounter a networking concept and your brain goes blank, find its DE equivalent here. You already have deep intuition for how database connections, ETL pipelines, and query engines work. Networking uses different words for the same patterns.

The reverse works too: when configuring cloud infrastructure (VPCs, security groups, load balancers), recognize that you're doing networking -- and apply what you've learned in this guide.

---

[Back to main guide](../README.md)
