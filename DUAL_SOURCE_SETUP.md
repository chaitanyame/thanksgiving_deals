# Dual Data Source Setup - Complete Guide

## Overview

This project now fetches deals from **TWO sources**:

1. **Google Sheets** - Contains 16,000+ historical deals (initial import)
2. **Slickdeals RSS** - Live deals updated every 30 minutes (ongoing sync)

The system merges both sources to provide comprehensive deal coverage.

## How It Works

### Initial Setup (One-Time)
1. **Import from Google Sheets**: Fetches all 16,458 deals from your Google Sheet
2. **Categorizes sheet deals**: Applies keyword-based categorization to match website structure
3. **Saves to `data/deals.json`**: Creates the initial database

### Ongoing Sync (Every 30 Minutes)
1. **Loads existing deals**: Reads all Google Sheet deals from `data/deals.json`
2. **Fetches RSS feed**: Gets latest 25 deals from Slickdeals frontpage
3. **Merges intelligently**: 
   - Keeps all Google Sheet deals
   - Adds new RSS deals
   - Updates existing deals if they appear in RSS
4. **Saves combined data**: Website shows both data sources

## Running Locally with Docker

### First Time Setup (Import Everything)
```bash
docker-compose up --build
```

This runs:
- `import-sheet` service → Imports 16,000+ deals from Google Sheets
- `scraper` service → Adds latest RSS deals
- `web` service → Starts website on http://localhost:8888

### Subsequent Updates (RSS Only)
```bash
docker-compose run --rm scraper
```

This merges new RSS deals with existing Google Sheet data.

### Re-import from Google Sheets
```bash
docker-compose run --rm import-sheet
```

This refreshes the sheet data (useful if sheet is updated).

## Automatic Syncing (Optional)

Enable the scheduler to automatically fetch new RSS deals every 30 minutes:

1. Edit `docker-compose.yml`
2. Uncomment the `scheduler` service section
3. Run: `docker-compose up -d`

The scheduler will continuously merge new RSS deals with the Google Sheet data.

## GitHub Actions Workflows

### 1. Import from Google Sheets (Manual)
File: `.github/workflows/import-sheet.yml`
- Trigger: Manual via "Run workflow" button
- Purpose: Import all deals from Google Sheets
- Use when: Sheet is updated or first-time setup

### 2. Sync Slickdeals Deals (Automated)
File: `.github/workflows/sync-deals.yml`
- Trigger: Every 30 minutes (cron)
- Purpose: Merge new RSS deals with existing sheet data
- Use when: Automatic - runs continuously

## Data Flow Diagram

```
┌─────────────────────┐
│  Google Sheets      │
│  (16,000+ deals)    │
└──────────┬──────────┘
           │ (one-time import)
           ↓
      ┌────────────────┐
      │ deals.json     │◄────┐
      │ (all deals)    │     │
      └────────┬───────┘     │
               │             │ (merge)
               ↓             │
┌──────────────────────┐    │
│  Slickdeals RSS      │────┘
│  (latest 25 deals)   │
└──────────────────────┘
           │
           ↓
┌──────────────────────┐
│  Website             │
│  (shows combined)    │
└──────────────────────┘
```

## Key Files

- `scripts/import_from_sheet.py` - Imports deals from Google Sheets CSV export
- `scripts/sync_combined.py` - Merges RSS deals with existing sheet data
- `scripts/sync_deals.py` - Original RSS-only script (deprecated, use `sync_combined.py`)
- `data/deals.json` - Combined database of all deals
- `docker-compose.yml` - Docker services configuration

## Configuration

### Change Google Sheet
Edit `scripts/import_from_sheet.py`:
```python
SHEET_ID = 'YOUR_SHEET_ID_HERE'
```

### Change RSS Update Frequency
Edit `.github/workflows/sync-deals.yml`:
```yaml
schedule:
  - cron: '*/30 * * * *'  # Every 30 minutes
  # Change to: '0 */1 * * *'  # Every hour
```

Or in `docker-compose.yml` scheduler service:
```yaml
sleep 1800  # 30 minutes in seconds
# Change to: sleep 3600  # 1 hour
```

## Troubleshooting

### No deals showing after import
- Check if `data/deals.json` exists and has data
- Run: `docker-compose logs import-sheet` to see import errors
- Verify Google Sheet is publicly accessible

### Categories not matching
- Google Sheet deals use exact category names from CSV
- RSS deals use keyword-based categorization
- Both approaches work together

### Import is slow
- Google Sheet has 16,000+ rows, import takes ~30 seconds
- This is normal for first-time import
- Subsequent RSS syncs are fast (~2 seconds)

### Duplicate deals
- The merge function uses deal IDs to prevent duplicates
- Sheet deals: `sheet-{index}-{title}`
- RSS deals: `slickdeals-f{deal_number}`
- If a sheet deal appears in RSS, RSS version takes precedence

## Benefits of Dual Data Source

✅ **Comprehensive Coverage**: 16,000+ historical deals + latest live deals
✅ **Always Current**: RSS updates ensure fresh deals appear immediately
✅ **Resilient**: If RSS is down, sheet data remains available
✅ **Flexible**: Can re-import sheet data anytime without losing RSS updates

## Next Steps

1. Run `docker-compose up --build` to import all data
2. Open http://localhost:8888 to see all 16,000+ deals
3. (Optional) Uncomment scheduler service for automatic updates
4. (Optional) Deploy to GitHub Pages with both workflows enabled
