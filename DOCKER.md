# Docker Setup for Slickdeals Black Friday Tracker

## Quick Start

### 1. Run the full setup (Import Google Sheets + Start Website):
```bash
docker-compose up --build
```

This will:
1. Import all deals from Google Sheets (~16,000+ deals)
2. Merge with latest RSS feed deals
3. Start an Nginx web server on http://localhost:8888

### 2. Access the website:
Open your browser to: **http://localhost:8888**

## Commands

### Run scraper once and start web server:
```bash
docker-compose up --build
```

### Import Google Sheets data only:
```bash
docker-compose run --rm import-sheet
```

### Sync RSS deals only (merge with existing):
```bash
docker-compose run --rm scraper
```

### Stop all services:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs -f
```

### Rebuild after code changes:
```bash
docker-compose up --build
```

## Automatic Syncing (Optional)

To enable automatic deal syncing every 30 minutes:

1. Edit `docker-compose.yml`
2. Uncomment the `scheduler` service section (lines starting with `#`)
3. Run:
```bash
docker-compose up --build
```

The scheduler will continuously fetch new deals every 30 minutes.

## Troubleshooting

### No deals showing on website
- Check if scraper ran successfully: `docker-compose logs scraper`
- Verify `data/deals.json` exists and has content
- Wait a moment after first run, then refresh the browser

### Port 8080 already in use
Edit `docker-compose.yml` and change `8080:80` to another port like `3000:80`, then access http://localhost:3000

### Scraper fails
- Check logs: `docker-compose logs scraper`
- Test manually: `docker-compose run --rm scraper`
- Ensure internet connection is available for RSS feed access

## Development Workflow

1. Make changes to Python/JS/CSS files
2. For Python changes: `docker-compose up --build scraper`
3. For frontend changes: Just refresh browser (files are mounted as volumes)
4. To test full stack: `docker-compose up --build`

## Architecture

- **import-sheet** service: One-time import from Google Sheets (~16,000+ deals)
- **scraper** service: Merges RSS feed deals with existing sheet data
- **web** service: Nginx serves static HTML/CSS/JS files on port 8888
- **scheduler** service (optional): Runs scraper every 30 minutes to fetch new RSS deals
- Shared volume: `./data` persists deal data between runs

## How It Works

1. **Initial Import**: `import-sheet` fetches all deals from Google Sheets CSV export
2. **Ongoing Sync**: `scraper` fetches new deals from RSS and merges with sheet data
3. **Result**: Website shows all Google Sheets deals + latest RSS deals combined

## Notes

- The `data/deals.json` file persists on your host machine
- Static files (HTML/CSS/JS) are mounted as read-only volumes
- Python scripts are mounted as volumes for easy development
- No database needed - all data in JSON file
