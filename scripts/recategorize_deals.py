#!/usr/bin/env python3
"""
Recategorize Existing Deals Script
Re-runs the enhanced categorize_item() function on all deals in deals.json
"""
import json
import sys
from pathlib import Path
from datetime import datetime
import importlib.util

# Force fresh import of categorize_item from sync_combined to avoid module caching
def load_categorize_item():
    """Load categorize_item with fresh import to avoid Python module caching"""
    script_path = Path(__file__).parent / 'sync_combined.py'
    spec = importlib.util.spec_from_file_location("sync_combined_fresh", str(script_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.categorize_item

categorize_item = load_categorize_item()

def recategorize_deals():
    """Load deals.json, recategorize all deals, and save back"""
    deals_file = Path(__file__).parent.parent / 'data' / 'deals.json'
    
    if not deals_file.exists():
        print(f"Error: {deals_file} not found")
        return False
    
    # Load existing deals
    print("Loading deals.json...")
    with open(deals_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    deals = data.get('deals', [])
    total = len(deals)
    print(f"Found {total} deals to recategorize")
    
    # Track changes
    changes = 0
    uncategorized_before = sum(1 for d in deals if d.get('mainCategory') == 'Uncategorized')
    
    print("\nRecategorizing...")
    for i, deal in enumerate(deals, 1):
        if i % 500 == 0:
            print(f"  Processed {i}/{total} deals...")
        
        old_main = deal.get('mainCategory', '')
        old_sub = deal.get('subCategory', '')
        
        # Re-run categorization
        new_cat = categorize_item(deal.get('title', ''), deal.get('link', ''))
        
        # Update if changed
        if new_cat['main'] != old_main or new_cat['sub'] != old_sub:
            deal['mainCategory'] = new_cat['main']
            deal['subCategory'] = new_cat['sub']
            changes += 1
    
    uncategorized_after = sum(1 for d in deals if d.get('mainCategory') == 'Uncategorized')
    
    # Update timestamp
    data['lastUpdated'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Save back
    print("\nSaving updated deals.json...")
    with open(deals_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Report results
    print("\n" + "="*60)
    print("RECATEGORIZATION COMPLETE")
    print("="*60)
    print(f"Total deals processed: {total:,}")
    print(f"Deals with category changes: {changes:,}")
    print(f"\nUncategorized deals:")
    print(f"  Before: {uncategorized_before:,} ({uncategorized_before/total*100:.1f}%)")
    print(f"  After:  {uncategorized_after:,} ({uncategorized_after/total*100:.1f}%)")
    print(f"  Fixed:  {uncategorized_before - uncategorized_after:,} deals now categorized")
    print("="*60)
    
    return True

if __name__ == '__main__':
    success = recategorize_deals()
    sys.exit(0 if success else 1)
