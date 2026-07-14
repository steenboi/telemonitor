# telemonitor
Automated Infrastructure Monitoring and Security Alerting Server

## Project Overview
This project transforms legacy consumer hardware (my old ASUS laptop from 2015) into a headless, prod-ready enterprise Linux server. It features a containerized telemetry stack deployed using IaC, centralized log aggregation, and custom Python automation for security auditing. My main machine is being used as the client to monitor this headless server.

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
* `ssh_alert.py`: The custom Python security automation script.
* `prometheus.yml`: Configuration file defining scrape intervals and targets.
* `loki-config.yml`: Schema and storage configurations for the log aggregator.

## Repo Contents

* `compose.yml`: The Podman Compose architecture defining the isolated container network, storage volumes, and deployment parameters for Prometheus, Grafana, and Loki.
* `ssh_alert.py`: The custom Python security automation script.
* `prometheus.yml`: Configuration file defining scrape intervals and targets.
* `loki-config.yml`: Schema and storage configurations for the log aggregator.

## Deployment Highlights

* **Infrastructure as Code:** Migrated the telemetry stack from bare-metal `systemd` services to an easily reproducible, isolated Podman container deployment.
* **Credential Security:** Environment variables and secured external configuration files (`chmod 600`) were utilized to ensure SMTP app passwords were never hardcoded into the automation scripts.
* **SELinux Compliance:** Container volumes were mapped using Red Hat's `:Z` flag to handle SELinux relabeling natively, ensuring rootless containers could read host configurations without triggering security denials.
