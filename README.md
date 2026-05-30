# Already Done — Daily Unsubscribed Users Report

Standalone Python service that queries Supabase for users who are **not** subscribed (`rc_subscription_status` not in `active`/`trial`) and emails **one daily report** to a single client address via SendGrid. The report includes an HTML summary and a CSV attachment.

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
# Copy or clone this folder to the VPS
cd /root/alreadyapp-report-service

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Fill in SUPABASE_*, SENDGRID_*, REPORT_* values

mkdir -p logs

# Test before enabling timer
REPORT_DRY_RUN=true .venv/bin/python daily_unsubscribed_report.py

# Install systemd units (adjust paths in unit files if deploy dir differs)
sudo cp deploy/alreadyapp-unsubscribed-report.service /etc/systemd/system/
sudo cp deploy/alreadyapp-unsubscribed-report.timer /etc/systemd/system/

sudo systemctl daemon-reload
sudo systemctl enable --now alreadyapp-unsubscribed-report.timer
```

Default schedule: **08:00 UTC daily**. Edit `OnCalendar` in `deploy/alreadyapp-unsubscribed-report.timer` to change it.

### Useful commands

```bash
# Trigger a run immediately (same as timer would)
sudo systemctl start alreadyapp-unsubscribed-report.service

# Timer status
sudo systemctl list-timers | grep unsubscribed
sudo systemctl status alreadyapp-unsubscribed-report.timer

# Logs
tail -f /root/alreadyapp-report-service/logs/report.log
```

## Unsubscribed user definition

Matches the mobile app logic:

- **Subscribed:** `rc_subscription_status` is `active` or `trial`
- **Unsubscribed:** any other value, or null/empty

Only users with a non-empty `email` are included in the report.

## Report columns

- ID
- Email
- Name
- Status (`rc_subscription_status`)
- Plan (`rc_subscription_plan`)
- Created At
- Provider (`subscription_provider`)
