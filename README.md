# Already Done — Daily User Segment Report

Standalone Python service that queries Supabase and emails **one daily report** to a single client address via SendGrid. Users are split into **4 marketing segments** by `rc_subscription_status`, each with its own CSV attachment:

1. **Paid subscribers** — `rc_subscription_status` = `active`
2. **Trial users** — `rc_subscription_status` = `trial`
3. **Unsubscribed** — `rc_subscription_status` = `inactive`
4. **Never trial or subscription** — empty/null or any other status

## Schedule

The systemd timer runs **every day at 8:00 AM Pacific Time** (`America/Los_Angeles`).

- **PST** (winter): 8:00 AM PST = 16:00 UTC  
- **PDT** (summer): 8:00 AM PDT = 15:00 UTC  

Report subject dates and CSV filenames use the same Pacific timezone.

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

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase service role key |
| `SENDGRID_API_KEY` | Yes (unless dry run) | SendGrid API key |
| `REPORT_FROM_EMAIL` | Yes (unless dry run) | Verified sender in SendGrid |
| `REPORT_TO_EMAIL` | Yes (unless dry run) | Report recipient |
| `REPORT_DRY_RUN` | No | `true` = no email sent |

## Manual run

```bash
REPORT_DRY_RUN=true venv/bin/python daily_unsubscribed_report.py
venv/bin/python daily_unsubscribed_report.py
```

## Deploy on VPS (systemd timer)

```bash
cd /root/alreadydone_report_service
mkdir -p logs

sudo cp deploy/alreadyapp-unsubscribed-report.service /etc/systemd/system/
sudo cp deploy/alreadyapp-unsubscribed-report.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now alreadyapp-unsubscribed-report.timer
```

Verify next run (should show **08:00** with Pacific/UTC offset):

```bash
sudo systemctl list-timers | grep unsubscribed
```

If `Timezone=` is not supported on an older systemd, edit the timer and use:

```ini
OnCalendar=*-*-* 08:00:00 America/Los_Angeles
```

## Email attachments

- `paid_YYYY-MM-DD.csv`
- `trial_YYYY-MM-DD.csv`
- `unsubscribed_YYYY-MM-DD.csv`
- `never_subscribed_YYYY-MM-DD.csv`

Dates are **Pacific** (`America/Los_Angeles`).

## Useful commands

```bash
sudo systemctl start alreadyapp-unsubscribed-report.service
sudo systemctl status alreadyapp-unsubscribed-report.service
tail -f /root/alreadydone_report_service/logs/report.log
```
