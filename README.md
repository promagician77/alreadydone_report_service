# Already Done — Daily User Segment Report

Standalone Python service that queries Supabase and emails **one daily report** to a single client address via SendGrid. The report splits users into **3 marketing segments**, each with its own CSV attachment:

1. **Paid subscribers** — `rc_subscription_status` is `active` (and plan is not `trial`)
2. **Trial (not subscribed)** — `rc_subscription_plan` is `trial`
3. **Unsubscribed** — `rc_subscription_status` is `inactive`

This runs as a **separate process** from the FastAPI backend (`alreadydone_backend`).

## Setup

```bash
cd alreadydone_report_service

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

cp .env.example .env
# Edit .env with your values
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL (same as backend) |
| `SUPABASE_KEY` | Yes | Supabase service role key |
| `SENDGRID_API_KEY` | Yes (unless dry run) | SendGrid API key |
| `REPORT_FROM_EMAIL` | Yes (unless dry run) | Verified sender in SendGrid |
| `REPORT_TO_EMAIL` | Yes (unless dry run) | Single recipient for the daily report |
| `REPORT_DRY_RUN` | No | `true` to print preview without sending (default: `false`) |

## Manual run

```bash
# Dry run — prints summary + CSV preview, no email
REPORT_DRY_RUN=true .venv/bin/python daily_unsubscribed_report.py

# Live send to REPORT_TO_EMAIL
.venv/bin/python daily_unsubscribed_report.py
```

## Deploy on VPS (systemd timer)

```bash
cd ~/alreadydone_report_service

python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
mkdir -p logs

REPORT_DRY_RUN=true venv/bin/python daily_unsubscribed_report.py

sudo cp deploy/alreadyapp-unsubscribed-report.service /etc/systemd/system/
sudo cp deploy/alreadyapp-unsubscribed-report.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now alreadyapp-unsubscribed-report.timer
```

Default schedule: **08:00** in the **server's local timezone**. Check with `timedatectl` and `systemctl list-timers`.

### Useful commands

```bash
sudo systemctl start alreadyapp-unsubscribed-report.service
sudo systemctl list-timers | grep unsubscribed
tail -f logs/report.log
```

## Segment definitions

Only users with a non-empty `email` are included. Segments are **mutually exclusive** (checked in this order):

| Segment | Rule |
|---------|------|
| **Trial** | `rc_subscription_plan` is `trial` |
| **Paid** | `rc_subscription_status` is `active` |
| **Unsubscribed** | `rc_subscription_status` is `inactive` |

Users who do not match any rule (e.g. `expired`, `canceled`, empty status) are **not included** in the report.

## Email contents

- **Subject:** `Already Done — User segments (YYYY-MM-DD) — N total (paid X, trial Y, unsubscribed Z)`
- **Body:** HTML summary with 3 sections (first 25 rows each)
- **Attachments:**
  - `paid_YYYY-MM-DD.csv`
  - `trial_YYYY-MM-DD.csv`
  - `unsubscribed_YYYY-MM-DD.csv`

## Report columns (each CSV)

- ID, Email, Name, RC Status, RC Plan, Created At, Provider
