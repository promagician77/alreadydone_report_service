"""Fetch users from Supabase and segment for marketing lists."""

from dataclasses import dataclass
from typing import Any, Literal

from report_service.supabase_client import get_supabase

SegmentName = Literal["paid", "trial", "unsubscribed", "never_subscribed"]

USER_COLUMNS = (
    "id, email, name, rc_subscription_status, rc_subscription_plan, "
    "created_at, subscription_provider"
)


@dataclass
class UserSegments:
    paid: list[dict[str, Any]]
    trial: list[dict[str, Any]]
    unsubscribed: list[dict[str, Any]]
    never_subscribed: list[dict[str, Any]] 

    @property
    def total(self) -> int:
        return (
            len(self.paid)
            + len(self.trial)
            + len(self.unsubscribed)
            + len(self.never_subscribed)
        )


def _normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _has_email(row: dict[str, Any]) -> bool:
    return bool(str(row.get("email") or "").strip())


def classify_segment(row: dict[str, Any]) -> SegmentName:
    """
    Segment users by rc_subscription_status only:
    - paid: active
    - trial: trial
    - unsubscribed: inactive (had trial/subscription flow, not currently paying)
    - never_subscribed: null/empty or any other status
    """
    rc_status = _normalize_status(row.get("rc_subscription_status"))

    if rc_status == "active":
        return "paid"
    if rc_status == "trial":
        return "trial"
    if rc_status == "inactive":
        return "unsubscribed"
    return "never_subscribed"


def fetch_user_segments() -> UserSegments:
    supabase = get_supabase()
    response = supabase.table("Users").select(USER_COLUMNS).execute()
    rows = [row for row in (response.data or []) if _has_email(row)]

    paid: list[dict[str, Any]] = []
    trial: list[dict[str, Any]] = []
    unsubscribed: list[dict[str, Any]] = []
    never_subscribed: list[dict[str, Any]] = []

    for row in rows:
        segment = classify_segment(row)
        if segment == "paid":
            paid.append(row)
        elif segment == "trial":
            trial.append(row)
        elif segment == "unsubscribed":
            unsubscribed.append(row)
        else:
            never_subscribed.append(row)

    sort_key = lambda row: row.get("id") or 0
    paid.sort(key=sort_key)
    trial.sort(key=sort_key)
    unsubscribed.sort(key=sort_key)
    never_subscribed.sort(key=sort_key)

    return UserSegments(
        paid=paid,
        trial=trial,
        unsubscribed=unsubscribed,
        never_subscribed=never_subscribed,
    )
