"""Build HTML summary and CSV attachments for the daily marketing report."""

import csv
import html
import io
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from report_service.users import SegmentName, UserSegments

# Pacific Time (PST/PDT) — matches systemd timer schedule
REPORT_TIMEZONE = ZoneInfo("America/Los_Angeles")

REPORT_COLUMNS = [
    ("id", "ID"),
    ("email", "Email"),
    ("name", "Name"),
    ("rc_subscription_status", "RC Status"),
    ("rc_subscription_plan", "RC Plan"),
    ("created_at", "Created At"),
    ("subscription_provider", "Provider"),
]

SEGMENT_LABELS: dict[SegmentName, str] = {
    "paid": "Paid subscribers",
    "trial": "Trial users",
    "unsubscribed": "Unsubscribed (inactive)",
    "never_subscribed": "Never trial or subscription",
}

SEGMENT_DESCRIPTIONS: dict[SegmentName, str] = {
    "paid": "rc_subscription_status is active.",
    "trial": "rc_subscription_status is trial.",
    "unsubscribed": "rc_subscription_status is inactive.",
    "never_subscribed": (
        "rc_subscription_status is empty or any value other than active, trial, or inactive."
    ),
}

SEGMENT_ORDER: tuple[SegmentName, ...] = (
    "paid",
    "trial",
    "unsubscribed",
    "never_subscribed",
)


def report_date_label(when: datetime | None = None) -> str:
    if when is None:
        dt = datetime.now(timezone.utc).astimezone(REPORT_TIMEZONE)
    elif when.tzinfo is None:
        dt = when.replace(tzinfo=timezone.utc).astimezone(REPORT_TIMEZONE)
    else:
        dt = when.astimezone(REPORT_TIMEZONE)
    return dt.strftime("%Y-%m-%d")


def build_subject(segments: UserSegments, when: datetime | None = None) -> str:
    date_label = report_date_label(when)
    return (
        f"Already Done — User segments ({date_label}) — "
        f"{segments.total} total "
        f"(paid {len(segments.paid)}, trial {len(segments.trial)}, "
        f"inactive {len(segments.unsubscribed)}, never {len(segments.never_subscribed)})"
    )


def _cell_value(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if value is None:
        return ""
    return str(value).strip()


def build_csv_bytes(users: list[dict[str, Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([label for _, label in REPORT_COLUMNS])
    for row in users:
        writer.writerow([_cell_value(row, key) for key, _ in REPORT_COLUMNS])
    return buffer.getvalue().encode("utf-8")


def csv_filename(segment: SegmentName, when: datetime | None = None) -> str:
    date_label = report_date_label(when)
    return f"{segment}_{date_label}.csv"


def build_segment_attachments(
    segments: UserSegments, when: datetime | None = None
) -> list[tuple[str, bytes]]:
    return [
        (csv_filename(segment, when), build_csv_bytes(getattr(segments, segment)))
        for segment in SEGMENT_ORDER
    ]


def _render_table(users: list[dict[str, Any]], max_rows: int = 25) -> str:
    if not users:
        return "<p><em>None</em></p>"

    header_cells = "".join(
        f"<th>{html.escape(label)}</th>" for _, label in REPORT_COLUMNS
    )
    body_rows = []
    for row in users[:max_rows]:
        cells = "".join(
            f"<td>{html.escape(_cell_value(row, key))}</td>" for key, _ in REPORT_COLUMNS
        )
        body_rows.append(f"<tr>{cells}</tr>")

    rows_html = "\n".join(body_rows)
    more = ""
    if len(users) > max_rows:
        more = f"<p><em>Showing first {max_rows} of {len(users)}. See CSV attachment for full list.</em></p>"

    return f"""\
{more}
<table border="1" cellpadding="6" cellspacing="0">
  <thead><tr>{header_cells}</tr></thead>
  <tbody>
{rows_html}
  </tbody>
</table>
"""


def build_html_body(segments: UserSegments, when: datetime | None = None) -> str:
    date_label = report_date_label(when)
    sections = []

    for segment in SEGMENT_ORDER:
        users = getattr(segments, segment)
        label = SEGMENT_LABELS[segment]
        description = SEGMENT_DESCRIPTIONS[segment]
        sections.append(
            f"<h2>{html.escape(label)} ({len(users)})</h2>"
            f"<p>{html.escape(description)}</p>"
            f"{_render_table(users)}"
        )

    sections_html = "\n".join(sections)
    return f"""\
<p>Daily user segment report for <strong>{html.escape(date_label)}</strong>.</p>
<p>
  <strong>{segments.total}</strong> users with email across 4 marketing segments.
  Four CSV files are attached (one per segment).
</p>
{sections_html}
"""
