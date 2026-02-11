# Qrtools Account ID Session Loading Fix

> **Version:** 1.1.0+  
> **Last Updated:** 2026-01-31  
> **Status:** ✅ Implemented & Documented

## Tóm tắt

Qrtools API đã hỗ trợ **Multi-Account** với session isolation hoàn toàn. Mỗi account có:
- Session file riêng: `profile_threads/{accountId}/threads_session.json`
- Browser profile riêng: `profiles/{accountId}/`
- Cache riêng biệt

**Tất cả endpoints đều hỗ trợ account_id** qua:
- Query parameter: `?account_id=account_01` (khuyến nghị)
- Request body: `{"account_id": "account_01"}`
- HTTP header: `X-Account-ID: account_01`

**Browser Profile Path (Client-Side Profile):**
- Mặc định, hệ thống không lưu browser profile ở máy chủ để đảm bảo bảo mật
- Browser profile chỉ được tạo khi client chỉ định rõ ràng `profile_path`
- Profile path có thể truyền qua query param, header, hoặc request body

## Quick Start

```bash
# Login với account_id
curl -X POST "http://localhost:3000/api/login?account_id=account_01" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "pass1"}'

# Lấy feed với account_id
curl "http://localhost:3000/api/feed?account_id=account_01&min_likes=100"

# Like post với account_id
curl -X POST "http://localhost:3000/api/post/3817952812169631580/like?account_id=account_01&username=may__lily&shortcode=DT8F9qykxdc"

# Sử dụng profile_path (client-side profile)
curl "http://localhost:3000/api/feed?account_id=account_01&profile_path=/home/user/profiles/account_01"

# Kết hợp account_id và profile_path
curl -X POST "http://localhost:3000/api/login?account_id=account_01" \
  -H "Content-Type: application/json" \
  -H "X-Profile-Path: /home/user/profiles/account_01" \
  -d '{"username": "user1", "password": "pass1"}'
```

## Vấn đề

Qrtools API đang load session từ `output/threads_session.json` cố định, không sử dụng `account_id` để load đúng session/profile.

## Nguyên nhân

Qrtools là Node.js microservice riêng, tự quản lý browser và load session cố định từ:
- `output/threads_session.json` (session file)
- Browser profile mặc định (không phụ thuộc vào account_id)

## Giải pháp

### Option 1: Cấu hình Qrtools để sử dụng account_id (Khuyến nghị)

Cần sửa Qrtools API để:
1. Nhận `account_id` từ query params (đã có)
2. Load session từ `./profiles/{account_id}/` hoặc session file tương ứng
3. Không load từ `output/threads_session.json` cố định

**File cần sửa trong Qrtools:**
- `src/config.js` - Cấu hình sessionStoragePath dựa trên account_id
- `src/interactions/session.js` - Load session từ profile path tương ứng với account_id
- `src/browser/browser-manager.js` - Sử dụng user_data_dir dựa trên account_id

**Ví dụ sửa trong Qrtools:**

```javascript
// src/config.js
const getSessionPath = (accountId) => {
  if (accountId) {
    return `./profiles/${accountId}/threads_session.json`;
  }
  return 'output/threads_session.json'; // Fallback
};

// src/interactions/session.js
async function loadSession(page, accountId = null) {
  const sessionPath = getSessionPath(accountId);
  // Load session from account-specific path
  // ...
}

// src/browser/browser-manager.js
async function launchBrowser(accountId = null) {
  const userDataDir = accountId 
    ? `./profiles/${accountId}` 
    : './profiles/default';
  
  // Launch browser with account-specific profile
  // ...
}
```

### Option 2: Python backend quản lý browser, Qrtools chỉ là proxy

Python backend đã có `BrowserContextProvider` để quản lý browser contexts. Qrtools có thể:
1. Nhận `account_id` từ query params
2. Request browser context từ Python backend (qua WebSocket hoặc HTTP endpoint)
3. Sử dụng browser context được cung cấp thay vì tự tạo

**Cần implement:**
- Python backend endpoint để expose browser context cho Qrtools
- Qrtools client để request browser context từ Python backend

