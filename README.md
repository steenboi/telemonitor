# telemonitor
Automated Infrastructure Monitoring and Security Alerting Server

## Project Overview
This project transforms legacy consumer hardware (my old ASUS laptop from 2015) into a headless, prod-ready enterprise Linux server. It features a containerized telemetry stack deployed using IaC, centralized log aggregation, and custom Python automation for security auditing. The repository is intentionally structured as a portfolio artifact for sysadmin, datacenter, and NOC roles.

All systems were administered remotely via secure shell (SSH), utilizing strict host-based firewalls and static network configs to create or mimic a small scale Data Center/NOC environment and ensure stack stability.

## High-Level Architecture (HLD)

* **Base Infrastructure:** AlmaLinux 9 deployed as a headless target server (`multi-user.target`), managed entirely remotely from a Fedora 44 workstation.
* **Web & Network Security:** Nginx deployed via CLI as the primary web server. `firewalld` strictly configured to permit only required inbound traffic (SSH, HTTP/HTTPS, and specific monitoring ports).
* **Telemetry Stack (NOC Operations):** Node Exporter runs bare-metal on the target server to expose system metrics. A centralized Collector Stack (Prometheus, Grafana, Loki) is orchestrated via Podman Compose on the admin workstation. A continuous ping monitor logs network uptime.
* **Log Aggregation:** `rsyslog` captures authentication events to `/var/log/secure`. Promtail ships these logs over the network to the containerized Loki instance, creating a single-pane-of-glass dashboard in Grafana.
* **Security Automation:** A custom Python script routinely parses local authentication logs to detect SSH brute-force attempts, grouping failures by IP address. Exceeding a 3-failure threshold triggers an automated SMTP email alert. 
* **Scheduling & Maintenance:** Security auditing, continuous NOC-style uptime logging, and automated DNF package updates are scheduled and managed via `cron`. Storage is managed via `logrotate` to prevent disk exhaustion.

## Tech Stack

**Operating Systems & Networking**
* AlmaLinux 9 (Target Server) | Fedora 44 (Admin Workstation)
* `firewalld`, `nmcli` (Static IP Enforcement), SSH

**Containerization & Orchestration**
* Podman & Podman Compose (Rootless container architecture)

**Monitoring & Telemetry**
* Prometheus (Metrics scraping)
* Grafana (Data visualization & dashboarding)
* Loki & Promtail (Centralized log shipping and aggregation)
* Node Exporter (Hardware and OS metrics)

**Automation & Scripting**
* Python 3 (Security log parsing, SMTP alerting)
* Bash / systemd (Service management, `cron` scheduling, `logrotate`)

## Repo Contents

* `compose.yml`: The Podman Compose architecture defining the isolated container network, storage volumes, and deployment parameters for Prometheus, Grafana, and Loki.
* `scripts/ssh_alert.py`: The custom Python security automation script for SSH brute-force detection and email alerting.
* `.env.example`: Example credential file for SMTP settings used by the alert script.
* `prometheus/prometheus.yml`: Configuration file with scrape intervals, targets, and metric relabeling rules for label management.
* `promtail/promtail-config.yml`: Promtail configuration for shipping `/var/log/secure` into Loki.
* `systemd/promtail.service`: Systemd unit for the bare-metal Promtail agent.
* `systemd/node_exporter.service`: Systemd unit for the bare-metal Node Exporter agent.
* `cron/ssh_alert`: Cron template for the SSH alert job and nightly DNF updates.
* `logrotate/ssh_alert`: Logrotate policy for the alerting log output.
* `loki/loki-config.yml`: Schema and storage configurations for the log aggregator.

## Deployment Highlights

* **Infrastructure as Code:** Migrated the telemetry stack from bare-metal `systemd` services to an easily reproducible, isolated Podman container deployment.
* **Credential Security:** Environment variables and secured external configuration files (`chmod 600`) were utilized to ensure SMTP app passwords were never hardcoded into the automation scripts.
* **SELinux Compliance:** Container volumes were mapped using Red Hat's `:Z` flag to handle SELinux relabeling natively, ensuring rootless containers could read host configurations without triggering security denials.

## Quick Start Guide

### Prerequisites
Ensure the following are installed and configured:
* **Podman & Podman Compose** - Container runtime and orchestration
* **Node Exporter** - Running on target server at `<target_server_ip>:9100` (bare-metal or containerized)
* **Network Access** - Target server must be reachable from admin workstation

### Configuration Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/steenboi/telemonitor.git
   cd telemonitor
   ```

2. **Update Prometheus targets:**
   Edit `prometheus/prometheus.yml` and replace placeholders with your infrastructure details:
   ```yaml
   - job_name: "prod-server"
     static_configs:
       - targets: ["192.168.1.100:9100"]
   ```

3. **Configure credentials (optional):**
  If using the SSH alert automation, copy the example file and fill in SMTP credentials:
   ```bash
     cp .env.example .env
     sudo install -m 600 .env /etc/ssh_alert.env
     # edit .env with your SMTP values, then install it on the host as /etc/ssh_alert.env
   ```
   
4. **Start the telemetry stack:**
   ```bash
   podman-compose up -d
   ```

### Verification

* **Prometheus UI** - http://localhost:9090
  - Verify target health at Status → Targets
  - Confirm metrics ingestion from Node Exporter

* **Grafana Dashboard** - http://localhost:3000
  - Default credentials: `admin` / `admin`
  - Add Prometheus data source: `http://prometheus:9090`
  - Add Loki data source: `http://loki:3100`

* **Loki Log Aggregation** - Verify logs are shipping via Promtail on target server
  - Query example in Grafana: `{job="auth"}`

### Common Operations

* **View logs:**
  ```bash
  podman-compose logs -f prometheus
  ```

* **Stop the stack:**
  ```bash
  podman-compose down
  ```

* **Persistent restart:**
  ```bash
  podman-compose up -d
  ```

### Troubleshooting

* **Prometheus can't scrape targets:**
  - Verify Node Exporter is running on target server: `curl http://<target_ip>:9100/metrics`
  - Check firewall rules on target server allow inbound on port 9100
  - Confirm network connectivity: `ping <target_server_ip>`

* **Grafana can't connect to Prometheus:**
  - Verify container network isolation - containers must resolve by service name (e.g., `prometheus`)
  - Check Grafana data source configuration points to `http://prometheus:9090`

* **Loki rejecting logs:**
  - Check log timestamp is within 168h (schema config `reject_old_samples_max_age`)
  - Verify Promtail is shipping logs with correct labels
