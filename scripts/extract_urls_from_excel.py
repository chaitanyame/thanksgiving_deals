#!/usr/bin/env python3
"""
Extract URLs from Excel file and update deals.json with actual URLs.

This script parses the extracted Excel XML files to map deal titles to their
actual URLs, then updates deals.json to replace search URLs with actual ones.
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import unquote, urlparse


def parse_relationships(rels_file: str) -> dict:
    """Parse a .rels XML file to get rId -> URL mappings."""
    rId_to_url = {}
    
    try:
        # Read file content and extract relationships
        with open(rels_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all Relationship elements with Target URLs
        # Pattern: <Relationship Id="rIdXXX" ... Target="URL" TargetMode="External"/>
        pattern = r'<Relationship\s+Id="(rId\d+)"[^>]*Type="[^"]*hyperlink"[^>]*Target="([^"]+)"'
        matches = re.findall(pattern, content)
        
        for rId, url in matches:
            # Decode HTML entities
            url = url.replace('&amp;', '&')
            rId_to_url[rId] = url
    
    except Exception as e:
        print(f"Error parsing {rels_file}: {e}")
    
    return rId_to_url


def parse_shared_strings(shared_strings_file: str) -> list:
    """Parse sharedStrings.xml to get string values by index."""
    strings = []
    
    try:
        with open(shared_strings_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse each <si> element (string item)
        # Each <si> can contain one or more <t> elements
        si_pattern = r'<si>(.*?)</si>'
        si_matches = re.findall(si_pattern, content, re.DOTALL)
        
        for si_content in si_matches:
            # Extract all text from <t> elements within this <si>
            t_pattern = r'<t[^>]*>([^<]*)</t>'
            t_matches = re.findall(t_pattern, si_content)
            
            # Combine all text from the <t> elements
            full_text = ''.join(t_matches).strip()
            strings.append(full_text)
        
        print(f"  Sample strings: {strings[:5] if strings else 'none'}")
    
    except Exception as e:
        print(f"Error parsing shared strings: {e}")
    
    return strings


def parse_worksheet(sheet_file: str, rels_file: str, shared_strings: list) -> dict:
    """Parse a worksheet to get cell values and hyperlinks."""
    cell_values = {}
    cell_hyperlinks = {}
    
    try:
        with open(sheet_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse relationships to get URLs
        rId_to_url = parse_relationships(rels_file)
        
        # Find cell values - pattern: <c r="A1" ...><v>value</v></c>
        # If t="s", value is an index into shared strings
        cell_pattern = r'<c\s+r="([A-Z]+\d+)"[^>]*(?:t="s")?[^>]*>(?:<[^v][^>]*>)*<v>(\d+)</v>'
        for match in re.finditer(cell_pattern, content):
            cell_ref = match.group(1)
            value_idx = int(match.group(2))
            
            # Check if this is a shared string reference
            if 't="s"' in match.group(0) and value_idx < len(shared_strings):
                cell_values[cell_ref] = shared_strings[value_idx]
            else:
                cell_values[cell_ref] = str(value_idx)
        
        # Find hyperlinks - pattern: <hyperlink r:id="rIdXXX" ref="A1"/>
        hyperlink_pattern = r'<hyperlink\s+r:id="(rId\d+)"\s+ref="([A-Z]+\d+)"'
        for match in re.finditer(hyperlink_pattern, content):
            rId = match.group(1)
            cell_ref = match.group(2)
            
            if rId in rId_to_url:
                cell_hyperlinks[cell_ref] = rId_to_url[rId]
        
        # Also check alternate order
        hyperlink_pattern2 = r'<hyperlink\s+[^>]*ref="([A-Z]+\d+)"[^>]*r:id="(rId\d+)"'
        for match in re.finditer(hyperlink_pattern2, content):
            cell_ref = match.group(1)
            rId = match.group(2)
            
            if rId in rId_to_url:
                cell_hyperlinks[cell_ref] = rId_to_url[rId]
    
    except Exception as e:
        print(f"Error parsing worksheet: {e}")
    
    return cell_values, cell_hyperlinks


def extract_deal_urls(extract_dir: str) -> dict:
    """Extract title-to-URL mappings from the extracted Excel directory."""
    title_to_url = {}
    
    shared_strings_file = os.path.join(extract_dir, 'xl', 'sharedStrings.xml')
    shared_strings = parse_shared_strings(shared_strings_file) if os.path.exists(shared_strings_file) else []
    
    print(f"Loaded {len(shared_strings)} shared strings")
    
    # Process each worksheet
    worksheets_dir = os.path.join(extract_dir, 'xl', 'worksheets')
    rels_dir = os.path.join(worksheets_dir, '_rels')
    
    for sheet_file in sorted(Path(worksheets_dir).glob('sheet*.xml')):
        sheet_name = sheet_file.stem
        rels_file = os.path.join(rels_dir, f'{sheet_name}.xml.rels')
        
        if not os.path.exists(rels_file):
            print(f"No rels file for {sheet_name}, skipping")
            continue
        
        print(f"Processing {sheet_name}...")
        
        # Get URLs directly from the rels file
        rId_to_url = parse_relationships(rels_file)
        print(f"  Found {len(rId_to_url)} hyperlink relationships")
        
        # Read the sheet to find which cells have hyperlinks
        with open(sheet_file, 'r', encoding='utf-8') as f:
            sheet_content = f.read()
        
        # Parse hyperlinks with both attribute orders
        hyperlink_pattern = r'<hyperlink\s+[^>]*r:id="(r?Id\d+)"[^>]*ref="([A-Z]+)(\d+)"'
        hyperlink_pattern2 = r'<hyperlink\s+[^>]*ref="([A-Z]+)(\d+)"[^>]*r:id="(r?Id\d+)"'
        
        cell_hyperlinks = {}
        for match in re.finditer(hyperlink_pattern, sheet_content):
            rId = match.group(1)
            col = match.group(2)
            row = int(match.group(3))
            cell_ref = f"{col}{row}"
            
            if rId in rId_to_url:
                cell_hyperlinks[cell_ref] = rId_to_url[rId]
        
        for match in re.finditer(hyperlink_pattern2, sheet_content):
            col = match.group(1)
            row = int(match.group(2))
            rId = match.group(3)
            cell_ref = f"{col}{row}"
            
            if rId in rId_to_url:
                cell_hyperlinks[cell_ref] = rId_to_url[rId]
        
        print(f"  Mapped {len(cell_hyperlinks)} cell hyperlinks")
        
        # Find cell values with shared strings
        # Pattern: <c r="C5" s="X" t="s"><v>123</v></c>
        cell_pattern = r'<c\s+r="([A-Z]+)(\d+)"[^>]*t="s"[^>]*><v>(\d+)</v></c>'
        
        for match in re.finditer(cell_pattern, sheet_content):
            col = match.group(1)
            row = int(match.group(2))
            string_idx = int(match.group(3))
            cell_ref = f"{col}{row}"
            
            # Column C appears to contain the deal title based on the hyperlinks
            if col == 'C' and cell_ref in cell_hyperlinks:
                if string_idx < len(shared_strings):
                    title = shared_strings[string_idx]
                    url = cell_hyperlinks[cell_ref]
                    
                    # Only include slickdeals URLs with /f/ pattern
                    if 'slickdeals.net/f/' in url or 'slickdeals.net?sdtrk=bfsheet&u2=' in url:
                        title_to_url[title] = url
    
    return title_to_url


def normalize_title(title: str) -> str:
    """Normalize a title for matching."""
    # Remove extra whitespace and lowercase
    title = re.sub(r'\s+', ' ', title.strip().lower())
    return title


def update_deals_json(deals_file: str, title_to_url: dict) -> tuple:
    """Update deals.json with actual URLs."""
    with open(deals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create a normalized title lookup
    normalized_lookup = {}
    for title, url in title_to_url.items():
        normalized_lookup[normalize_title(title)] = url
    
    updated = 0
    for deal in data.get('deals', []):
        current_link = deal.get('link', '')
        
        # Skip if already has an actual URL
        if '/f/' in current_link and 'newsearch' not in current_link:
            continue
        
        # Try to find a matching URL by title
        deal_title = deal.get('title', '')
        normalized_deal_title = normalize_title(deal_title)
        
        if normalized_deal_title in normalized_lookup:
            new_url = normalized_lookup[normalized_deal_title]
            deal['link'] = new_url
            updated += 1
    
    # Save updated data
    with open(deals_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    return updated, len(data.get('deals', []))


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    
    extract_dir = os.path.join(project_dir, 'temp_excel')
    deals_file = os.path.join(project_dir, 'data', 'deals.json')
    
    print(f"Extract dir: {extract_dir}")
    print(f"Extract dir exists: {os.path.exists(extract_dir)}")
    
    print("Extracting URLs from Excel XML files...")
    title_to_url = extract_deal_urls(extract_dir)
    print(f"\nExtracted {len(title_to_url)} title-to-URL mappings")
    
    if title_to_url:
        print(f"\nUpdating {deals_file}...")
        updated, total = update_deals_json(deals_file, title_to_url)
        print(f"Updated {updated} of {total} deals")
    else:
        print("\nNo URLs extracted. Check the Excel structure.")


if __name__ == '__main__':
    main()
