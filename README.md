# Already Done — Daily User Segment Report

Standalone Python service that queries Supabase and emails **one daily report** to a single client address via SendGrid. Users are split into **4 marketing segments** by `rc_subscription_status`, each with its own CSV attachment:

1. **Paid subscribers** — `rc_subscription_status` = `active`
2. **Trial users** — `rc_subscription_status` = `trial`
3. **Unsubscribed** — `rc_subscription_status` = `inactive`
4. **Never trial or subscription** — empty/null or any other status

## Segment rules

| Segment | `rc_subscription_status` |
|---------|---------------------------|
| Paid | `active` |
| Trial | `trial` |
| Unsubscribed | `inactive` |
| Never trial or subscription | empty, null, or anything else |

Only users with a non-empty `email` are included.

## Setup

```bash
cd alreadydone_report_service
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
```

## Manual run

```bash
REPORT_DRY_RUN=true venv/bin/python daily_unsubscribed_report.py
venv/bin/python daily_unsubscribed_report.py
```

## Email attachments

- `paid_YYYY-MM-DD.csv`
- `trial_YYYY-MM-DD.csv`
- `unsubscribed_YYYY-MM-DD.csv`
- `never_subscribed_YYYY-MM-DD.csv`

See earlier sections in this README for env vars, VPS systemd timer setup, and useful commands.
