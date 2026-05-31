"""Fetch users from Supabase and segment for marketing lists."""

from dataclasses import dataclass
from typing import Any, Literal

from report_service.supabase_client import get_supabase

SegmentName = Literal["paid", "trial_not_subscribed", "never_subscribed"]

USER_COLUMNS = (
    "id, email, name, rc_subscription_status, rc_subscription_plan, "
    "created_at, subscription_provider, rc_customer_id, "
    "subscription_status, stripe_subscription_id"
)

ENGAGED_STATUSES = {
    "trial",
    "trialing",
    "expired",
    "canceled",
    "cancelled",
    "billing_issue",
    "paused",
    "past_due",
    "unpaid",
    "incomplete",
    "incomplete_expired",
}


@dataclass
class UserSegments:
    paid: list[dict[str, Any]]
    trial_not_subscribed: list[dict[str, Any]]
    never_subscribed: list[dict[str, Any]]

    @property
    def total(self) -> int:
        return len(self.paid) + len(self.trial_not_subscribed) + len(self.never_subscribed)


def _normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _has_email(row: dict[str, Any]) -> bool:
    return bool(str(row.get("email") or "").strip())


def _has_rc_engagement(row: dict[str, Any]) -> bool:
    return bool(str(row.get("rc_customer_id") or "").strip())


def _has_stripe_engagement(row: dict[str, Any]) -> bool:
    return bool(str(row.get("stripe_subscription_id") or "").strip())


def classify_segment(row: dict[str, Any]) -> SegmentName:
    """
    Segment users for marketing:
    - paid: current paid subscription (not trial)
    - trial_not_subscribed: on trial, or had trial/subscription but not currently paying
    - never_subscribed: installed/signed up but never entered trial or subscription flow
    """
    rc_status = _normalize_status(row.get("rc_subscription_status"))
    stripe_status = _normalize_status(row.get("subscription_status"))

    if rc_status == "active" or stripe_status == "active":
        return "paid"

    if rc_status in ENGAGED_STATUSES or stripe_status in ENGAGED_STATUSES:
        return "trial_not_subscribed"

    if _has_rc_engagement(row) or _has_stripe_engagement(row):
        return "trial_not_subscribed"

    if rc_status or stripe_status:
        return "trial_not_subscribed"

    return "never_subscribed"


def fetch_user_segments() -> UserSegments:
    supabase = get_supabase()
    response = supabase.table("Users").select(USER_COLUMNS).execute()
    rows = [row for row in (response.data or []) if _has_email(row)]

    paid: list[dict[str, Any]] = []
    trial_not_subscribed: list[dict[str, Any]] = []
    never_subscribed: list[dict[str, Any]] = []

    for row in rows:
        segment = classify_segment(row)
        if segment == "paid":
            paid.append(row)
        elif segment == "trial_not_subscribed":
            trial_not_subscribed.append(row)
        else:
            never_subscribed.append(row)

    sort_key = lambda row: row.get("id") or 0
    paid.sort(key=sort_key)
    trial_not_subscribed.sort(key=sort_key)
    never_subscribed.sort(key=sort_key)

    return UserSegments(
        paid=paid,
        trial_not_subscribed=trial_not_subscribed,
        never_subscribed=never_subscribed,
    )
