#!/usr/bin/env python3
"""Daily report: unsubscribed Supabase users emailed to a single client address."""

import logging
import sys

from report_service.config import settings
from report_service.email_sender import deliver_report
from report_service.report_builder import build_csv_bytes, build_html_body
from report_service.users import fetch_unsubscribed_users

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
        users = fetch_unsubscribed_users()
        logger.info("Fetched %s unsubscribed users", len(users))
    except Exception as exc:
        logger.exception("Failed to fetch users from Supabase: %s", exc)
        return 1

    html_body = build_html_body(users)
    csv_bytes = build_csv_bytes(users)

    try:
        deliver_report(html_body, csv_bytes, len(users))
    except Exception as exc:
        logger.exception("Failed to deliver report: %s", exc)
        return 1

    if settings.REPORT_DRY_RUN:
        logger.info("Dry run complete: %s users (no email sent)", len(users))
    else:
        logger.info(
            "Report sent: %s users to %s",
            len(users),
            settings.REPORT_TO_EMAIL,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