### Option 3: Pass profile path từ Python backend

Python backend có thể pass profile path cho Qrtools:
- `profile_path`: `./profiles/{account_id}/`
- Qrtools sử dụng profile path này để load session và launch browser

## Hiện trạng

**✅ ĐÃ FIX (Version 1.1.0+):**
- ✅ Python backend pass `account_id` đến Qrtools API (đã verify trong logs)
- ✅ Qrtools API đã được update để hỗ trợ multi-account
- ✅ Qrtools API sử dụng `account_id` để load session từ `profile_threads/{accountId}/threads_session.json`
- ✅ Session storage được tách biệt cho từng account
- ✅ Browser profile được sử dụng từ `profiles/{accountId}/` cho mỗi account
- ✅ Tất cả endpoints đều hỗ trợ account_id

**Account ID Extraction (Priority Order):**
1. **Query Parameter**: `?account_id=account_01` (highest priority)
2. **Request Body**: `{"account_id": "account_01"}` (for POST requests)
3. **HTTP Header**: `X-Account-ID: account_01` hoặc `account-id: account_01`
4. **JWT Token**: Nếu `CONFIG.api.accountId.parseJWT = true` và có JWT token
5. **Custom Headers**: Configurable trong `CONFIG.api.accountId.customHeaders`

**Session Storage Paths:**
- **Với account ID**: `profile_threads/{accountId}/threads_session.json`
- **Không có account ID**: `output/threads_session.json` (default fallback)

**Browser Profile Paths:**
- **Server-side (tự động)**: `profiles/{accountId}/` (theo Python backend structure)
- **Client-side (explicit)**: Chỉ được sử dụng khi client chỉ định rõ ràng `profile_path`
- **Security**: Mặc định không lưu browser profile ở máy chủ để đảm bảo bảo mật
- **Require Explicit Path**: `CONFIG.browser.persistentProfile.requireExplicitPath = true` (mặc định)

## Cách sử dụng API với Account ID

### 1. Query Parameter (Khuyến nghị)

**Curl:**
```bash
# Lấy feed với account_id
curl "http://localhost:3000/api/feed?account_id=account_01&min_likes=100"

# Login với account_id
curl -X POST "http://localhost:3000/api/login?account_id=account_01" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "pass1"}'

# Like post với account_id
curl -X POST "http://localhost:3000/api/post/3817952812169631580/like?account_id=account_01&username=may__lily&shortcode=DT8F9qykxdc"
```

**Python:**
```python
import requests

# Lấy feed với account_id
response = requests.get('http://localhost:3000/api/feed', params={
    'account_id': 'account_01',
    'min_likes': 100
})

# Login với account_id
response = requests.post('http://localhost:3000/api/login', 
    params={'account_id': 'account_01'},
    json={'username': 'user1', 'password': 'pass1'}
)

# Like post với account_id
response = requests.post(
    'http://localhost:3000/api/post/3817952812169631580/like',
    params={
        'account_id': 'account_01',
        'username': 'may__lily',
        'shortcode': 'DT8F9qykxdc'
    }
)
```

**JavaScript/Node.js:**
```javascript
// Lấy feed với account_id
const response = await fetch('http://localhost:3000/api/feed?account_id=account_01&min_likes=100');

// Login với account_id
await fetch('http://localhost:3000/api/login?account_id=account_01', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user1',
    password: 'pass1'
  })
});

// Like post với account_id
await fetch('http://localhost:3000/api/post/3817952812169631580/like?account_id=account_01&username=may__lily&shortcode=DT8F9qykxdc', {
  method: 'POST'
});
```

### 2. HTTP Header

**Curl:**
```bash
# Sử dụng X-Account-ID header
curl -H "X-Account-ID: account_01" "http://localhost:3000/api/feed?min_likes=100"

# Hoặc account-id header
curl -H "account-id: account_01" "http://localhost:3000/api/feed"
```

**Python:**
```python
import requests

headers = {'X-Account-ID': 'account_01'}
response = requests.get('http://localhost:3000/api/feed', 
    headers=headers,
    params={'min_likes': 100}
)
```

