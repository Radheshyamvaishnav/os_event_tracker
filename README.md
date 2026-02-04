# Om Swami Events Tracker

A Python script that monitors the Om Swami Ashram events page (https://omswami.org/events) and sends email notifications whenever new events are added.

## Features

- 🔍 Automatically scrapes the events page
- 📧 Sends beautiful HTML email notifications for new events
- 💾 Stores event history to track changes
- 🔄 Runs continuously or as a one-time check
- 📝 Detailed logging for monitoring
- ⚙️ Easy configuration via JSON file

## Requirements

- Python 3.7 or higher
- Internet connection

## Installation

1. **Clone or download this repository**

2. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Set up your email credentials:**

   On first run, the script will create a `config.json` file. Edit it with your email settings:

   ```json
   {
     "email": {
       "smtp_server": "smtp.gmail.com",
       "smtp_port": 587,
       "sender_email": "your_email@gmail.com",
       "sender_password": "your_app_password",
       "recipient_emails": [
         "recipient1@gmail.com",
         "recipient2@gmail.com",
         "recipient3@gmail.com"
       ]
     },
     "check_interval_minutes": 60
   }
   ```

   **Note:** You can add as many recipient email addresses as you need in the `recipient_emails` array.

2. **For Gmail users:**
   
   You need to create an "App Password" instead of using your regular password:
   
   a. Go to your Google Account settings
   b. Navigate to Security → 2-Step Verification (enable if not already)
   c. Scroll down to "App passwords"
   d. Generate a new app password for "Mail"
   e. Use this 16-character password in your config.json

3. **For other email providers:**
   
   Update the `smtp_server` and `smtp_port` according to your provider:
   - **Outlook/Hotmail**: smtp.office365.com, port 587
   - **Yahoo**: smtp.mail.yahoo.com, port 587
   - **Custom SMTP**: Check your provider's documentation

## Usage

### Run Continuously (Recommended)

The script will check for new events at regular intervals:

```bash
python event_tracker.py
```

By default, it checks every 60 minutes. You can change this in `config.json`.

### Run Once (For Cron Jobs)

If you want to use a cron job or task scheduler:

```bash
python event_tracker.py --once
```

### Using a Custom Config File

```bash
python event_tracker.py --config /path/to/custom_config.json
```

## Setting Up Automated Checks

### Linux/Mac (Cron)

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add a line to run every hour:
   ```
   0 * * * * /usr/bin/python3 /path/to/event_tracker.py --once
   ```

3. Or check every 30 minutes:
   ```
   */30 * * * * /usr/bin/python3 /path/to/event_tracker.py --once
   ```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create a new Basic Task
3. Set the trigger (e.g., daily at specific times or every hour)
4. Set the action to run: `python event_tracker.py --once`
5. Set the "Start in" directory to where your script is located

### Running as a Background Service (Linux)

You can run the script continuously in the background:

```bash
nohup python event_tracker.py &
```

Or create a systemd service for better management.

## How It Works

1. **Scraping**: The script fetches the events page and extracts event information (title, date, description)
2. **Storage**: Events are stored in `events_data.json` with unique IDs
3. **Comparison**: On each check, current events are compared with stored events
4. **Notification**: If new events are found, an email is sent with event details
5. **Logging**: All activities are logged to `event_tracker.log` and console

## Files Created

- `config.json` - Your configuration settings
- `events_data.json` - Stores previously seen events
- `event_tracker.log` - Log file with all activity

## Email Notification Format

You'll receive a nicely formatted HTML email containing:
- Event title
- Event date
- Event description
- Direct link to the events page

## Troubleshooting

### Email not sending

1. **Check your credentials** in `config.json`
2. **For Gmail**: Make sure you're using an App Password, not your regular password
3. **Check the logs** in `event_tracker.log` for specific error messages
4. **Firewall**: Ensure your firewall allows outbound SMTP connections

### No events detected

1. Check `event_tracker.log` for errors
2. Verify internet connectivity
3. The website structure may have changed - check if the script needs updating

### Script crashes

1. Check `event_tracker.log` for error details
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Verify Python version is 3.7+: `python --version`

## Testing

To test if everything is set up correctly:

1. Run the script once:
   ```bash
   python event_tracker.py --once
   ```

2. Check `event_tracker.log` for any errors

3. On the first run, all current events will be considered "new" and you'll receive an email

4. Run it again - you shouldn't receive an email (no new events)

5. When an actual new event is added to the website, you'll get notified!

## Customization

### Multiple Recipients

The script supports sending notifications to multiple email addresses. Simply add all email addresses to the `recipient_emails` array in your config:

```json
{
  "email": {
    "recipient_emails": [
      "person1@gmail.com",
      "person2@yahoo.com",
      "person3@outlook.com"
    ]
  }
}
```

All recipients will receive the same notification email when new events are detected.

**Backward Compatibility:** If you're upgrading from an older version that used `recipient_email` (singular), the script will still work. However, it's recommended to update to the new `recipient_emails` (plural) array format.

### Change Check Interval

Edit `check_interval_minutes` in `config.json`:

```json
{
  "check_interval_minutes": 30
}
```

### Modify Email Template

Edit the `send_email_notification` method in `event_tracker.py` to customize the email format.

### Add More Event Details

Modify the `fetch_events` method to extract additional information from the website.

## Security Notes

- Never commit `config.json` with real credentials to version control
- Use app-specific passwords instead of your main email password
- Keep your config file permissions restricted (chmod 600 on Linux/Mac)

## License

This script is provided as-is for personal use. Please respect the Om Swami website's terms of service and don't overload their servers with too frequent requests.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the log file for detailed error messages
3. Ensure you're using the latest version of the script

## Changelog

### Version 1.1
- **New Feature**: Multiple recipients support - send notifications to multiple email addresses
- Backward compatibility with single recipient configuration
- Enhanced logging to show number of recipients

### Version 1.0
- Initial release
- Event monitoring and email notifications
- Continuous and one-time run modes
- Detailed logging
- HTML email formatting
