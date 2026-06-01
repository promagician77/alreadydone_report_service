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


_TH_STYLE = (
    "border: 1px solid #ccc; padding: 7px 10px; text-align: left; "
    "background: #f5f5f5; white-space: nowrap;"
)
_TD_STYLE = "border: 1px solid #ccc; padding: 6px 10px; white-space: nowrap;"
_TR_EVEN_STYLE = "background: #fafafa;"


def _render_table(users: list[dict[str, Any]], max_rows: int = 25) -> str:
    if not users:
        return '<p style="color: #888;"><em>None</em></p>'

    header_cells = "".join(
        f'<th style="{_TH_STYLE}">{html.escape(label)}</th>'
        for _, label in REPORT_COLUMNS
    )
    body_rows = []
    for i, row in enumerate(users[:max_rows]):
        row_style = f' style="{_TR_EVEN_STYLE}"' if i % 2 == 1 else ""
        cells = "".join(
            f'<td style="{_TD_STYLE}">{html.escape(_cell_value(row, key))}</td>'
            for key, _ in REPORT_COLUMNS
        )
        body_rows.append(f"<tr{row_style}>{cells}</tr>")

    rows_html = "\n".join(body_rows)
    truncation_note = (
        f'<p style="font-size: 12px; color: #888; margin-top: 4px;">'
        f"<em>Showing first {max_rows} of {len(users)}. See CSV attachment for full list.</em></p>"
        if len(users) > max_rows
        else ""
    )

    return (
        f'<table style="border-collapse: collapse; font-size: 13px; width: 100%;">\n'
        f"  <thead><tr>{header_cells}</tr></thead>\n"
        f"  <tbody>\n{rows_html}\n  </tbody>\n"
        f"</table>\n"
        f"{truncation_note}"
    )


_BODY_STYLE = "font-family: Arial, Helvetica, sans-serif; color: #222; font-size: 14px; margin: 0; padding: 0; background: #fff;"
_CONTAINER_STYLE = "max-width: 960px; margin: 24px auto; padding: 0 16px;"
_H1_STYLE = "font-size: 18px; color: #1a1a1a; margin-bottom: 4px;"
_META_STYLE = "font-size: 13px; color: #555; margin-top: 0; margin-bottom: 24px;"
_H2_STYLE = "font-size: 15px; color: #333; margin-top: 32px; margin-bottom: 4px; border-bottom: 2px solid #e0e0e0; padding-bottom: 4px;"
_DESC_STYLE = "font-size: 12px; color: #777; margin-top: 2px; margin-bottom: 8px;"


def build_html_body(segments: UserSegments, when: datetime | None = None) -> str:
    date_label = report_date_label(when)
    sections = []

    for segment in SEGMENT_ORDER:
        if segment == "never_subscribed":
            continue
        users = getattr(segments, segment)
        label = SEGMENT_LABELS[segment]
        description = SEGMENT_DESCRIPTIONS[segment]
        sections.append(
            f'<h2 style="{_H2_STYLE}">{html.escape(label)} ({len(users)})</h2>\n'
            f'<p style="{_DESC_STYLE}">{html.escape(description)}</p>\n'
            f"{_render_table(users)}"
        )

    sections_html = "\n".join(sections)
    counts = (
        f"<strong>{len(segments.paid)}</strong> paid &nbsp;·&nbsp; "
        f"<strong>{len(segments.trial)}</strong> trial &nbsp;·&nbsp; "
        f"<strong>{len(segments.unsubscribed)}</strong> inactive &nbsp;·&nbsp; "
        f"<strong>{len(segments.never_subscribed)}</strong> never subscribed"
    )

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"></head>
<body style="{_BODY_STYLE}">
<div style="{_CONTAINER_STYLE}">
  <h1 style="{_H1_STYLE}">Already Done &mdash; User Segments</h1>
  <p style="{_META_STYLE}">
    Report date: <strong>{html.escape(date_label)}</strong> &nbsp;&middot;&nbsp;
    <strong>{segments.total}</strong> users with email &nbsp;&middot;&nbsp;
    {counts}
  </p>
  <p style="font-size: 12px; color: #888; margin-top: -12px;">
    Four CSV attachments included (one per segment).
  </p>
{sections_html}
</div>
</body>
</html>
"""


def build_plain_body(segments: UserSegments, when: datetime | None = None) -> str:
    date_label = report_date_label(when)
    lines = [
        f"Already Done — User Segments — {date_label}",
        f"Total: {segments.total} users with email",
        "",
        f"  Paid:             {len(segments.paid)}",
        f"  Trial:            {len(segments.trial)}",
        f"  Inactive:         {len(segments.unsubscribed)}",
        f"  Never subscribed: {len(segments.never_subscribed)}",
        "",
        "Four CSV attachments are included (one per segment).",
    ]
    return "\n".join(lines)