**JavaScript/Node.js:**
```javascript
const response = await fetch('http://localhost:3000/api/feed?min_likes=100', {
  headers: {
    'X-Account-ID': 'account_01'
  }
});
```

### 3. Request Body (POST requests)

**Curl:**
```bash
curl -X POST "http://localhost:3000/api/feed/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "account_01",
    "min_likes": 100,
    "limit": 50
  }'
```

**Python:**
```python
import requests

response = requests.post('http://localhost:3000/api/feed/refresh', json={
    'account_id': 'account_01',
    'min_likes': 100,
    'limit': 50
})
```

**JavaScript/Node.js:**
```javascript
await fetch('http://localhost:3000/api/feed/refresh', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    account_id: 'account_01',
    min_likes: 100,
    limit: 50
  })
});
```

### 4. Browse & Comment với Account ID

**Curl:**
```bash
curl -X POST "http://localhost:3000/api/feed/browse-and-comment?account_id=account_01" \
  -H "Content-Type: application/json" \
  -d '{
    "filterCriteria": {
      "min_likes": 10,
      "has_media": true
    },
    "maxPostsToComment": 5,
    "randomSelection": true,
    "commentTemplates": ["Nice post! 👍", "Great content!"],
    "maxItems": 50
  }'
```

### 5. Browser Profile Path (Client-Side Profile)

**Lưu ý quan trọng về bảo mật:** Mặc định, hệ thống không lưu browser profile ở máy chủ để đảm bảo bảo mật và quyền riêng tư. Browser profile chỉ được tạo khi client chỉ định rõ ràng `profile_path`.

**Curl:**
```bash
# Sử dụng profile_path qua query parameter
curl "http://localhost:3000/api/feed?profile_path=/home/user/browser_profiles/my_profile&min_likes=100"

# Sử dụng profile_path qua header
curl -H "X-Profile-Path: /home/user/browser_profiles/my_profile" "http://localhost:3000/api/feed"

# Kết hợp account_id và profile_path
curl "http://localhost:3000/api/feed?account_id=account_01&profile_path=/home/user/profiles/account_01"

# Login với profile_path
curl -X POST "http://localhost:3000/api/login?account_id=account_01" \
  -H "Content-Type: application/json" \
  -H "X-Profile-Path: /home/user/profiles/account_01" \
  -d '{"username": "user1", "password": "pass1"}'
```

**Python:**
```python
import requests

# Sử dụng profile_path qua query parameter
response = requests.get('http://localhost:3000/api/feed', params={
    'profile_path': '/home/user/browser_profiles/my_profile',
    'min_likes': 100
})

# Sử dụng profile_path qua header
headers = {'X-Profile-Path': '/home/user/browser_profiles/my_profile'}
response = requests.get('http://localhost:3000/api/feed', headers=headers)

# Kết hợp account_id và profile_path
response = requests.get('http://localhost:3000/api/feed', params={
    'account_id': 'account_01',
    'profile_path': '/home/user/profiles/account_01'
})

# Login với profile_path
response = requests.post('http://localhost:3000/api/login',
    params={'account_id': 'account_01'},
    headers={'X-Profile-Path': '/home/user/profiles/account_01'},
    json={'username': 'user1', 'password': 'pass1'}
)
```

**JavaScript/Node.js:**
```javascript
// Sử dụng profile_path qua query parameter
const response = await fetch('http://localhost:3000/api/feed?profile_path=/home/user/browser_profiles/my_profile&min_likes=100');

// Sử dụng profile_path qua header
const response = await fetch('http://localhost:3000/api/feed', {
  headers: {
    'X-Profile-Path': '/home/user/browser_profiles/my_profile'
  }
});

// Kết hợp account_id và profile_path
const response = await fetch('http://localhost:3000/api/feed?account_id=account_01&profile_path=/home/user/profiles/account_01');

// Login với profile_path
await fetch('http://localhost:3000/api/login?account_id=account_01', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Profile-Path': '/home/user/profiles/account_01'
  },
  body: JSON.stringify({
    username: 'user1',
    password: 'pass1'
  })
});
```

