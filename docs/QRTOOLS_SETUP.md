# Qrtools Integration Setup

## Environment Variables

Add the following to your `.env` file:

```bash
# Qrtools API Configuration
QRTOOLS_API_URL=http://localhost:3000/api
QRTOOLS_API_PORT=3000

# Browser Profile Path (for reference)
BROWSER_PROFILES_PATH=./profiles
```

## Setup Steps

1. **Copy Qrtools Project**:
   - Copy the Qrtools project into the `qrtools/` directory
   - Ensure all Qrtools files are in place

2. **Install Dependencies**:
   ```bash
   cd qrtools
   npm install
   npx playwright install chromium
   ```

3. **Start Qrtools API Server**:
   ```bash
   # From project root
   ./scripts/start_qrtools.sh
   
   # Or manually
   cd qrtools
   npm run api
   ```

4. **Verify Integration**:
   - Qrtools API should be running on `http://localhost:3000/api`
   - Python backend will connect to this URL
   - Browser profiles from `./profiles/` will be reused

## Browser Profile Reuse

The integration uses existing browser profiles:
- Profiles are located at `./profiles/{account_id}/`
- Qrtools will receive `account_id` parameter in API calls
- **✅ Qrtools API (v1.1.0+) supports multi-account:**
  - Account ID can be passed via query params (highest priority), body, or headers (`X-Account-ID` or `account-id`)
  - Session storage: `profile_threads/{accountId}/threads_session.json` (per account)
  - Browser profile: `profiles/{accountId}/` (per account, managed by Python backend)
  - Cache is isolated per account ID
- **✅ Python Backend Integration:**
  - `QrtoolsClient` passes account_id via query params, body, and headers
  - All API endpoints support account_id parameter
  - `login()` method supports account_id for session storage
- Python backend manages browser contexts via `BrowserManager`
- Qrtools uses account-specific browser profiles when `account_id` is provided

## Testing Connection

### Quick Test

Test kết nối cơ bản với Qrtools API:

```bash
# Test connection (no account required)
python scripts/test_qrtools_connection.py

# Test với account ID
python scripts/test_qrtools_connection.py --account-id account_01
```

Script sẽ test:
- Connection status
- Health check endpoint
- Stats endpoint
- Config endpoint
- Feed extraction (nếu có account_id)

### Manual Testing

1. **Test Health Check**:
   ```bash
   curl http://localhost:3000/api/health
   ```

2. **Test Stats**:
   ```bash
   curl http://localhost:3000/api/stats
   ```

3. **Test Config**:
   ```bash
   curl http://localhost:3000/api/config
   ```

4. **Test Feed Extraction** (với account_id):
   ```bash
   curl "http://localhost:3000/api/feed?account_id=account_01&limit=5"
   ```

## Troubleshooting

### Connection Refused

**Error**: `Connection refused` hoặc `Cannot connect to http://localhost:3000/api`

**Solutions**:
1. Kiểm tra Qrtools API server có đang chạy:
   ```bash
   # Check if process is running
   ps aux | grep "api_server.js"
   
   # Check if port 3000 is in use
   lsof -i :3000
   ```

2. Start Qrtools API server:
   ```bash
   cd qrtools
   npm run api
   ```

3. Kiểm tra port có bị conflict không:
   ```bash
   # Kill process using port 3000
   kill $(lsof -t -i:3000)
   
   # Hoặc dùng script helper
   cd qrtools
   npm run kill-port
   ```

### Timeout Errors

**Error**: `Request timeout` hoặc `Read timeout`

**Solutions**:
1. Tăng timeout trong `QrtoolsClient` (default: 120s)
2. Kiểm tra network connectivity
3. Verify Qrtools API server không bị hang

### Invalid Response

**Error**: `Invalid JSON response` hoặc `Unexpected response format`

**Solutions**:
1. Kiểm tra Qrtools API version có match không
2. Verify endpoint paths đúng format
3. Check Qrtools API logs để xem error details

### Account ID Issues

**Error**: `Account ID is required` hoặc `Browser context not found`

**Solutions**:
1. Đảm bảo account_id được truyền vào API calls
2. Verify browser profile tồn tại tại `./profiles/{account_id}/`
3. Check `BrowserContextProvider` hoạt động đúng

## Full Testing Workflow

1. **Start Qrtools API server**:
   ```bash
   cd qrtools
   npm run api
   ```

2. **Test connection**:
   ```bash
   python scripts/test_qrtools_connection.py --account-id account_01
   ```

3. **Start Python backend**:
   ```bash
   python -m uvicorn backend.main:app --reload
   ```

4. **Start frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

5. **Navigate to Feed Explorer page**:
   - Open browser: `http://localhost:5173/feed-explorer`
   - Select account
   - Test feed extraction

6. **Verify integration**:
   - Feed items load successfully
   - Stats display correctly
   - Interactions work (like, comment, etc.)
