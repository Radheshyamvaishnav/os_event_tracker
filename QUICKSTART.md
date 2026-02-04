# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install requests beautifulsoup4 lxml
```

### Step 2: Get Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable 2-Step Verification if not already enabled
3. Scroll to "App passwords" and click it
4. Select "Mail" and "Other (Custom name)"
5. Name it "Event Tracker" and generate
6. Copy the 16-character password (e.g., "abcd efgh ijkl mnop")

### Step 3: Configure Email

Run the script once to create config.json:
```bash
python event_tracker.py --once
```

Edit `config.json` with your details:
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "youremail@gmail.com",
    "sender_password": "abcdefghijklmnop",
    "recipient_emails": [
      "youremail@gmail.com",
      "family@gmail.com",
      "friend@gmail.com"
    ]
  },
  "check_interval_minutes": 60
}
```

**Tip:** Add as many email addresses as you want in the `recipient_emails` array!

### Step 4: Test It

```bash
python event_tracker.py --once
```

You should receive an email with all current events!

### Step 5: Run Continuously

```bash
python event_tracker.py
```

The script will now check for new events every hour and email you automatically.

## That's It! 🎉

Keep the terminal window open, or set up as a background service (see README.md).

## Quick Commands

| Command | Purpose |
|---------|---------|
| `python event_tracker.py` | Run continuously |
| `python event_tracker.py --once` | Check once and exit |
| `Ctrl+C` | Stop the script |

## First Time Users

On your first run, you'll get an email with ALL current events. This is normal! After that, you'll only get emails when NEW events are added.

## Troubleshooting

**Email not working?**
- Check you're using the App Password, not your regular Gmail password
- Verify sender_email and recipient_email are correct
- Check event_tracker.log for errors

**No emails after setup?**
- That's normal! You only get emails when NEW events are added
- The script is working - check the log file to confirm

**Want to test again?**
- Delete `events_data.json` and run `python event_tracker.py --once`
- You'll get an email with all events again