**Lưu ý về Profile Path:**
- Profile path phải là absolute path hoặc relative path hợp lệ
- Path không được chứa `..` hoặc `//` để tránh path traversal attacks
- Profile path được validate trước khi sử dụng
- Nếu không có `profile_path`, hệ thống sẽ sử dụng temporary browser context (không lưu profile)

**Python:**
```python
import requests

response = requests.post(
    'http://localhost:3000/api/feed/browse-and-comment',
    params={'account_id': 'account_01'},
    json={
        'filterCriteria': {
            'min_likes': 10,
            'has_media': True
        },
        'maxPostsToComment': 5,
        'randomSelection': True,
        'commentTemplates': ['Nice post! 👍', 'Great content!'],
        'maxItems': 50
    }
)
```

## Python Backend Integration

**✅ ĐÃ UPDATE:**
- `QrtoolsClient` đã được update để hỗ trợ account_id qua:
  - Query parameters (highest priority)
  - Request body (for POST requests)
  - HTTP headers (`X-Account-ID` và `account-id`)
- Tất cả API endpoints đều pass account_id đúng cách
- `login()` method đã được update để hỗ trợ account_id

**Ví dụ sử dụng QrtoolsClient:**
```python
from backend.app.services.qrtools_client import QrtoolsClient

client = QrtoolsClient()

# Login với account_id
await client.login(
    username="user1",
    password="pass1",
    account_id="account_01"
)

# Lấy feed với account_id
feed_data = await client.get_feed(
    account_id="account_01",
    min_likes=100,
    has_media=True
)

# Like post với account_id
await client.like_post(
    post_id="3817952812169631580",
    username="may__lily",
    shortcode="DT8F9qykxdc",
    account_id="account_01"
)
```

## Session Isolation

Mỗi account có session riêng biệt:

1. **Session Files:**
   - `account_01` → `profile_threads/account_01/threads_session.json`
   - `account_02` → `profile_threads/account_02/threads_session.json`
   - Default → `output/threads_session.json`

2. **Browser Profiles:**
   - **Server-side (tự động)**: 
     - `account_01` → `profiles/account_01/` (nếu được cấu hình)
     - `account_02` → `profiles/account_02/` (nếu được cấu hình)
     - Default → Browser profile mặc định hoặc temporary context
   - **Client-side (explicit)**:
     - Chỉ sử dụng khi client chỉ định `profile_path`
     - Path được validate để tránh security issues
     - Mặc định không lưu profile ở máy chủ (bảo mật)

3. **Cache Isolation:**
   - Cache được tách biệt theo account_id
   - Mỗi account có cache riêng, không ảnh hưởng lẫn nhau

4. **Security Considerations:**
   - Browser profile không được lưu tự động ở máy chủ (mặc định)
   - Client phải chỉ định rõ ràng `profile_path` nếu muốn sử dụng persistent profile
   - Path validation để tránh path traversal attacks
   - Temporary browser context được sử dụng nếu không có `profile_path`

## Testing & Verification

### 1. Test Multi-Account Login

```bash
# Login với account_01
curl -X POST "http://localhost:3000/api/login?account_id=account_01" \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "pass1"}'

# Verify session file được tạo
ls -la profile_threads/account_01/threads_session.json

# Login với account_02
curl -X POST "http://localhost:3000/api/login?account_id=account_02" \
  -H "Content-Type: application/json" \
  -d '{"username": "user2", "password": "pass2"}'

# Verify session file được tạo
ls -la profile_threads/account_02/threads_session.json
```

### 2. Test Feed Extraction với Account ID

```bash
# Extract feed với account_01
curl "http://localhost:3000/api/feed?account_id=account_01&min_likes=100"

# Extract feed với account_02
curl "http://localhost:3000/api/feed?account_id=account_02&min_likes=100"

# Verify cache được tách biệt
curl "http://localhost:3000/api/stats?account_id=account_01"
curl "http://localhost:3000/api/stats?account_id=account_02"
```

### 3. Test Interactions với Account ID

