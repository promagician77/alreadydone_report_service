# Already Done — Daily User Segment Report

Standalone Python service that queries Supabase and emails **one daily report** to a single client address via SendGrid. The report splits users into **3 marketing segments**, each with its own CSV attachment:

1. **Paid subscribers** — active paid subscription (not trial)
2. **Trial (not subscribed)** — on trial, or had trial/subscription but not currently paying
3. **Never trial or subscription** — installed/signed up but never entered the subscription flow

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

Recommended path on the server: `/root/alreadyapp-report-service`

```bash
cd /root/alreadydone_report_service   # or your deploy path

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

Only users with a non-empty `email` are included.

### 1. Paid subscribers

- `rc_subscription_status` is `active`, or
- legacy `subscription_status` is `active`

### 2. Trial (not subscribed)

Users who engaged with subscription but are **not** currently paying, including:

- Currently on trial (`trial` / `trialing`)
- Expired, canceled, billing issue, paused, etc.
- Has `rc_customer_id` or `stripe_subscription_id` without active paid status

Note: users who paid and later canceled are grouped here (no historical trial flag in the DB).

### 3. Never trial or subscription

- No meaningful subscription status
- No `rc_customer_id` or `stripe_subscription_id`

## Email contents

- **Subject:** `Already Done — User segments (YYYY-MM-DD) — N total (paid X, trial Y, never Z)`
- **Body:** HTML summary with 3 sections (first 25 rows each)
- **Attachments:**
  - `paid_YYYY-MM-DD.csv`
  - `trial_not_subscribed_YYYY-MM-DD.csv`
  - `never_subscribed_YYYY-MM-DD.csv`

## Report columns (each CSV)

- ID, Email, Name, RC Status, RC Plan, Stripe Status, Created At, Provider
