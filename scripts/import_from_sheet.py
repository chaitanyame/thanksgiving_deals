#!/usr/bin/env python3
"""
Google Sheets / Excel Import Script
Imports deals from Excel files (with hyperlinks) or Google Sheets CSV.

For Excel files: Uses XML parsing to extract hyperlinks properly (openpyxl hangs on large files)
For Google Sheets: Falls back to CSV export with search URL fallback
"""

import json
import csv
import re
import sys
import time
import zipfile
import tempfile
import shutil
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote, urljoin
from urllib.error import URLError, HTTPError

# Google Sheets CSV export URL
SHEET_ID = '1AuBRXBOVzUCiH2sOv3sLOAq-6243gJc3gF0aACKgNlo'
SHEET_CSV_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv'

DATA_DIR = Path(__file__).parent.parent / 'data'
DEALS_FILE = DATA_DIR / 'deals.json'

# User agent for web requests
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'


# =============================================================================
# EXCEL XML PARSING FUNCTIONS
# (Used instead of openpyxl which hangs on large files with many hyperlinks)
# =============================================================================

def parse_excel_relationships(rels_file: str) -> dict:
    """Parse a .rels XML file to get rId -> URL mappings for hyperlinks."""
    rId_to_url = {}
    
    try:
        with open(rels_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all Relationship elements with hyperlink type and external Target
        pattern = r'<Relationship\s+Id="(rId\d+)"[^>]*Type="[^"]*hyperlink"[^>]*Target="([^"]+)"'
        matches = re.findall(pattern, content)
        
        for rId, url in matches:
            # Decode HTML entities
            url = url.replace('&amp;', '&')
            rId_to_url[rId] = url
    
    except Exception as e:
        print(f"  Warning: Error parsing rels file: {e}")
    
    return rId_to_url


def parse_excel_shared_strings(shared_strings_file: str) -> list:
    """Parse sharedStrings.xml to get string values by index."""
    strings = []
    
    try:
        with open(shared_strings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse each <si> element (string item)
        si_pattern = r'<si>(.*?)</si>'
        si_matches = re.findall(si_pattern, content, re.DOTALL)
        
        for si_content in si_matches:
            # Extract all text from <t> elements within this <si>
            t_pattern = r'<t[^>]*>([^<]*)</t>'
            t_matches = re.findall(t_pattern, si_content)
            
            # Combine all text from the <t> elements
            full_text = ''.join(t_matches).strip()
            strings.append(full_text)
    
    except Exception as e:
        print(f"  Warning: Error parsing shared strings: {e}")
    
    return strings


def extract_excel_deals(extract_dir: str) -> list:
    """
    Extract deals with hyperlinks from an extracted Excel directory.
    
    Returns a list of dicts with: title, link, mainCategory, subCategory, 
    salePrice, originalPrice, store, salePeriod, notes
    """
    deals = []
    seen_titles = set()  # Track seen titles to avoid duplicates across sheets
    
    # Load shared strings
    shared_strings_file = os.path.join(extract_dir, 'xl', 'sharedStrings.xml')
    shared_strings = []
    if os.path.exists(shared_strings_file):
        shared_strings = parse_excel_shared_strings(shared_strings_file)
        print(f"  Loaded {len(shared_strings)} shared strings")
    
    # Process each worksheet
    worksheets_dir = os.path.join(extract_dir, 'xl', 'worksheets')
    rels_dir = os.path.join(worksheets_dir, '_rels')
    
    for sheet_file in sorted(Path(worksheets_dir).glob('sheet*.xml')):
        sheet_name = sheet_file.stem
        rels_file = os.path.join(rels_dir, f'{sheet_name}.xml.rels')
        
        if not os.path.exists(rels_file):
            continue
        
        print(f"  Processing {sheet_name}...")
        
        # Get hyperlink URLs from rels file
        rId_to_url = parse_excel_relationships(rels_file)
        if not rId_to_url:
            continue
        
        # Read the sheet content
        with open(sheet_file, 'r', encoding='utf-8') as f:
            sheet_content = f.read()
        
        # Map cell references to hyperlink URLs
        cell_hyperlinks = {}
        
        # Pattern 1: <hyperlink r:id="rIdXXX" ref="C5"/>
        hyperlink_pattern = r'<hyperlink\s+[^>]*r:id="(r?Id\d+)"[^>]*ref="([A-Z]+)(\d+)"'
        for match in re.finditer(hyperlink_pattern, sheet_content):
            rId = match.group(1)
            col = match.group(2)
            row = int(match.group(3))
            cell_ref = f"{col}{row}"
            
            if rId in rId_to_url:
                cell_hyperlinks[cell_ref] = rId_to_url[rId]
        
        # Pattern 2: <hyperlink ref="C5" r:id="rIdXXX"/>
        hyperlink_pattern2 = r'<hyperlink\s+[^>]*ref="([A-Z]+)(\d+)"[^>]*r:id="(r?Id\d+)"'
        for match in re.finditer(hyperlink_pattern2, sheet_content):
            col = match.group(1)
            row = int(match.group(2))
            rId = match.group(3)
            cell_ref = f"{col}{row}"
            
            if rId in rId_to_url:
                cell_hyperlinks[cell_ref] = rId_to_url[rId]
        
        # Parse cell values from the sheet
        # Build a mapping of cell_ref -> value
        cell_values = {}
        
        # Pattern: <c r="C5" s="X" t="s"><v>123</v></c> (shared string)
        # or: <c r="C5" s="X"><v>123</v></c> (inline value)
        cell_pattern = r'<c\s+r="([A-Z]+)(\d+)"([^>]*)><v>([^<]*)</v></c>'
        
        for match in re.finditer(cell_pattern, sheet_content):
            col = match.group(1)
            row = int(match.group(2))
            attrs = match.group(3)
            value = match.group(4)
            cell_ref = f"{col}{row}"
            
            # Check if it's a shared string reference
            if 't="s"' in attrs and value.isdigit():
                string_idx = int(value)
                if string_idx < len(shared_strings):
                    cell_values[cell_ref] = shared_strings[string_idx]
            else:
                cell_values[cell_ref] = value
        
        # Extract deals from this sheet
        # Based on the Excel structure:
        # Column A: Main Category, B: Sub Category, C: Item/Product (with hyperlink)
        # D: Sale Price, E: Original Price, F: Store, G: Sale Period, H: Notes
        
        sheet_deals = 0
        
        # Find all rows that have a hyperlink in column C
        for cell_ref, url in cell_hyperlinks.items():
            if not cell_ref.startswith('C'):
                continue
            
            row = int(cell_ref[1:])
            
            # Skip header rows
            if row < 4:
                continue
            
            # Get the title from the same cell
            title = cell_values.get(f'C{row}', '').strip()
            if not title:
                continue
            
            # Skip if we've already seen this title (deduplication across sheets)
            if title in seen_titles:
                continue
            seen_titles.add(title)
            
            # Get other fields
            main_category = cell_values.get(f'A{row}', 'Uncategorized').strip()
            sub_category = cell_values.get(f'B{row}', '').strip()
            sale_price = cell_values.get(f'D{row}', '').strip()
            original_price = cell_values.get(f'E{row}', '').strip()
            store = cell_values.get(f'F{row}', '').strip()
            sale_period = cell_values.get(f'G{row}', '').strip()
            notes = cell_values.get(f'H{row}', '').strip()
            
            # Only include slickdeals URLs
            if 'slickdeals.net' not in url:
                continue
            
            # Normalize the URL with tracking parameter
            link = normalize_link(url)
            
            deal = {
                'title': title,
                'link': link,
                'mainCategory': main_category if main_category else 'Uncategorized',
                'subCategory': sub_category,
                'salePrice': sale_price,
                'originalPrice': original_price,
                'store': store,
                'salePeriod': sale_period,
                'notes': notes,
            }
            deals.append(deal)
            sheet_deals += 1
        
        print(f"    Extracted {sheet_deals} new deals from {sheet_name}")
    
    return deals


def import_from_excel(excel_path: str) -> list:
    """
    Import deals from an Excel file (.xlsx) by extracting and parsing XML.
    
    This avoids using openpyxl which hangs on files with many hyperlinks.
    
    Args:
        excel_path: Path to the .xlsx file
        
    Returns:
        List of deal dictionaries with hyperlinks properly extracted
    """
    print(f"Importing from Excel: {excel_path}")
    
    # Create a temp directory to extract the xlsx
    temp_dir = tempfile.mkdtemp(prefix='excel_import_')
    
    try:
        # Extract the xlsx (it's a zip file)
        print(f"  Extracting Excel to temp directory...")
        with zipfile.ZipFile(excel_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
        
        # Extract deals with hyperlinks
        deals = extract_excel_deals(temp_dir)
        print(f"  Total deals extracted: {len(deals)}")
        
        return deals
        
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def normalize_link(link):
    """
    Normalize a link to include sdtrk=bfsheet tracking parameter.
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


def generate_search_url(title):
    """
    Generate a Slickdeals search URL as a fallback for deals without hyperlinks.
    """
    search_title = title
    for separator in [' $', ' from ', ' +', ' -', ' @']:
        if separator in search_title:
            search_title = search_title.split(separator)[0]
    
    search_title = search_title.replace('(various colors)', '').replace('(various sizes)', '')
    search_title = search_title.replace('(select colors)', '').replace('(select sizes)', '')
    search_title = ' '.join(search_title.split()).strip()
    
    return f'https://slickdeals.net/newsearch.php?searchin=first&forumchoice%5B%5D=9&q={quote(search_title)}&sdtrk=bfsheet'


# =============================================================================
# GOOGLE SHEETS CSV IMPORT (Fallback when Excel not available)
# =============================================================================

def import_from_sheet():
    """
    Import deals from Google Sheets CSV export.
    Note: This is a fallback when Excel file is not available.
    Hyperlinks are not preserved in CSV export, so search URLs are used as fallback.
    """
    print(f'Fetching deals from Google Sheets CSV...')
    print(f'WARNING: CSV export does not include hyperlinks. Use Excel import for actual URLs.')
    
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
            
            # CSV export doesn't include hyperlinks, use search URL as fallback
            link = generate_search_url(title)
            
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
        
        print(f'Imported {len(deals)} deals from Google Sheets (CSV fallback)')
        return deals
        
    except Exception as e:
        print(f'Error importing from Google Sheets: {e}', file=sys.stderr)
        return []


# =============================================================================
# MAIN IMPORT FUNCTION
# =============================================================================

def save_deals(deals: list, output_file: Path = None):
    """Save deals to JSON file."""
    if output_file is None:
        output_file = DEALS_FILE
    
    # Add IDs and pubDate to deals that don't have them
    for index, deal in enumerate(deals, start=1):
        if 'id' not in deal:
            deal['id'] = generate_deal_id(index, deal.get('title', ''))
        if 'pubDate' not in deal:
            deal['pubDate'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    data = {
        'lastUpdated': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        'deals': deals
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f'Successfully saved {len(deals)} deals to {output_file}')


def main():
    """
    Main entry point for importing deals.
    
    Usage:
        python import_from_sheet.py                    # Import from Google Sheets CSV
        python import_from_sheet.py path/to/file.xlsx  # Import from Excel with hyperlinks
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Import deals from Excel (.xlsx) or Google Sheets',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    # Import from Excel file (recommended - preserves hyperlinks):
    python import_from_sheet.py "C:/path/to/deals.xlsx"
    
    # Import from Google Sheets CSV (fallback - uses search URLs):
    python import_from_sheet.py
        '''
    )
    parser.add_argument(
        'excel_file',
        nargs='?',
        help='Path to Excel file (.xlsx). If not provided, imports from Google Sheets CSV.'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=DEALS_FILE,
        help=f'Output JSON file (default: {DEALS_FILE})'
    )
    
    args = parser.parse_args()
    
    if args.excel_file:
        # Import from Excel file with hyperlinks
        excel_path = Path(args.excel_file)
        if not excel_path.exists():
            print(f'Error: File not found: {excel_path}', file=sys.stderr)
            sys.exit(1)
        
        if not excel_path.suffix.lower() == '.xlsx':
            print(f'Error: Expected .xlsx file, got: {excel_path.suffix}', file=sys.stderr)
            sys.exit(1)
        
        deals = import_from_excel(str(excel_path))
    else:
        # Fall back to Google Sheets CSV
        deals = import_from_sheet()
    
    if not deals:
        print('No deals imported!', file=sys.stderr)
        sys.exit(1)
    
    # Count URL types
    direct_urls = sum(1 for d in deals if 'newsearch' not in d.get('link', ''))
    search_urls = sum(1 for d in deals if 'newsearch' in d.get('link', ''))
    
    print(f'\nURL Summary:')
    print(f'  Direct URLs (from hyperlinks): {direct_urls}')
    print(f'  Search URLs (fallback): {search_urls}')
    
    save_deals(deals, args.output)


if __name__ == '__main__':
    main()
