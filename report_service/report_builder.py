"""Build HTML summary and CSV attachment for the daily report."""

import csv
import html
import io
from datetime import datetime, timezone
from typing import Any

REPORT_COLUMNS = [
    ("id", "ID"),
    ("email", "Email"),
    ("name", "Name"),
    ("rc_subscription_status", "Status"),
    ("rc_subscription_plan", "Plan"),
    ("created_at", "Created At"),
    ("subscription_provider", "Provider"),
]


def report_date_label(when: datetime | None = None) -> str:
    dt = when or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d")


def build_subject(user_count: int, when: datetime | None = None) -> str:
    date_label = report_date_label(when)
    return f"Already Done — Unsubscribed users ({date_label}) — {user_count} total"


def _cell_value(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None:
        return ""
    return str(value).strip()


def build_csv_bytes(users: list[dict[str, Any]], when: datetime | None = None) -> bytes:
    date_label = report_date_label(when)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([label for _, label in REPORT_COLUMNS])
    for row in users:
        writer.writerow([_cell_value(row, key) for key, _ in REPORT_COLUMNS])
    return buffer.getvalue().encode("utf-8")


def csv_filename(when: datetime | None = None) -> str:
    return f"unsubscribed_users_{report_date_label(when)}.csv"


def build_html_body(users: list[dict[str, Any]], when: datetime | None = None) -> str:
    date_label = report_date_label(when)
    count = len(users)

    if count == 0:
        return (
            f"<p>Daily unsubscribed users report for <strong>{html.escape(date_label)}</strong>.</p>"
            f"<p><strong>0</strong> unsubscribed users found.</p>"
        )

    header_cells = "".join(
        f"<th>{html.escape(label)}</th>" for _, label in REPORT_COLUMNS
    )
    body_rows = []
    for row in users:
        cells = "".join(
            f"<td>{html.escape(_cell_value(row, key))}</td>" for key, _ in REPORT_COLUMNS
        )
        body_rows.append(f"<tr>{cells}</tr>")

    rows_html = "\n".join(body_rows)
    return f"""\
<p>Daily unsubscribed users report for <strong>{html.escape(date_label)}</strong>.</p>
<p><strong>{count}</strong> unsubscribed users found. CSV attached.</p>
<table border="1" cellpadding="6" cellspacing="0">
  <thead><tr>{header_cells}</tr></thead>
  <tbody>
{rows_html}
  </tbody>
</table>
"""
