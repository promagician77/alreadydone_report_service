"""Fetch users from Supabase and segment for marketing lists."""

from dataclasses import dataclass
from typing import Any, Literal

from report_service.supabase_client import get_supabase

SegmentName = Literal["paid", "trial", "unsubscribed"]

USER_COLUMNS = (
    "id, email, name, rc_subscription_status, rc_subscription_plan, "
    "created_at, subscription_provider"
)


@dataclass
class UserSegments:
    paid: list[dict[str, Any]]
    trial: list[dict[str, Any]]
    unsubscribed: list[dict[str, Any]]

    @property
    def total(self) -> int:
        return len(self.paid) + len(self.trial) + len(self.unsubscribed)


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _has_email(row: dict[str, Any]) -> bool:
    return bool(str(row.get("email") or "").strip())


def classify_segment(row: dict[str, Any]) -> SegmentName | None:
    """
    Segment users for marketing (mutually exclusive):
    - trial: rc_subscription_plan is 'trial'
    - paid: rc_subscription_status is 'active' (and not trial plan)
    - unsubscribed: rc_subscription_status is 'inactive'
    """
    plan = _normalize(row.get("rc_subscription_plan"))
    status = _normalize(row.get("rc_subscription_status"))

    if plan == "trial":
        return "trial"
    if status == "active":
        return "paid"
    if status == "inactive":
        return "unsubscribed"
    return None


def fetch_user_segments() -> UserSegments:
    supabase = get_supabase()
    response = supabase.table("Users").select(USER_COLUMNS).execute()
    rows = [row for row in (response.data or []) if _has_email(row)]

    paid: list[dict[str, Any]] = []
    trial: list[dict[str, Any]] = []
    unsubscribed: list[dict[str, Any]] = []

    for row in rows:
        segment = classify_segment(row)
        if segment == "paid":
            paid.append(row)
        elif segment == "trial":
            trial.append(row)
        elif segment == "unsubscribed":
            unsubscribed.append(row)

    sort_key = lambda row: row.get("id") or 0
    paid.sort(key=sort_key)
    trial.sort(key=sort_key)
    unsubscribed.sort(key=sort_key)

    return UserSegments(paid=paid, trial=trial, unsubscribed=unsubscribed)
