# Troubleshooting Guide

## Common Browser Console Errors

### 1. "Unchecked runtime.lastError: Could not establish connection. Receiving end does not exist."

**Nguyên nhân:**
- Đây là lỗi từ **browser extension** (không phải từ code của ứng dụng)
- Xảy ra khi một extension cố gắng gửi message nhưng không có receiver
- Thường gặp với các extension như ad blockers, privacy tools, hoặc các extension khác

**Giải pháp:**
- Lỗi này **không ảnh hưởng** đến ứng dụng của bạn
- Có thể bỏ qua hoặc disable extension gây lỗi
- Để tìm extension gây lỗi:
  1. Mở Chrome Extensions (`chrome://extensions/`)
  2. Disable từng extension một
  3. Reload trang và kiểm tra console

### 2. "Cannot read properties of undefined (reading 'payload')"

**Nguyên nhân:**
- Lỗi này thường đến từ **browser extension** (như `giveFreely.tsx`)
- Có thể xảy ra nếu WebSocket message không có structure đúng

**Giải pháp:**
- Code đã được cập nhật để handle cả `message.data` và `message.payload`
- Thêm validation cho message structure
- Error handling đã được cải thiện

**Nếu lỗi vẫn xảy ra:**
1. Kiểm tra browser extensions
2. Thử disable extensions và reload
3. Kiểm tra Network tab xem WebSocket có kết nối không

## WebSocket Connection Issues

### WebSocket không kết nối được

**Kiểm tra:**
1. Backend có đang chạy không? (`http://localhost:8000`)
2. CORS đã được cấu hình đúng chưa?
3. WebSocket URL đúng chưa? (ws://localhost:8000/ws)

**Debug:**
- Mở Browser DevTools > Network > WS tab
- Xem WebSocket connection status
- Kiểm tra console logs

### WebSocket messages không được nhận

**Kiểm tra:**
1. WebSocket client đã connect chưa?
2. Message format đúng chưa? (phải có `type` và `data` hoặc `payload`)
3. Event listeners đã được setup chưa?

## Common Issues

### 1. Jobs count = 0

**Nguyên nhân:**
- Không có jobs trong database cho account đó
- account_id không khớp giữa accounts và jobs table

**Giải pháp:**
- Kiểm tra database: `SELECT account_id, COUNT(*) FROM jobs GROUP BY account_id`
- Kiểm tra backend logs để xem query có chạy đúng không

### 2. API không trả về data

**Kiểm tra:**
1. Backend có đang chạy không?
2. API endpoint đúng chưa?
3. CORS đã được cấu hình chưa?
4. Network tab xem request có lỗi không?

### 3. UI không update

**Kiểm tra:**
1. WebSocket có kết nối không?
2. Store có được update không?
3. Component có reactive không?

## Debug Tips

### Enable Debug Logging

Trong browser console:
```javascript
localStorage.setItem('debug', 'true')
```

### Check WebSocket Connection

```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws?room=dashboard')
ws.onopen = () => console.log('Connected')
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data))
ws.onerror = (e) => console.error('Error:', e)
```

### Check API Endpoints

```javascript
// In browser console
fetch('/api/accounts')
  .then(r => r.json())
  .then(console.log)
  .catch(console.error)
```
