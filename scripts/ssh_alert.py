#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import smtplib
from collections import Counter
from email.message import EmailMessage
from pathlib import Path

DEFAULT_LOG_FILE = "/var/log/secure"
DEFAULT_SMTP_HOST = "smtp.gmail.com"
DEFAULT_SMTP_PORT = 465
DEFAULT_THRESHOLD = 3

FAILED_LOGIN_PATTERNS = (
    re.compile(r"Failed password for (?:invalid user )?.* from (?P<source>\S+)", re.IGNORECASE),
    re.compile(r"authentication failure;.*rhost=(?P<source>\S+)", re.IGNORECASE),
)


def get_env_value(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.environ.get(name, default)
    if value == "":
        value = default

    if required and not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    if value is None:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def get_env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise SystemExit(f"Environment variable {name} must be an integer") from exc


def parse_failures(log_path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()

    with log_path.open("r", encoding="utf-8", errors="replace") as log_file:
        for line in log_file:
            for pattern in FAILED_LOGIN_PATTERNS:
                match = pattern.search(line)
                if match:
                    counts[match.group("source")] += 1
                    break

    return counts


def build_alert_body(offenders: Counter[str], threshold: int, log_path: Path) -> str:
    lines = [
        f"SSH brute-force alert generated from {log_path}",
        "",
        f"Alert threshold: more than {threshold} failed attempts",
        f"Detected sources: {len(offenders)}",
        "",
    ]

    for source, count in offenders.most_common():
        lines.append(f"{source}: {count} failed attempts")

    lines.append("")
    lines.append("This alert was generated automatically by telemonitor.")
    return "\n".join(lines)


def send_alert(*, smtp_host: str, smtp_port: int, smtp_user: str, smtp_pass: str, alert_to: str, subject: str, body: str) -> None:
    message = EmailMessage()
    message["From"] = smtp_user
    message["To"] = alert_to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(message)


def main() -> int:
    log_file = Path(get_env_value("LOG_FILE", DEFAULT_LOG_FILE))
    if not log_file.exists():
        raise SystemExit(f"Log file does not exist: {log_file}")

    threshold = get_env_int("THRESHOLD", DEFAULT_THRESHOLD)
    smtp_host = get_env_value("SMTP_HOST", DEFAULT_SMTP_HOST)
    smtp_port = get_env_int("SMTP_PORT", DEFAULT_SMTP_PORT)
    smtp_user = get_env_value("SMTP_USER", os.environ.get("SMTP_FROM"))
    smtp_pass = get_env_value("SMTP_PASS", required=True)
    alert_to = get_env_value("ALERT_TO", smtp_user)

    failures = parse_failures(log_file)
    offenders = Counter({source: count for source, count in failures.items() if count > threshold})

    if not offenders:
        print(f"No SSH brute-force sources exceeded the threshold of {threshold}.")
        return 0

    body = build_alert_body(offenders, threshold, log_file)
    subject = "SSH Alert: Failed Login Threshold Exceeded"
    send_alert(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_user=smtp_user,
        smtp_pass=smtp_pass,
        alert_to=alert_to,
        subject=subject,
        body=body,
    )

    print(f"Alert sent for {len(offenders)} SSH source(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())