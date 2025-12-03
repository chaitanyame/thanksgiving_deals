# Slickdeals Black Friday Deals Tracker

[![GitHub Actions](https://github.com/chaitanyame/thanksgiving_deals/actions/workflows/sync-deals.yml/badge.svg)](https://github.com/chaitanyame/thanksgiving_deals/actions)
[![GitHub Pages](https://img.shields.io/badge/demo-live-brightgreen)](https://chaitanyame.github.io/thanksgiving_deals/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/chaitanyame/thanksgiving_deals/pulls)

A public, open-source website that automatically tracks and displays the latest Black Friday deals from Slickdeals frontpage and curated Google Sheets data, updated every 45 minutes.

🔗 **Live Site:** [https://chaitanyame.github.io/thanksgiving_deals/](https://chaitanyame.github.io/thanksgiving_deals/)

## Overview

This open-source project provides a free, serverless deal tracking website that anyone can fork, customize, and deploy. It aggregates deals from Slickdeals RSS feeds and optional Google Sheets data into a searchable, filterable interface.

### How It Works

1. **GitHub Actions** runs every 45 minutes and:
   - Fetches the latest deals from Slickdeals RSS feed
   - Imports curated deals from Google Sheets (via CSV export)
   - Merges both sources, deduplicating by deal ID
   - Categorizes each deal using intelligent keyword matching
   - Extracts pricing and store information
   - Saves all deals to `data/deals.json`

2. **GitHub Pages** hosts a static website that:
   - Loads deals from the JSON file
   - Displays them in a clean, responsive table
   - Allows filtering by category and searching by product name
   - Provides sorting options (by date, price)

### Key Features

- ✅ **Auto-updating**: Fresh deals every 45 minutes
- ✅ **No server needed**: Runs on GitHub Actions + GitHub Pages (free)
- ✅ **Dual data sources**: Combines RSS feed + Google Sheets for comprehensive coverage
- ✅ **Categorized**: 30+ categories with intelligent keyword matching
- ✅ **Searchable**: Filter by main category, sub-category, or search text
- ✅ **Dark/Light mode**: Toggle between themes with persistent preference
- ✅ **Mobile-friendly**: Responsive card-based design on mobile devices
- ✅ **Savings badges**: Shows percentage off for deals with original prices
- ✅ **100% Open Source**: Fork, customize, and deploy your own version

## Project Structure

```
blackfriday/
├── .github/
│   ├── workflows/
│   │   └── sync-deals.yml          # GitHub Actions workflow
│   └── copilot-instructions.md     # AI coding assistant guide
├── scripts/
│   ├── sync_combined.py            # Main Python scraper (RSS + Sheets)
│   ├── import_from_sheet.py        # Google Sheets import utility
│   ├── recategorize_deals.py       # Deal re-categorization utility
│   ├── fix_search_urls.py          # URL fixing utility
│   ├── extract_urls_from_excel.py  # Excel URL extraction utility
│   └── requirements.txt            # Python dependencies
├── css/
│   └── styles.css                  # Website styling
├── js/
│   └── app.js                      # Client-side logic
├── data/
│   └── deals.json                  # Generated deal data
├── index.html                      # Main webpage
├── docker-compose.yml              # Docker local dev setup
├── Dockerfile                      # Docker container config
├── DOCKER.md                       # Docker setup guide
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## Setup Instructions

### Prerequisites

- Python 3.7+ (for running scraper locally)
- Git and GitHub account
- (Optional) Local development setup

### Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new public repository named `blackfriday-deals`
2. Clone this repository to your local machine:
   ```bash
   git clone https://github.com/YOUR_USERNAME/blackfriday-deals.git
   cd blackfriday-deals
   ```

### Step 2: Push Initial Code

1. Copy all files from this directory to your cloned repository
2. Commit and push:
   ```bash
   git add .
   git commit -m "Initial commit: Black Friday tracker"
   git push -u origin main
   ```

### Step 3: Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Source", select:
   - Branch: `main`
   - Folder: `/ (root)`
4. Click **Save**
5. Wait 1-2 minutes for the site to deploy

Your site will be available at: `https://YOUR_USERNAME.github.io/blackfriday-deals/`

### Step 4: Test the Workflow (Optional)

1. Go to **Actions** tab in your GitHub repository
2. Click **Sync Slickdeals Deals** workflow
3. Click **Run workflow** button
4. Wait for it to complete
5. Check `data/deals.json` to see if deals were fetched

## Local Development

### Running the scraper locally

1. Install dependencies:
   ```bash
   pip install -r scripts/requirements.txt
   ```

2. Run the script:
   ```bash
   python scripts/sync_combined.py
   ```

3. Open `index.html` in your browser to test the website

### Testing without GitHub Pages

You can test locally by:
1. Running a simple HTTP server:
   ```bash
   python -m http.server 8000
   ```
2. Opening `http://localhost:8000` in your browser

## Data Format

The `data/deals.json` file contains:

```json
{
  "lastUpdated": "2024-11-27T10:30:00Z",
  "deals": [
    {
      "id": "slickdeals-f16123456",
      "title": "Bose QuietComfort Headphones $199",
      "link": "https://slickdeals.net/f/16123456?sdtrk=bfsheet",
      "mainCategory": "Electronics",
      "subCategory": "Headphones, Headsets & Earbuds",
      "salePrice": "$199",
      "originalPrice": "",
      "store": "Amazon",
      "pubDate": "2024-11-27T09:30:00Z"
    }
  ]
}
```

## Categories

The scraper supports 30+ categories including:

- Video Games (Consoles, Memberships, PC Games, etc.)
- Computers (GPUs, SSDs, Memory, Laptops, Monitors, etc.)
- Electronics (TVs, Speakers, Headphones, Smart Watches, etc.)
- Grocery (Snacks, Drinks, Breakfast, Pasta, etc.)
- Home & Home Improvement (Mattresses, Appliances, Furniture, Tools, etc.)
- Clothing & Accessories (Clothing, Shoes, Watches, Jewelry, etc.)
- Health & Beauty (Vitamins, Protein Powder, Skincare, etc.)
- Sporting Goods (Bikes, Exercise Equipment, etc.)
- Autos (Motor Oil, Car Care, EV Chargers, etc.)
- Travel & Vacations (Hotels, Flights, Car Rentals, etc.)
- Restaurants (Pizza, Fast Food, Delivery)
- And more...

## Customization

### Change Update Frequency

Edit `.github/workflows/sync-deals.yml` and modify the cron schedule:

```yaml
schedule:
  - cron: '0 */6 * * *'  # Every 6 hours
```

See [cron syntax](https://crontab.guru) for more options.

### Add More Categories

Edit `scripts/sync_combined.py` and add more keyword rules in the `categorize_item()` function.

### Customize Styling

Edit `css/styles.css` to change colors, fonts, and layout.

## Troubleshooting

### Deals not updating
- Check the **Actions** tab to see if the workflow ran successfully
- Look for error messages in the workflow logs
- Ensure `data/deals.json` exists and has valid JSON format

### Website shows "No deals found"
- Wait for the first workflow run to complete (usually takes 1-2 minutes)
- Manually trigger the workflow from the Actions tab
- Check that the JSON file was created: `data/deals.json`

### GitHub Pages not deploying
- Ensure you selected the correct source in Settings → Pages
- Try clearing browser cache or waiting a few minutes
- Check that `index.html` exists in the root directory

## Contributing

We welcome contributions from the community! Here's how you can help:

### Ways to Contribute

- 🐛 **Report bugs**: Open an issue describing the problem
- 💡 **Suggest features**: Share ideas for improvements
- 🔧 **Submit PRs**: Fix bugs or add new features
- 📝 **Improve docs**: Help make documentation clearer
- 🏷️ **Add categories**: Improve deal categorization logic

### Development Workflow

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Make changes** and test locally
5. **Commit** with clear messages: `git commit -m "Add: description of change"`
6. **Push** to your fork: `git push origin feature/your-feature-name`
7. **Open a Pull Request** against `main`

### Code Style

- Python: Follow PEP 8 guidelines
- JavaScript: Use ES6+ syntax, no external dependencies
- CSS: Use CSS custom properties for theming
- Commits: Use conventional commit messages (Add:, Fix:, Update:, etc.)

### Testing Your Changes

```bash
# Test the scraper
python scripts/sync_combined.py

# Test the website locally
python -m http.server 8000
# Open http://localhost:8000
```

## License

This project is open source and available under the [MIT License](LICENSE).

## Disclaimer

This project is not affiliated with Slickdeals. The `&sdtrk=bfsheet` parameter is used to track traffic from this site within Slickdeals' system.

## Support

For issues or questions:
1. Check existing [GitHub Issues](https://github.com/chaitanyame/thanksgiving_deals/issues)
2. Create a new issue with details about the problem
3. Include steps to reproduce if applicable

## Acknowledgments

- Deal data sourced from [Slickdeals](https://slickdeals.net) RSS feeds
- Hosted on [GitHub Pages](https://pages.github.com)
- Automated with [GitHub Actions](https://github.com/features/actions)

## Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

---

**Happy deal hunting!** 🎉

*Made with ❤️ by the open source community*
