# Category Update Summary

## Changes Made

I've updated the `scripts/sync_deals.py` categorization logic to better match the categories in your CSV/Google Sheets reference:

### New Categories Added:

1. **Babies & Kids**
   - Kids Toys (ATVs, go-karts, hoverboards, toy cars)
   - Baby Products (diapers, formula, cribs, strollers, car seats)

2. **Clothing & Accessories**
   - Changed "Men's Clothing & Accessories" → "Apparel" (matches CSV)
   - Enhanced Shoes subcategory with more keywords

3. **Grocery**
   - **NEW**: Household Goods (paper towels, cleaning supplies, detergent, etc.)
   - Existing snacks/drinks categories remain

4. **Home & Home Improvement**
   - **NEW**: Grills & Grilling Accessories (gas grills, pellet grills, smokers, griddles)
   - **NEW**: Stoves (ovens, ranges, cooktops)
   - **NEW**: Gardening & Outdoor (lawn mowers, patio furniture, garden tools)

5. **Sporting Goods** - Significantly Expanded:
   - **NEW**: Guns, Ammo & Accessories
   - **NEW**: Hunting (trail cameras, camo, optics, hunting boots)
   - **NEW**: Fishing (fish finders, rods, reels, tackle)
   - **NEW**: Golf (golf balls, clubs, putters, drivers)
   - **NEW**: Knives (pocket knives, hunting knives)
   - **NEW**: Sports Equipment (basketball hoops, baseball bats, sports balls)
   - **NEW**: Fitness & Wellness (yoga mats, resistance bands, fitness trackers, pilates)
   - Existing: Exercise Equipment (enhanced with more keywords)
   - Existing: Bicycles & Bike Accessories

## Important Note About Deal Volume

### Current Setup:
- The script fetches deals from **Slickdeals RSS feed** which provides ~25 most recent deals
- This RSS updates continuously, but only shows the latest frontpage deals
- The script runs every 30 minutes to keep the site updated with fresh deals

### Your CSV Reference:
- Shows **16,000+ deals** - this is a comprehensive historical collection
- These deals were accumulated over time, not from a single RSS fetch
- Some deals in the CSV may be expired or from previous days

### Why You're Not Seeing All Categories:
The current live RSS feed may not have deals in every category at this moment. Categories will appear as deals are posted throughout Black Friday. The categorization logic is now in place to properly categorize deals when they appear.

## Testing the Changes

To see the updated categories in action:

```bash
# Run via Docker (recommended)
docker-compose run --rm scraper

# Then check the website
# Categories will populate as deals matching those keywords appear in the RSS feed
```

## To Match Your CSV Exactly

If you want to import all 16,000+ deals from your Google Sheet:

1. Export the Google Sheet as CSV
2. Modify the script to read from CSV instead of RSS feed
3. Parse the CSV and convert to the `deals.json` format

Would you like me to create a script to import deals from your CSV file instead of (or in addition to) the RSS feed?

## Files Modified

- `scripts/sync_deals.py` - Updated `categorize_item()` function (lines 60-300+)
- Added 10+ new category patterns with 100+ new keywords
