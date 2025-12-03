# Slickdeals Black Friday Deals Tracker - AI Agent Guide

> **Repository**: [github.com/chaitanyame/thanksgiving_deals](https://github.com/chaitanyame/thanksgiving_deals)  
> **License**: MIT  
> **Live Site**: [chaitanyame.github.io/thanksgiving_deals](https://chaitanyame.github.io/thanksgiving_deals/)

## Project Architecture

This is a **serverless static website** that auto-updates deal listings from Slickdeals RSS and Google Sheets:

- **Backend**: Python scraper (`scripts/sync_combined.py`) runs via GitHub Actions every 45 minutes
- **Data Layer**: Single JSON file (`data/deals.json`) stores all deal data
- **Frontend**: Vanilla JS (`js/app.js`) + HTML/CSS, hosted on GitHub Pages
- **No database, no API server** - everything is static file-based

The architecture is intentionally simple: RSS + Sheets → Python → JSON → Static Site. All state persists in `deals.json` which gets committed to the repo.

## Key Components & Data Flow

1. **GitHub Actions** (`.github/workflows/sync-deals.yml`) triggers `sync_combined.py` every 45 minutes
2. **Scraper** (`scripts/sync_combined.py`) fetches RSS + Google Sheets, merges and categorizes deals, writes to `data/deals.json`
3. **Frontend** (`js/app.js`) loads JSON via fetch, renders filterable table
4. **Categorization Logic** in `sync_combined.py::categorize_item()` uses keyword matching for 30+ categories

## Critical Developer Workflows

### Testing the Scraper Locally
```bash
cd scripts
pip install -r requirements.txt
python sync_combined.py
# Check data/deals.json was updated
```

### Running the Website Locally
```bash
# From project root
python -m http.server 8000
# Open http://localhost:8000
```

### Manual Workflow Trigger
Go to GitHub Actions → "Sync Slickdeals Deals" → "Run workflow" to test automation without waiting 45 minutes.

### Debugging Failed Workflows
Check `.github/workflows/sync-deals.yml` logs for Python errors. Common issues:
- RSS feed format changes (check `feedparser` parsing in `fetch_feed()`)
- JSON encoding errors (ensure UTF-8 handling in `main()`)

## Project-Specific Conventions

### Deal Categorization System
- **Primary pattern**: Keyword matching in `categorize_item()` function in `sync_combined.py`
- **Structure**: Returns `{'main': str, 'sub': str}` tuple
- **Adding categories**: Add new `has_any()` checks in `categorize_item()` with clear keyword lists
- **Fallback**: Uncategorized deals get `{'main': 'Uncategorized', 'sub': ''}`

Example pattern:
```python
if has_any(['ps5', 'playstation 5', 'xbox series x']):
    return {'main': 'Video Games', 'sub': 'Video Game Consoles'}
```

### Link Normalization
All Slickdeals links MUST include `sdtrk=bfsheet` tracking parameter via `normalize_link()`. This is non-negotiable for affiliate tracking.

### Price Extraction
Uses regex pattern `\$[\d,]+(?:\.\d{2})?` in `extract_price()`. Handles formats like `$24.99` and `$1,299.00`.

### Data Schema (`deals.json`)
```json
{
  "lastUpdated": "ISO 8601 timestamp with Z suffix",
  "deals": [{
    "id": "slickdeals-f{deal_number}",
    "title": "Full deal title from RSS",
    "link": "Normalized URL with sdtrk parameter",
    "mainCategory": "From categorize_item()",
    "subCategory": "From categorize_item() or empty string",
    "salePrice": "Extracted via regex or empty string",
    "originalPrice": "Always empty string (future feature)",
    "store": "Detected from title (currently only 'Amazon' or empty)",
    "pubDate": "ISO 8601 from RSS feed"
  }]
}
```

## Frontend Patterns

### Filter Dependencies
- Changing `mainCategoryFilter` resets `subCategoryFilter` and repopulates subcategory options
- All filters trigger `applyFiltersAndSort()` which re-renders the table
- Filters work via DOM `<select>` and `<input>` elements, no framework state management

### Sorting Implementation
In-place array sorting on `filteredDeals` (see `sortDeals()` in `app.js`). Price sorting extracts numeric values via regex to handle formatted strings like "$1,299.00".

### Date Formatting
`formatDate()` shows relative times ("2 hours ago") for recent deals, switches to absolute dates for older deals (> 7 days).

## Common Modification Patterns

### Adding a New Category
1. Edit `scripts/sync_combined.py::categorize_item()`
2. Add keyword check using `has_any(['keyword1', 'keyword2'])`
3. Return `{'main': 'Category Name', 'sub': 'Subcategory'}`
4. Test locally with `python scripts/sync_combined.py`
5. Verify frontend dropdown populates correctly

### Changing Update Frequency
Edit `.github/workflows/sync-deals.yml` cron expression:
- Current: `*/45 * * * *` (every 45 minutes)
- Example: `0 */6 * * *` (every 6 hours)

### Adding Store Detection
Edit `detect_store()` in `sync_combined.py`. Currently only detects Amazon via lowercase keyword matching. Add similar patterns for other stores.

## Dependencies & Versions

- **Python**: 3.11+ (specified in workflow)
- **Key Library**: `feedparser==6.0.10` (only dependency)
- **Frontend**: Zero dependencies, vanilla JS (ES6+)
- **Hosting**: GitHub Pages (automatically serves from `main` branch root)

## Testing & Validation

- **No unit tests exist** - test by running scraper and checking `deals.json` output
- **Manual validation**: Check deals appear in browser, filters work, links have `sdtrk=bfsheet`
- **Workflow testing**: Use GitHub Actions manual trigger to test changes before scheduled run

## Important Constraints

1. **No backend server** - all logic must be client-side JS or scraper Python
2. **Single data file** - `deals.json` must remain under GitHub's file size limits (currently ~KB range)
3. **RSS dependency** - if Slickdeals changes RSS format, `fetch_feed()` must be updated
4. **Static hosting** - no server-side rendering, API endpoints, or dynamic routes

## References

- **Main documentation**: `README.md` (setup, features, troubleshooting)
- **Categorization logic**: `scripts/sync_combined.py` `categorize_item()` function
- **Frontend rendering**: `js/app.js` `renderDeals()` function
- **Workflow definition**: `.github/workflows/sync-deals.yml`
