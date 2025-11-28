#!/usr/bin/env python3
"""
Google Sheets Import Script
Fetches all deals from Google Sheets and populates data/deals.json
"""

import json
import csv
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote

# Google Sheets CSV export URL
SHEET_ID = '1AuBRXBOVzUCiH2sOv3sLOAq-6243gJc3gF0aACKgNlo'
SHEET_CSV_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

DATA_DIR = Path(__file__).parent.parent / 'data'
DEALS_FILE = DATA_DIR / 'deals.json'


def normalize_link(link):
    """
    Normalize a link to include sdtrk=bfsheet.
    """
    if not link:
        return ''
    
    link = str(link).strip()
    if not link:
        return ''
    
    if 'sdtrk=bfsheet' in link:
        return link
    
    if '?' in link:
        return link + '&sdtrk=bfsheet'
    else:
        return link + '?sdtrk=bfsheet'


def generate_deal_id(index, title):
    """
    Generate a unique deal ID from index and title.
    """
    # Use first few words of title for uniqueness
    words = ''.join(c for c in title.lower() if c.isalnum() or c.isspace())
    words = '-'.join(words.split()[:5])
    return f'sheet-{index}-{words}'[:100]  # Limit length


def import_from_sheet():
    """
    Import deals from Google Sheets CSV export.
    """
    print(f'Fetching deals from Google Sheets...')
    
    try:
        # Fetch CSV data
        with urlopen(SHEET_CSV_URL) as response:
            csv_data = response.read().decode('utf-8')
        
        # Parse CSV - skip first 3 header rows
        lines = csv_data.splitlines()
        # Find the actual header row (contains "Main Category")
        header_line = None
        for i, line in enumerate(lines):
            if 'Main Category' in line and 'Item / Product' in line:
                header_line = i
                break
        
        if header_line is None:
            print('Could not find header row in CSV')
            return
        
        # Parse from header line onwards
        csv_reader = csv.DictReader(lines[header_line:])
        deals = []
        
        for index, row in enumerate(csv_reader, start=1):
            # Skip header rows or empty rows
            title = row.get('Item / Product', '').strip()
            if not title or title.startswith('See all') or not row.get('Main Category'):
                continue
            
            # Extract data from CSV
            main_category = row.get('Main Category', 'Uncategorized').strip()
            sub_category = row.get('Sub Category', '').strip()
            sale_price = row.get('Sale Price', '').strip()
            original_price = row.get('Original Price', '').strip()
            store = row.get('Store', '').strip()
            sale_period = row.get('Sale Period', '').strip()
            notes = row.get('Notes', '').strip()
            
            # Get link from CSV if available, otherwise use title or placeholder
            link = row.get('Link', '').strip() or row.get('URL', '').strip()
            if not link:
                # Clean title for search: remove price info and extra text
                # Remove anything after $ sign, + sign, or "from" keyword
                search_title = title
                for separator in [' $', ' from ', ' +', ' -', ' @']:
                    if separator in search_title:
                        search_title = search_title.split(separator)[0]
                
                # Remove common deal phrases
                search_title = search_title.replace('(various colors)', '').replace('(various sizes)', '')
                search_title = search_title.replace('(select colors)', '').replace('(select sizes)', '')
                search_title = ' '.join(search_title.split()).strip()
                
                # Use the cleaned title as a search query on Slickdeals
                link = f'https://slickdeals.net/newsearch.php?searchin=first&forumchoice%5B%5D=9&q={quote(search_title)}&sdtrk=bfsheet'
            else:
                # Normalize the link to include tracking parameter
                link = normalize_link(link)
            
            deal = {
                'id': generate_deal_id(index, title),
                'title': title,
                'link': link,
                'mainCategory': main_category,
                'subCategory': sub_category,
                'salePrice': sale_price,
                'originalPrice': original_price,
                'store': store,
                'salePeriod': sale_period,
                'notes': notes,
                'pubDate': datetime.utcnow().isoformat() + 'Z'
            }
            deals.append(deal)
        
        print(f'Imported {len(deals)} deals from Google Sheets')
        
        # Save to file
        data = {
            'lastUpdated': datetime.utcnow().isoformat() + 'Z',
            'deals': deals
        }
        
        DEALS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DEALS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f'Successfully saved {len(deals)} deals to {DEALS_FILE}')
        
    except Exception as e:
        print(f'Error importing from Google Sheets: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    import_from_sheet()