```bash
# Like post với account_01
curl -X POST "http://localhost:3000/api/post/3817952812169631580/like?account_id=account_01&username=may__lily&shortcode=DT8F9qykxdc"

# Like post với account_02 (cùng post)
curl -X POST "http://localhost:3000/api/post/3817952812169631580/like?account_id=account_02&username=may__lily&shortcode=DT8F9qykxdc"

# Verify mỗi account có session riêng
```

### 4. Monitor Logs

**Qrtools API Logs:**
- Check account_id extraction: `[Account ID] Extracted account_id: account_01`
- Check session path: `[Session] Loading session from: profile_threads/account_01/threads_session.json`
- Check browser profile: `[Browser] Using profile: profiles/account_01/`

**Python Backend Logs:**
- Check account_id pass: `[QrtoolsClient] Calling API with account_id: account_01`
- Check request params: `[QrtoolsClient] Request params: {'account_id': 'account_01', ...}`

## Troubleshooting

### Vấn đề: Session không được load đúng account

**Nguyên nhân:**
- Account ID không được extract đúng
- Session path không đúng
- Browser profile không đúng

**Giải pháp:**
1. Verify account_id được pass đúng:
   ```bash
   # Enable logging trong Qrtools config
   CONFIG.api.accountId.logExtraction = true
   ```

2. Check session file path:
   ```bash
   ls -la profile_threads/account_01/threads_session.json
   ```

3. Check browser profile:
   ```bash
   ls -la profiles/account_01/
   ```

### Vấn đề: Cache bị conflict giữa các accounts

**Nguyên nhân:**
- Cache không được tách biệt theo account_id

**Giải pháp:**
- Clear cache và test lại:
  ```bash
  curl -X DELETE "http://localhost:3000/api/cache?account_id=account_01"
  ```

### Vấn đề: Browser profile không đúng

**Nguyên nhân:**
- Browser profile path không được resolve đúng
- Profile path không được validate
- Client không chỉ định `profile_path` nhưng expect persistent profile

**Giải pháp:**
1. Verify browser profile path trong Qrtools config
2. Check `profiles/{accountId}/` directory exists (nếu dùng server-side)
3. Verify `profile_path` được pass đúng từ client
4. Check path validation không block valid paths
5. Nếu cần persistent profile, đảm bảo pass `profile_path` rõ ràng

### Vấn đề: Profile path không được accept

**Nguyên nhân:**
- Path validation fail (chứa `..` hoặc `//`)
- Path không phải absolute hoặc relative hợp lệ
- Path không tồn tại

**Giải pháp:**
- Sử dụng absolute path: `/home/user/profiles/account_01`
- Hoặc relative path hợp lệ: `./profiles/account_01`
- Tránh sử dụng `..` trong path
- Đảm bảo directory tồn tại trước khi sử dụng

## Best Practices

1. **Luôn sử dụng account_id:**
   - Luôn pass account_id trong mọi request
   - Sử dụng query parameter cho GET requests
   - Sử dụng body hoặc header cho POST requests

2. **Session Management:**
   - Login một lần cho mỗi account
   - Session sẽ được tự động lưu và reuse
   - Không cần login lại trừ khi session expired

3. **Browser Profile Management:**
   - **Security First**: Mặc định không lưu browser profile ở máy chủ
   - **Explicit Path**: Chỉ sử dụng `profile_path` khi thực sự cần persistent profile
   - **Path Validation**: Đảm bảo profile path hợp lệ và an toàn
   - **Temporary Context**: Sử dụng temporary browser context khi không cần persistent profile
   - **Client-Side Control**: Client có toàn quyền kiểm soát profile path

4. **Cache Management:**
   - Clear cache khi cần fresh data
   - Cache được tách biệt theo account, không cần lo conflict

5. **Error Handling:**
   - Check response để verify account_id được sử dụng đúng
   - Monitor logs để debug issues
   - Handle session expired errors
   - Validate profile_path trước khi sử dụng

6. **Security Best Practices:**
   - Không hardcode profile paths trong code
   - Validate profile paths từ client input
   - Sử dụng temporary browser context khi không cần persistent profile
   - Không lưu sensitive data trong browser profiles

