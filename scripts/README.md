# Scripts Directory

This directory contains utility scripts for the Threads Automation Tool.

## Node.js Scripts

### Feed Extractor (`threads_feed_extractor.js`)

Extracts feed data from live Threads feed using Playwright.

**Requirements:**
- Node.js 18+
- Playwright package

**Installation:**
```bash
cd scripts
npm install
npx playwright install chromium
```

**Usage:**
```bash
# Direct usage
node threads_feed_extractor.js --headless true --maxItems 50

# Via npm script
npm run extract-feed -- --headless true --maxItems 50
```

**Arguments:**
- `--headless`: Run browser in headless mode (true/false)
- `--maxItems`: Maximum number of items to extract
- `--min_likes`: Minimum likes filter
- `--username`: Username filter
- `--text_contains`: Text content filter
- `--has_media`: Filter posts with media (true/false)
- `--output_dir`: Output directory (optional)
- `--output_filename`: Output filename (optional)

**Output:**
The script outputs JSON to stdout with the following structure:
```json
{
  "extracted_at": "2024-01-01T00:00:00Z",
  "total_items": 50,
  "filtered_items_count": 25,
  "items": [...]
}
```

## Python Scripts

See individual script directories for documentation:
- `cli/` - CLI tools (Git, Jobs, Testing)
- `analysis/` - Analysis scripts
- `migration/` - Database migration scripts
- `test/` - Test scripts
