# Hyperlink Extraction Limitation

## Problem
Google Sheets hyperlinks (clickable links in cells) are **NOT preserved** when exporting to CSV, TSV, or HTML formats. Only the visible text is exported.

## Current Solution
The import script generates Slickdeals search URLs based on the product name:
```
https://slickdeals.net/newsearch.php?q=PRODUCT_NAME&sdtrk=bfsheet
```

For example:
- **Product:** "Men's Alpine Action™ II Jacket"
- **Link:** `https://slickdeals.net/newsearch.php?q=Men%27s%20Alpine%20Action%E2%84%A2%20II%20Jacket&sdtrk=bfsheet`

This works well because it searches Slickdeals for the specific product.

## Better Solutions

### Option 1: Add URL Column in Google Sheets (RECOMMENDED)
1. Add a new column called "Link" or "URL" in your Google Sheet
2. Paste the actual Slickdeals URLs as plain text (not hyperlinks)
3. The import script will use these URLs directly

**Example Sheet Structure:**
```
Main Category | Sub Category | Item / Product | Link | Original Price | Sale Price | ...
Electronics   | Laptops      | Dell XPS 13    | https://slickdeals.net/f/17123456 | $999 | $799 | ...
```

### Option 2: Use Google Sheets API v4
Requires authentication but can extract actual hyperlinks from cells.

**Steps:**
1. Enable Google Sheets API in Google Cloud Console
2. Create service account credentials
3. Share the spreadsheet with the service account email
4. Update import script to use `google-api-python-client`

**Example code:**
```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
credentials = service_account.Credentials.from_service_account_file(
    'credentials.json', scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)

# Get cell data with hyperlinks
result = service.spreadsheets().get(
    spreadsheetId=SHEET_ID,
    ranges=['Sheet1!C:C'],  # Column C (Item/Product)
    includeGridData=True
).execute()

# Extract hyperlink from cell
for row in result['sheets'][0]['data'][0]['rowData']:
    cell = row['values'][2]  # Column C
    if 'hyperlink' in cell:
        url = cell['hyperlink']
```

### Option 3: Keep Current Search URLs
The current implementation works reasonably well because:
- ✅ Searches Slickdeals for exact product name
- ✅ Usually finds the right deal in top results
- ✅ No authentication required
- ✅ No manual URL entry needed
- ⚠️ May show multiple results instead of exact deal

## Implementation Status

**Current:** Using search URLs (Option 3)
- File: `scripts/import_from_sheet_html.py`
- Cleans product titles (removes prices, shipping info)
- Generates search URLs automatically

**To switch to Option 1** (URL column):
1. Add "Link" or "URL" column to your Google Sheet
2. The script already checks for these columns
3. Run `docker-compose run --rm import-sheet`

**To implement Option 2** (Sheets API):
1. Add `google-api-python-client` to `requirements.txt`
2. Create new script `import_from_sheets_api.py`
3. Add credentials file to project
4. Update `docker-compose.yml` to mount credentials

## Testing

Test a search URL:
```bash
# This should find the Columbia Alpine Action II Jacket on Slickdeals
open "https://slickdeals.net/newsearch.php?q=Men%27s%20Alpine%20Action%20II%20Jacket&sdtrk=bfsheet"
```

## Recommendation

For best results: **Add a "Link" column** to your Google Sheet with actual Slickdeals URLs as plain text. This is the simplest solution that doesn't require authentication.
