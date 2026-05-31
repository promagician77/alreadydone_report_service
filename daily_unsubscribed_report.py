#!/usr/bin/env python3
"""Daily report: user segments emailed to a single client address."""

import logging
import sys

from report_service.config import settings
from report_service.email_sender import deliver_report
from report_service.report_builder import build_html_body, build_segment_attachments
from report_service.users import fetch_user_segments

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    try:
        settings.validate_for_run()
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    try:
        segments = fetch_user_segments()
        logger.info(
            "Segmented users: paid=%s trial=%s unsubscribed=%s never_subscribed=%s total=%s",
            len(segments.paid),
            len(segments.trial),
            len(segments.unsubscribed),
            len(segments.never_subscribed),
            segments.total,
        )
    except Exception as exc:
        logger.exception("Failed to fetch users from Supabase: %s", exc)
        return 1

    html_body = build_html_body(segments)
    attachments = build_segment_attachments(segments)

    try:
        deliver_report(html_body, attachments, segments)
    except Exception as exc:
        logger.exception("Failed to deliver report: %s", exc)
        return 1

    if settings.REPORT_DRY_RUN:
        logger.info("Dry run complete: %s users (no email sent)", segments.total)
    else:
        logger.info(
            "Report sent: paid=%s trial=%s inactive=%s never=%s to %s",
            len(segments.paid),
            len(segments.trial),
            len(segments.unsubscribed),
            len(segments.never_subscribed),
            settings.REPORT_TO_EMAIL,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
