#!/usr/bin/env python3
"""
Google Sheets Import Script with Hyperlink Extraction
Fetches deals from Google Sheets HTML export to preserve hyperlinks
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import quote
from html.parser import HTMLParser

# Google Sheets URLs
SHEET_ID = '1AuBRXBOVzUCiH2sOv3sLOAq-6243gJc3gF0aACKgNlo'
SHEET_HTML_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:html'

DATA_DIR = Path(__file__).parent.parent / 'data'
DEALS_FILE = DATA_DIR / 'deals.json'


class SheetHTMLParser(HTMLParser):
    """Parse Google Sheets HTML to extract data with hyperlinks"""
    
    def __init__(self):
        super().__init__()
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.in_link = False
        self.current_row = []
        self.current_cell_text = []
        self.current_link = None
        self.rows = []
        self.col_index = 0
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == 'table':
            self.in_table = True
        elif tag == 'tr' and self.in_table:
            self.in_row = True
            self.current_row = []
            self.col_index = 0
        elif tag == 'td' and self.in_row:
            self.in_cell = True
            self.current_cell_text = []
            self.current_link = None
        elif tag == 'a' and self.in_cell:
            self.in_link = True
            self.current_link = attrs_dict.get('href', '')
    
    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr':
            if self.current_row:
                self.rows.append(self.current_row)
            self.in_row = False
        elif tag == 'td':
            cell_text = ''.join(self.current_cell_text).strip()
            # Store as tuple: (text, link)
            self.current_row.append((cell_text, self.current_link))
            self.in_cell = False
            self.col_index += 1
        elif tag == 'a':
            self.in_link = False
    
    def handle_data(self, data):
        if self.in_cell:
            self.current_cell_text.append(data)


def normalize_link(link):
    """Normalize a link to include sdtrk=bfsheet."""
    if not link:
        return ''
    
    link = str(link).strip()
    if not link or link.startswith('#'):
        return ''
    
    if 'sdtrk=bfsheet' in link:
        return link
    
    if '?' in link:
        return link + '&sdtrk=bfsheet'
    else:
        return link + '?sdtrk=bfsheet'


def generate_deal_id(index, title):
    """Generate a unique deal ID from index and title."""
    words = ''.join(c for c in title.lower() if c.isalnum() or c.isspace())
    words = '-'.join(words.split()[:5])
    return f'sheet-{index}-{words}'[:100]


def clean_title_for_search(title):
    """Clean title for search: remove price info and extra text"""
    search_title = title
    
    # Remove anything after $ sign, + sign, or "from" keyword
    for separator in [' $', ' from ', ' +', ' -', ' @']:
        if separator in search_title:
            search_title = search_title.split(separator)[0]
    
    # Remove common deal phrases
    search_title = search_title.replace('(various colors)', '').replace('(various sizes)', '')
    search_title = search_title.replace('(select colors)', '').replace('(select sizes)', '')
    search_title = ' '.join(search_title.split()).strip()
    
    return search_title


def import_from_sheet():
    """Import deals from Google Sheets HTML export to preserve hyperlinks."""
    print(f'Fetching deals from Google Sheets with hyperlinks...')
    
    try:
        # Fetch HTML data
        with urlopen(SHEET_HTML_URL) as response:
            html_data = response.read().decode('utf-8')
        
        # Parse HTML to extract table data with hyperlinks
        parser = SheetHTMLParser()
        parser.feed(html_data)
        
        if not parser.rows:
            print('No data found in HTML export')
            return
        
        # Find header row
        header_row_index = None
        for i, row in enumerate(parser.rows):
            row_text = [cell[0] for cell in row]
            if any('Main Category' in text for text in row_text) and any('Item' in text or 'Product' in text for text in row_text):
                header_row_index = i
                break
        
        if header_row_index is None:
            print('Could not find header row')
            return
        
        # Get column indices
        header_row = parser.rows[header_row_index]
        headers = [cell[0].strip() for cell in header_row]
        
        col_indices = {}
        for i, header in enumerate(headers):
            if 'Main Category' in header:
                col_indices['main_category'] = i
            elif 'Sub Category' in header:
                col_indices['sub_category'] = i
            elif 'Item' in header or 'Product' in header:
                col_indices['title'] = i
            elif 'Original Price' in header:
                col_indices['original_price'] = i
            elif 'Sale Price' in header:
                col_indices['sale_price'] = i
            elif 'Store' in header:
                col_indices['store'] = i
            elif 'Sale Period' in header:
                col_indices['sale_period'] = i
            elif 'Notes' in header:
                col_indices['notes'] = i
        
        print(f'Found columns: {col_indices}')
        
        # Process data rows
        deals = []
        for row_index in range(header_row_index + 1, len(parser.rows)):
            row = parser.rows[row_index]
            
            if len(row) <= max(col_indices.values()):
                continue
            
            # Get title and link
            title_cell = row[col_indices['title']]
            title = title_cell[0].strip()
            link = title_cell[1]  # Hyperlink from cell
            
            if not title or title.startswith('See all'):
                continue
            
            # Extract other fields
            main_category = row[col_indices['main_category']][0].strip() if 'main_category' in col_indices else 'Uncategorized'
            sub_category = row[col_indices['sub_category']][0].strip() if 'sub_category' in col_indices else ''
            sale_price = row[col_indices['sale_price']][0].strip() if 'sale_price' in col_indices else ''
            original_price = row[col_indices['original_price']][0].strip() if 'original_price' in col_indices else ''
            store = row[col_indices['store']][0].strip() if 'store' in col_indices else ''
            sale_period = row[col_indices['sale_period']][0].strip() if 'sale_period' in col_indices else ''
            notes = row[col_indices['notes']][0].strip() if 'notes' in col_indices else ''
            
            if not main_category:
                continue
            
            # Process link
            if link:
                # Use the actual hyperlink from the sheet
                link = normalize_link(link)
            else:
                # Fallback: create search URL
                search_title = clean_title_for_search(title)
                link = f'https://slickdeals.net/newsearch.php?searchin=first&forumchoice%5B%5D=9&q={quote(search_title)}&sdtrk=bfsheet'
            
            deal = {
                'id': generate_deal_id(len(deals) + 1, title),
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
        
        # Count deals with real links vs search links
        real_links = sum(1 for d in deals if 'slickdeals.net/f/' in d['link'] or 'slickdeals.net/e/' in d['link'])
        search_links = sum(1 for d in deals if 'newsearch.php' in d['link'])
        print(f'Real Slickdeals links: {real_links}, Search links: {search_links}')
        
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
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    import_from_sheet()