## Next Steps

1. **Verify Integration:**
   - ✅ Test với account_01 → should load session từ `profile_threads/account_01/threads_session.json`
   - ✅ Test với account_02 → should load session từ `profile_threads/account_02/threads_session.json`
   - ✅ Verify session được load đúng cho mỗi account
   - ✅ Verify browser profile được sử dụng đúng cho mỗi account

2. **Test Multi-Account:**
   - ✅ Login với account_01 → session saved to `profile_threads/account_01/`
   - ✅ Login với account_02 → session saved to `profile_threads/account_02/`
   - ✅ Verify không có conflict giữa các accounts

3. **Monitor Logs:**
   - ✅ Check Qrtools API logs để verify account_id được extract đúng
   - ✅ Check Python backend logs để verify account_id được pass đúng
   - ✅ Verify session paths trong Qrtools logs

4. **Documentation:**
   - ✅ API documentation đã được cập nhật với multi-account examples
   - ✅ Python integration examples
   - ✅ JavaScript/Node.js integration examples
   - ✅ Browser Profile Path (Client-Side Profile) documentation
   - ✅ Security best practices cho profile management

---

## Browser Profile Path (Client-Side Profile) - Chi tiết

### Tổng quan

**Lưu ý quan trọng về bảo mật:** Mặc định, hệ thống không lưu browser profile ở máy chủ để đảm bảo bảo mật và quyền riêng tư. Browser profile chỉ được tạo khi client chỉ định rõ ràng `profile_path`.

### Cách truyền Profile Path

Profile path có thể được truyền qua:

1. **Query Parameter**: `?profile_path=/path/to/profile` hoặc `?profile_dir=/path/to/profile`
2. **Request Body**: `{"profile_path": "/path/to/profile"}` hoặc `{"profile_dir": "/path/to/profile"}`
3. **HTTP Header**: `X-Profile-Path: /path/to/profile` hoặc `profile-path: /path/to/profile`

### Cấu hình

Các cấu hình quan trọng trong `src/config.js`:

- `CONFIG.browser.persistentProfile.enabled` - Bật/tắt persistent profile (mặc định: false)
- `CONFIG.browser.persistentProfile.requireExplicitPath` - Yêu cầu client chỉ định profile path (mặc định: true)

### Security Considerations

1. **Path Validation:**
   - Profile path phải là absolute path hoặc relative path hợp lệ
   - Path không được chứa `..` hoặc `//` để tránh path traversal attacks
   - Profile path được validate trước khi sử dụng

2. **Default Behavior:**
   - Nếu không có `profile_path`, hệ thống sẽ sử dụng temporary browser context
   - Temporary context không lưu profile, đảm bảo bảo mật
   - Client có toàn quyền kiểm soát khi nào sử dụng persistent profile

3. **Best Practices:**
   - Chỉ sử dụng `profile_path` khi thực sự cần persistent profile
   - Sử dụng temporary browser context cho các operations không cần persistent state
   - Validate profile paths từ client input
   - Không hardcode profile paths trong code

### Use Cases

1. **Temporary Operations (Recommended):**
   - Extract feed data (không cần login)
   - Read-only operations
   - Không cần persistent session

2. **Persistent Profile (When Needed):**
   - Login và maintain session
   - Interactions cần persistent state
   - Multi-request operations với cùng context

### Examples

**Temporary Context (Recommended for most cases):**
```bash
# Không cần profile_path - sử dụng temporary context
curl "http://localhost:3000/api/feed?account_id=account_01&min_likes=100"
```

**Persistent Profile (When needed):**
```bash
# Chỉ định profile_path khi cần persistent profile
curl "http://localhost:3000/api/feed?account_id=account_01&profile_path=/home/user/profiles/account_01"
```

**Kết hợp account_id và profile_path:**
```bash
# Sử dụng cả account_id và profile_path
curl -X POST "http://localhost:3000/api/login?account_id=account_01" \
  -H "Content-Type: application/json" \
  -H "X-Profile-Path: /home/user/profiles/account_01" \
  -d '{"username": "user1", "password": "pass1"}'
```