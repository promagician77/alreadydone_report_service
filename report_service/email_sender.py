"""Send daily report email via SendGrid."""

import base64
import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Mail,
)

from report_service.config import settings
from report_service.report_builder import build_subject, csv_filename

logger = logging.getLogger(__name__)


def preview_report(subject: str, html_body: str, csv_bytes: bytes, user_count: int) -> None:
    print(f"[dry-run] subject: {subject}")
    print(f"[dry-run] to: {settings.REPORT_TO_EMAIL}")
    print(f"[dry-run] from: {settings.REPORT_FROM_EMAIL}")
    print(f"[dry-run] user_count: {user_count}")
    print(f"[dry-run] attachment: {csv_filename()}")
    preview_lines = csv_bytes.decode("utf-8").splitlines()[:6]
    if preview_lines:
        print("[dry-run] csv preview:")
        for line in preview_lines:
            print(f"  {line}")
    else:
        print("[dry-run] csv preview: (empty)")
    print("[dry-run] html preview:")
    print(html_body)


def send_report(subject: str, html_body: str, csv_bytes: bytes) -> None:
    message = Mail(
        from_email=settings.REPORT_FROM_EMAIL,
        to_emails=settings.REPORT_TO_EMAIL,
        subject=subject,
        html_content=html_body,
    )

    encoded_csv = base64.b64encode(csv_bytes).decode("utf-8")
    attachment = Attachment(
        FileContent(encoded_csv),
        FileName(csv_filename()),
        FileType("text/csv"),
        Disposition("attachment"),
    )
    message.attachment = attachment

    client = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = client.send(message)
    logger.info(
        "SendGrid response status=%s to=%s",
        response.status_code,
        settings.REPORT_TO_EMAIL,
    )
    if response.status_code >= 400:
        raise RuntimeError(f"SendGrid send failed with status {response.status_code}")


def deliver_report(html_body: str, csv_bytes: bytes, user_count: int) -> None:
    subject = build_subject(user_count)
    if settings.REPORT_DRY_RUN:
        preview_report(subject, html_body, csv_bytes, user_count)
        return
    send_report(subject, html_body, csv_bytes)
