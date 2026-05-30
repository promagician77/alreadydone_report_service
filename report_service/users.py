"""Fetch and filter unsubscribed users from Supabase."""

from typing import Any

from report_service.supabase_client import get_supabase

ACTIVE_STATUSES = {"active", "trial"}

USER_COLUMNS = (
    "id, email, name, rc_subscription_status, "
    "rc_subscription_plan, created_at, subscription_provider"
)


def _normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _has_email(row: dict[str, Any]) -> bool:
    return bool(str(row.get("email") or "").strip())


def is_unsubscribed(row: dict[str, Any]) -> bool:
    status = _normalize_status(row.get("rc_subscription_status"))
    return status not in ACTIVE_STATUSES


def fetch_unsubscribed_users() -> list[dict[str, Any]]:
    supabase = get_supabase()
    response = supabase.table("Users").select(USER_COLUMNS).execute()
    rows = list(response.data or [])

    unsubscribed = [row for row in rows if _has_email(row) and is_unsubscribed(row)]
    unsubscribed.sort(key=lambda row: row.get("id") or 0)
    return unsubscribed
