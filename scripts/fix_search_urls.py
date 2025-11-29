#!/usr/bin/env python3
"""
Fix Search URLs Script
Replaces search URLs with actual Slickdeals deal URLs in deals.json
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote, unquote, parse_qs, urlparse
from urllib.error import URLError, HTTPError

DATA_DIR = Path(__file__).parent.parent / 'data'
DEALS_FILE = DATA_DIR / 'deals.json'

# User agent for web requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


def is_search_url(url):
    """Check if URL is a search URL rather than a direct deal link."""
    if not url:
        return False
    return 'newsearch.php' in url or '/newsearch.php' in url


def normalize_link(raw_link):
    """Normalize a Slickdeals link to include sdtrk=bfsheet."""
    if not raw_link:
        return ''

    link = str(raw_link).strip()
    if not link:
        return ''

    if 'sdtrk=bfsheet' in link:
        return link

    if '?' in link:
        return link + '&sdtrk=bfsheet'
    else:
        return link + '?sdtrk=bfsheet'


def fetch_actual_deal_url(title):
    """
    Search Slickdeals for a deal title and return the actual deal URL.
    Returns None if no matching deal is found.
    """
    try:
        # Clean title for search
        search_title = title
        for separator in [' $', ' from ', ' +', ' -', ' @']:
            if separator in search_title:
                search_title = search_title.split(separator)[0]
        
        search_title = search_title.replace('(various colors)', '').replace('(various sizes)', '')
        search_title = search_title.replace('(select colors)', '').replace('(select sizes)', '')
        search_title = ' '.join(search_title.split()).strip()
        
        # Limit search to first 100 chars
        if len(search_title) > 100:
            search_title = search_title[:100]
        
        # Search Slickdeals deals forum
        search_url = f'https://slickdeals.net/newsearch.php?searchin=first&forumchoice%5B%5D=9&q={quote(search_title)}'
        
        req = Request(search_url, headers={'User-Agent': USER_AGENT})
        with urlopen(req, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # Look for deal links in the search results
        # Pattern: /f/XXXXX-deal-title or full URLs
        deal_pattern = r'href="(https://slickdeals\.net/f/\d+[^"]*)"'
        matches = re.findall(deal_pattern, html)
        
        if matches:
            # Return the first matching deal URL (cleaned)
            url = matches[0]
            # Remove any trailing fragments or extra params
            if '#' in url:
                url = url.split('#')[0]
            return url
        
        # Also try relative pattern
        relative_pattern = r'href="(/f/\d+[^"]*)"'
        rel_matches = re.findall(relative_pattern, html)
        
        if rel_matches:
            return 'https://slickdeals.net' + rel_matches[0].split('#')[0]
        
        return None
    except KeyboardInterrupt:
        raise  # Re-raise to allow clean exit
    except Exception as e:
        # Silently skip on errors
        return None


def fix_deals():
    """Fix all deals with search URLs by replacing them with actual deal URLs."""
    print('Loading deals from JSON...')
    
    if not DEALS_FILE.exists():
        print(f'Error: {DEALS_FILE} not found')
        sys.exit(1)
    
    with open(DEALS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    deals = data.get('deals', [])
    print(f'Loaded {len(deals)} deals')
    
    # Find deals with search URLs
    search_url_deals = [d for d in deals if is_search_url(d.get('link', ''))]
    print(f'Found {len(search_url_deals)} deals with search URLs to fix')
    
    if not search_url_deals:
        print('No deals to fix!')
        return
    
    fixed_count = 0
    failed_count = 0
    
    try:
        for i, deal in enumerate(search_url_deals):
            title = deal.get('title', '')
            old_link = deal.get('link', '')
            
            print(f'[{i+1}/{len(search_url_deals)}] Processing: {title[:60]}...')
            
            # Try to find actual deal URL
            actual_url = fetch_actual_deal_url(title)
            
            if actual_url:
                # Update the deal with the actual URL
                deal['link'] = normalize_link(actual_url)
                print(f'  [OK] Fixed: {deal["link"][:70]}...')
                fixed_count += 1
            else:
                print(f'  [SKIP] Could not find deal URL, keeping search URL')
                failed_count += 1
            
            # Be nice to the server - rate limit requests
            time.sleep(0.5)
            
            # Save progress every 50 deals
            if (i + 1) % 50 == 0:
                print(f'\nSaving progress ({i+1} processed)...')
                data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
                with open(DEALS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print('Progress saved.\n')
    except KeyboardInterrupt:
        print(f'\n\nInterrupted! Saving progress...')
        data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
        with open(DEALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f'Progress saved. Fixed {fixed_count} deals so far.')
        sys.exit(0)
    
    # Final save
    print(f'\nSaving final results...')
    data['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
    with open(DEALS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'\n=== Summary ===')
    print(f'Total deals with search URLs: {len(search_url_deals)}')
    print(f'Successfully fixed: {fixed_count}')
    print(f'Could not fix: {failed_count}')
    print(f'\nDone! Updated {DEALS_FILE}')


if __name__ == '__main__':
    fix_deals()
