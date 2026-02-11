# Qrtools Setup Instructions

This directory should contain the Qrtools (Threads Feed Extraction Tools) project.

## Setup Steps

1. **Copy Qrtools project** into this directory:
   ```bash
   # If you have Qrtools in another location
   cp -r /path/to/qrtools/* ./qrtools/
   ```

2. **Install dependencies**:
   ```bash
   cd qrtools
   npm install
   npx playwright install chromium
   ```

3. **Configure Qrtools**:
   - Edit `qrtools/src/config.js` to match your setup
   - Ensure API server port is 3000 (or update `.env` accordingly)

4. **Start Qrtools API Server**:
   ```bash
   # From project root
   ./scripts/start_qrtools.sh
   
   # Or manually
   cd qrtools
   npm run api
   ```

## Integration Notes

- Qrtools API server should run on `http://localhost:3000/api`
- Python backend will call Qrtools API via HTTP
- Browser profiles from `./profiles/` will be reused by Qrtools
- Account ID will be passed to Qrtools to identify which profile to use

## Environment Variables

Add to `.env`:
```bash
QRTOOLS_API_URL=http://localhost:3000/api
QRTOOLS_API_PORT=3000
BROWSER_PROFILES_PATH=./profiles
```

## Browser Context Integration

Qrtools will receive `account_id` parameter in API calls and should:
1. Request browser context from Python backend (via internal API)
2. Use existing Playwright context from BrowserManager
3. Reuse browser profiles from `./profiles/{account_id}`

See plan document for detailed integration approach.
