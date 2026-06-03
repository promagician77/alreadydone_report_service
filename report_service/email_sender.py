"""Send daily report email via SendGrid."""

import base64
import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Disposition,
    Email,
    FileContent,
    FileName,
    FileType,
    Mail,
    Personalization,
)

from report_service.config import settings
from report_service.report_builder import build_plain_body, build_subject
from report_service.users import UserSegments

logger = logging.getLogger(__name__)


def preview_report(
    subject: str,
    html_body: str,
    attachments: list[tuple[str, bytes]],
    segments: UserSegments,
) -> None:
    print(f"[dry-run] subject: {subject}")
    print(f"[dry-run] to: {settings.REPORT_TO_EMAIL}")
    print(f"[dry-run] from: {settings.REPORT_FROM_EMAIL}")
    print(f"[dry-run] paid: {len(segments.paid)}")
    print(f"[dry-run] trial: {len(segments.trial)}")
    print(f"[dry-run] unsubscribed (inactive): {len(segments.unsubscribed)}")
    print(f"[dry-run] never_subscribed: {len(segments.never_subscribed)}")
    print(f"[dry-run] attachments:")
    for filename, content in attachments:
        print(f"  - {filename} ({len(content)} bytes)")
        preview_lines = content.decode("utf-8").splitlines()[:4]
        for line in preview_lines:
            print(f"      {line}")
    print("[dry-run] html preview:")
    print(html_body)


def send_report(
    subject: str,
    html_body: str,
    attachments: list[tuple[str, bytes]],
    segments: UserSegments,
) -> None:
    to_emails = [e.strip() for e in settings.REPORT_TO_EMAIL.split(",") if e.strip()]
    personalization = Personalization()
    for addr in to_emails:
        personalization.add_to(Email(addr))
    message = Mail(
        from_email=settings.REPORT_FROM_EMAIL,
        subject=subject,
        html_content=html_body,
        plain_text_content=build_plain_body(segments),
    )
    message.add_personalization(personalization)

    for filename, csv_bytes in attachments:
        encoded_csv = base64.b64encode(csv_bytes).decode("utf-8")
        attachment = Attachment(
            FileContent(encoded_csv),
            FileName(filename),
            FileType("text/csv"),
            Disposition("attachment"),
        )
        message.add_attachment(attachment)

    client = SendGridAPIClient(settings.SENDGRID_API_KEY)
    response = client.send(message)
    logger.info(
        "SendGrid response status=%s to=%s attachments=%s",
        response.status_code,
        to_emails,
        len(attachments),
    )
    if response.status_code >= 400:
        raise RuntimeError(f"SendGrid send failed with status {response.status_code}")


def deliver_report(
    html_body: str,
    attachments: list[tuple[str, bytes]],
    segments: UserSegments,
) -> None:
    subject = build_subject(segments)
    if settings.REPORT_DRY_RUN:
        preview_report(subject, html_body, attachments, segments)
        return
    send_report(subject, html_body, attachments, segments)
