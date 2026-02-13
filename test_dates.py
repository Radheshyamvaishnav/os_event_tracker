#!/usr/bin/env python3
"""
Test script for event tracker date extraction
Run this before committing to verify everything works
"""

import requests
from bs4 import BeautifulSoup, NavigableString
import hashlib
from datetime import datetime

# Copy the fetch_events function logic here for testing
def test_fetch_events():
    """Test version of fetch_events"""
    url = "https://omswami.org/events"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        events = []
        
        # Find all event cards - they contain h3 titles
        event_sections = soup.find_all('h3')
        
        print(f"Found {len(event_sections)} h3 elements")
        print("=" * 80)
        
        for section in event_sections:
            # Get the event title
            title = section.get_text(strip=True)
            
            # Skip if it's not an event
            if title in ["Event Gallery", "Download Pics"]:
                print(f"\n⊘ Skipping: {title}")
                continue
            
            print(f"\n{'='*80}")
            print(f"EVENT: {title}")
            print(f"{'='*80}")
            
            # Find the parent container
            parent = section.find_parent()
            
            # Try to find event dates
            date_info = "Date not specified"
            
            # Look for calendar icon after the title (h3)
            calendar_icon = section.find_next('img', alt='Event Date')
            
            if calendar_icon:
                print("✓ Found calendar icon")
                print(f"  Calendar icon tag: {calendar_icon.name}")
                print(f"  Calendar parent: {calendar_icon.parent.name}")
                
                # Try next_siblings
                sibling_count = 0
                for idx, sibling in enumerate(calendar_icon.next_siblings):
                    sibling_count += 1
                    if isinstance(sibling, (str, NavigableString)):
                        # It's a text node
                        date_text = str(sibling).strip()
                        print(f"  Sibling {idx} (text): '{date_text[:80]}'")
                        
                        if date_text and len(date_text) > 3:  # Valid date text
                            date_info = date_text
                            print(f"  ✓✓ SELECTED AS DATE: {date_info}")
                            break
                    else:
                        # It's an element
                        date_text = sibling.get_text(strip=True)
                        print(f"  Sibling {idx} (element {sibling.name}): '{date_text[:80]}'")
                        
                        if date_text and len(date_text) > 3 and not date_text.startswith('Event Details'):
                            date_info = date_text
                            print(f"  ✓✓ SELECTED AS DATE: {date_info}")
                            break
                    
                    if idx > 10:  # Safety limit
                        print("  ⚠ Reached safety limit (10 siblings)")
                        break
                
                if sibling_count == 0:
                    print("  ⚠ WARNING: Calendar icon has NO next_siblings!")
                    print("  Trying parent's next_siblings instead...")
                    
                    parent = calendar_icon.parent
                    for idx, sibling in enumerate(parent.next_siblings):
                        if isinstance(sibling, (str, NavigableString)):
                            date_text = str(sibling).strip()
                            print(f"  Parent sibling {idx} (text): '{date_text[:80]}'")
                            if date_text and len(date_text) > 3:
                                date_info = date_text
                                print(f"  ✓✓ SELECTED AS DATE: {date_info}")
                                break
                        else:
                            date_text = sibling.get_text(strip=True)
                            print(f"  Parent sibling {idx} (element): '{date_text[:80]}'")
                            if date_text and len(date_text) > 3:
                                date_info = date_text
                                print(f"  ✓✓ SELECTED AS DATE: {date_info}")
                                break
                        
                        if idx > 10:
                            break
            else:
                print("✗ No calendar icon found")
            
            # Get event description
            description = ""
            if parent:
                paragraphs = parent.find_all('p')[:2]
                description = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            # Create event
            event_id = hashlib.md5(title.encode()).hexdigest()
            
            event = {
                'id': event_id,
                'title': title,
                'date': date_info,
                'description': description[:100] + '...' if len(description) > 100 else description,
                'url': url,
                'discovered_at': datetime.now().isoformat()
            }
            
            events.append(event)
            
            print(f"\nFINAL RESULT:")
            print(f"  Title: {event['title']}")
            print(f"  Date: {event['date']}")
            print(f"  Description: {event['description'][:80]}...")
        
        print(f"\n{'='*80}")
        print(f"SUMMARY: Found {len(events)} events")
        print(f"{'='*80}\n")
        
        for i, event in enumerate(events, 1):
            print(f"{i}. {event['title']}")
            print(f"   Date: {event['date']}")
            print(f"   ID: {event['id']}")
            print()
        
        # Check if any dates are missing
        missing_dates = [e['title'] for e in events if e['date'] == "Date not specified"]
        if missing_dates:
            print("⚠ WARNING: The following events have no date:")
            for title in missing_dates:
                print(f"  - {title}")
            print()
            return False
        else:
            print("✓ SUCCESS: All events have dates!")
            return True
            
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("EVENT TRACKER - DATE EXTRACTION TEST")
    print("="*80 + "\n")
    
    success = test_fetch_events()
    
    print("\n" + "="*80)
    if success:
        print("✓✓✓ TEST PASSED - All events have dates!")
        print("You can safely commit and push now.")
    else:
        print("✗✗✗ TEST FAILED - Some events are missing dates")
        print("DO NOT commit yet. Check the output above for details.")
    print("="*80 + "\n")
    
    exit(0 if success else 1)
