#!/usr/bin/env python3
"""
Om Swami Events Tracker
Monitors https://omswami.org/events for new events and sends email notifications
"""

import requests
from bs4 import BeautifulSoup, NavigableString
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import hashlib
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('event_tracker.log'),
        logging.StreamHandler()
    ]
)

class OmSwamiEventTracker:
    def __init__(self, config_file='config.json'):
        """Initialize the event tracker with configuration"""
        self.url = "https://omswami.org/events"
        self.events_file = "events_data.json"
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """Load email configuration from file or environment variables"""
        # Try to load from environment variables first (for cloud deployment)
        if os.environ.get('SENDER_EMAIL'):
            logging.info("Loading configuration from environment variables")
            try:
                recipient_emails_str = os.environ.get('RECIPIENT_EMAILS', '[]')
                recipient_emails = json.loads(recipient_emails_str)
                
                return {
                    "email": {
                        "smtp_server": os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
                        "smtp_port": int(os.environ.get('SMTP_PORT', 587)),
                        "sender_email": os.environ['SENDER_EMAIL'],
                        "sender_password": os.environ['SENDER_PASSWORD'],
                        "recipient_emails": recipient_emails
                    },
                    "check_interval_minutes": int(os.environ.get('CHECK_INTERVAL_MINUTES', 60))
                }
            except (json.JSONDecodeError, KeyError) as e:
                logging.error(f"Error loading config from environment: {e}")
                logging.warning("Falling back to config file")
        
        # Fall back to config.json file
        if os.path.exists(self.config_file):
            logging.info("Loading configuration from config.json")
            with open(self.config_file, 'r') as f:
                return json.load(f)
        else:
            # Create default config file
            default_config = {
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "sender_email": "your_email@gmail.com",
                    "sender_password": "your_app_password",
                    "recipient_emails": [
                        "recipient1@gmail.com",
                        "recipient2@gmail.com"
                    ]
                },
                "check_interval_minutes": 60
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            logging.warning(f"Created default config file: {self.config_file}")
            logging.warning("Please update the config file with your email credentials!")
            return default_config
    
    def fetch_events(self):
        """Fetch and parse events from the website"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Find all event cards - they contain h3 titles
            event_sections = soup.find_all('h3')
            
            for section in event_sections:
                # Get the event title
                title = section.get_text(strip=True)
                
                # Skip if it's not an event (like "Event Gallery" or "Download Pics")
                if title in ["Event Gallery", "Download Pics"]:
                    continue
                
                # Find the parent container to get more details
                parent = section.find_parent()
                
                # Try to find event dates - they appear after calendar icon
                date_info = "Date not specified"
                
                # Look for calendar icon after the title (h3)
                calendar_icon = section.find_next('img', alt='Event Date')
                
                if calendar_icon:
                    logging.debug(f"Found calendar icon for event: {title}")
                    
                    # Try next_siblings first
                    found = False
                    sibling_count = 0
                    
                    for idx, sibling in enumerate(calendar_icon.next_siblings):
                        sibling_count += 1
                        if isinstance(sibling, (str, NavigableString)):
                            # It's a text node
                            date_text = str(sibling).strip()
                            logging.debug(f"  Sibling {idx} (text): '{date_text[:50]}'")
                            
                            if date_text and len(date_text) > 3:  # Valid date text
                                date_info = date_text
                                logging.info(f"Found date for '{title}': {date_info}")
                                found = True
                                break
                        else:
                            # It's an element
                            date_text = sibling.get_text(strip=True)
                            logging.debug(f"  Sibling {idx} (element): '{date_text[:50]}'")
                            
                            if date_text and len(date_text) > 3 and not date_text.startswith('Event Details'):
                                date_info = date_text
                                logging.info(f"Found date for '{title}': {date_info}")
                                found = True
                                break
                        
                        if idx > 10:  # Safety limit
                            break
                    
                    # If no siblings found, try parent's siblings
                    if not found and sibling_count == 0:
                        logging.debug(f"  No next_siblings found, trying parent's siblings")
                        parent_elem = calendar_icon.parent
                        
                        for idx, sibling in enumerate(parent_elem.next_siblings):
                            if isinstance(sibling, (str, NavigableString)):
                                date_text = str(sibling).strip()
                                logging.debug(f"  Parent sibling {idx} (text): '{date_text[:50]}'")
                                if date_text and len(date_text) > 3:
                                    date_info = date_text
                                    logging.info(f"Found date for '{title}': {date_info}")
                                    break
                            else:
                                date_text = sibling.get_text(strip=True)
                                logging.debug(f"  Parent sibling {idx} (element): '{date_text[:50]}'")
                                if date_text and len(date_text) > 3:
                                    date_info = date_text
                                    logging.info(f"Found date for '{title}': {date_info}")
                                    break
                            
                            if idx > 10:
                                break
                else:
                    logging.warning(f"No calendar icon found for event: {title}")
                
                # Get event description (first few paragraphs)
                description = ""
                if parent:
                    paragraphs = parent.find_all('p')[:2]  # Get first 2 paragraphs
                    description = ' '.join([p.get_text(strip=True) for p in paragraphs])
                
                # Create event ID based on title
                event_id = hashlib.md5(title.encode()).hexdigest()
                
                event = {
                    'id': event_id,
                    'title': title,
                    'date': date_info,
                    'description': description[:500] if description else 'No description available',
                    'url': self.url,
                    'discovered_at': datetime.now().isoformat()
                }
                
                events.append(event)
            
            logging.info(f"Successfully fetched {len(events)} events")
            return events
            
        except requests.RequestException as e:
            logging.error(f"Error fetching events: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error parsing events: {e}")
            return []
    
    def load_previous_events(self):
        """Load previously stored events"""
        if os.path.exists(self.events_file):
            try:
                with open(self.events_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logging.warning("Could not decode events file, starting fresh")
                return []
        return []
    
    def save_events(self, events):
        """Save events to file"""
        with open(self.events_file, 'w') as f:
            json.dump(events, f, indent=2)
        logging.info(f"Saved {len(events)} events to {self.events_file}")
    
    def find_new_events(self, current_events, previous_events):
        """Compare current and previous events to find new ones"""
        previous_ids = {event['id'] for event in previous_events}
        new_events = [event for event in current_events if event['id'] not in previous_ids]
        return new_events
    
    def send_email_notification(self, new_events):
        """Send email notification about new events"""
        try:
            email_config = self.config['email']
            
            # Support both single recipient (backward compatibility) and multiple recipients
            recipients = email_config.get('recipient_emails', [])
            
            # Backward compatibility: if old 'recipient_email' key exists, use it
            if not recipients and 'recipient_email' in email_config:
                recipients = [email_config['recipient_email']]
            
            if not recipients:
                logging.error("No recipient emails configured!")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🔔 New Event(s) on Om Swami Ashram - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = email_config['sender_email']
            msg['To'] = ', '.join(recipients)  # Join all recipients for display
            
            # Create email body
            text_parts = ["New events have been added to Om Swami Ashram website!\n\n"]
            html_parts = ["""
            <html>
              <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #ff6b35;">🔔 New Events on Om Swami Ashram</h2>
                <p>The following new event(s) have been discovered:</p>
            """]
            
            for event in new_events:
                # Text version
                text_parts.append(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
                text_parts.append(f"Event: {event['title']}\n")
                text_parts.append(f"Date: {event['date']}\n")
                text_parts.append(f"Description: {event['description']}\n")
                text_parts.append(f"Link: {event['url']}\n\n")
                
                # HTML version
                html_parts.append(f"""
                <div style="margin: 20px 0; padding: 15px; border-left: 4px solid #ff6b35; background-color: #f9f9f9;">
                    <h3 style="color: #333; margin-top: 0;">{event['title']}</h3>
                    <p><strong>📅 Date:</strong> {event['date']}</p>
                    <p><strong>📝 Description:</strong> {event['description']}</p>
                    <p><a href="{event['url']}" style="color: #ff6b35; text-decoration: none;">View Event Details →</a></p>
                </div>
                """)
            
            text_parts.append("\nVisit the events page: https://omswami.org/events")
            text_parts.append("\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            text_parts.append("At the holy feet of the Great Guru, Om Swami,\n")
            text_parts.append("I offer my obeisances with devotion.\n")
            text_parts.append("Made with ❤️ by Radheshyam Om.\n")
            
            html_parts.append("""
                <p style="margin-top: 30px;">
                    <a href="https://omswami.org/events" 
                       style="display: inline-block; padding: 10px 20px; background-color: #ff6b35; 
                              color: white; text-decoration: none; border-radius: 5px;">
                        Visit Events Page
                    </a>
                </p>
                <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                <div style="margin-top: 30px; padding: 20px; background: linear-gradient(135deg, #fff5f0 0%, #ffe8dd 100%); 
                            border-left: 4px solid #ff6b35; border-radius: 5px; text-align: center;">
                    <p style="color: #8b4513; font-size: 14px; font-style: italic; margin: 0; line-height: 1.6;">
                        At the holy feet of the Great Guru, Om Swami,<br>
                        I offer my obeisances with devotion.
                    </p>
                    <p style="color: #666; font-size: 12px; margin-top: 10px;">
                        Made with ❤️ by Radheshyam Om.
                    </p>
                </div>
                <p style="color: #999; font-size: 11px; margin-top: 20px; text-align: center;">
                    This is an automated notification from your Om Swami Events Tracker.
                </p>
              </body>
            </html>
            """)
            
            # Attach both versions
            text_body = ''.join(text_parts)
            html_body = ''.join(html_parts)
            
            msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email to all recipients
            with smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port']) as server:
                server.starttls()
                server.login(email_config['sender_email'], email_config['sender_password'])
                server.send_message(msg, to_addrs=recipients)
            
            logging.info(f"Email notification sent successfully to {len(recipients)} recipient(s): {', '.join(recipients)}")
            return True
            
        except Exception as e:
            logging.error(f"Error sending email: {e}")
            return False
    
    def check_for_new_events(self):
        """Main method to check for new events"""
        logging.info("Checking for new events...")
        
        # Fetch current events
        current_events = self.fetch_events()
        if not current_events:
            logging.warning("No events fetched, skipping this check")
            return
        
        # Load previous events
        previous_events = self.load_previous_events()
        
        # Find new events
        new_events = self.find_new_events(current_events, previous_events)
        
        if new_events:
            logging.info(f"Found {len(new_events)} new event(s)!")
            for event in new_events:
                logging.info(f"  - {event['title']}")
            
            # Send notification
            self.send_email_notification(new_events)
        else:
            logging.info("No new events found")
        
        # Save current events for next comparison
        self.save_events(current_events)
    
    def run_continuous(self):
        """Run the tracker continuously with specified interval"""
        interval_minutes = self.config.get('check_interval_minutes', 60)
        interval_seconds = interval_minutes * 60
        
        logging.info(f"Starting continuous monitoring (checking every {interval_minutes} minutes)")
        logging.info("Press Ctrl+C to stop")
        
        try:
            while True:
                self.check_for_new_events()
                logging.info(f"Next check in {interval_minutes} minutes...")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logging.info("Tracker stopped by user")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Om Swami Events Tracker')
    parser.add_argument('--once', action='store_true', 
                       help='Run once and exit (for cron jobs)')
    parser.add_argument('--config', default='config.json',
                       help='Path to config file (default: config.json)')
    
    args = parser.parse_args()
    
    tracker = OmSwamiEventTracker(config_file=args.config)
    
    if args.once:
        tracker.check_for_new_events()
    else:
        tracker.run_continuous()


if __name__ == "__main__":
    main()
