# Threads Automation Tool

Công cụ automation local để đăng nội dung Threads sử dụng Playwright.

## Tính năng

- ✅ **Đăng nhập bền vững**: Sử dụng browser profile để lưu cookie/localStorage
- ✅ **Chống phát hiện**: Mô phỏng hành vi giống người (delay ngẫu nhiên, gõ theo chunk)
- ✅ **Xử lý trạng thái UI**: Phát hiện loading, disabled, success, error, và shadow fail
- ✅ **Logic retry**: Exponential backoff cho các thao tác thất bại
- ✅ **Structured Logging**: Log định dạng key-value để debug
- ✅ **Post Scheduling**: Lên lịch đăng bài với priority và retry logic
- ✅ **Excel Integration**: Đăng nhiều bài từ file Excel
- ✅ **Safety Guard**: Rate limiting và phát hiện trùng lặp (sẽ triển khai)

## Yêu cầu

- Python 3.11+
- Playwright
- Chromium browser
- pandas, openpyxl (cho Excel integration)

## Cài đặt

```bash
# Chạy script setup (tạo venv và cài đặt mọi thứ)
./setup.sh

# Hoặc thủ công:
# 1. Tạo virtual environment
python3 -m venv venv

# 2. Kích hoạt virtual environment
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Cài đặt dependencies
pip install -r requirements.txt

# 4. Cài đặt Playwright browsers
playwright install chromium
```

## Sử dụng nhanh

```bash
# Đăng một thread
python main.py --account account_01 --content "Xin chào Threads!"

# Lên lịch đăng bài
python main.py --account account_01 --content "Xin chào Threads!" --schedule "2025-12-17 10:00:00"

# Đăng từ Excel
python main.py --account account_01 --excel posts.xlsx

# Chạy scheduler
python main.py --scheduler --account account_01
```

Xem [CLI_USAGE.md](docs/CLI_USAGE.md) để biết tất cả các commands.

## Lần chạy đầu tiên

1. Chạy tool với ID tài khoản của bạn
2. Browser sẽ mở (chế độ headed)
3. Nếu chưa đăng nhập, tool sẽ tự động mở form đăng nhập và chờ bạn đăng nhập thủ công
4. Sau khi đăng nhập, các lần chạy sau sẽ tự động đăng nhập qua cookies đã lưu

## Chạy UI (Vue.js)

Sau khi cài đặt dependencies, bạn có thể chạy frontend UI:

```bash
cd frontend
npm install
npm run dev
```

UI sẽ mở tại: `http://localhost:5173`

**Features:**
- 📊 Dashboard: Overview stats, charts, recent activity
- 📅 Jobs: List, add, delete jobs với filters
- 📤 Excel Upload: Upload và process Excel files
- ⏰ Scheduler: Control scheduler, view active jobs
- 👤 Accounts: Account management

Xem chi tiết trong [UI_USAGE.md](docs/UI_USAGE.md)

**Note:** Streamlit UI đã được thay thế bằng Vue.js UI. Streamlit code đã được xóa.

---

## Cấu trúc dự án

```
threads_tool/
├── main.py                 # Điểm vào chính (entry point)
├── run_ui.sh              # Script chạy Streamlit UI
├── cli/                    # CLI module
│   ├── parser.py          # Argument parser
│   └── commands/          # Command handlers
│       ├── excel.py       # Excel commands
│       ├── jobs.py        # Job management commands
│       ├── post.py        # Post thread command
│       └── schedule.py    # Schedule & scheduler commands
├── ui/                     # UI module (Streamlit)
│   ├── streamlit_app.py   # Main Streamlit app
│   └── api/               # API wrappers
│       ├── jobs_api.py    # Jobs API wrapper
│       └── accounts_api.py # Accounts API wrapper
├── browser/
│   ├── manager.py         # Quản lý vòng đời browser
│   └── login_guard.py     # Phát hiện trạng thái đăng nhập
├── threads/
│   ├── composer.py        # Đăng thread với anti-detection
│   ├── verifier.py        # Xác minh đăng bài
│   ├── types.py           # Types & constants
│   ├── selectors.py       # UI selectors
│   ├── behavior.py        # Anti-detection behavior
│   └── ui_state.py        # UI state detection
├── services/
│   ├── logger.py          # Structured logging
│   ├── scheduler.py       # Job scheduler
│   └── exceptions.py     # Custom exceptions
├── content/
│   └── excel_loader.py    # Excel file loader
├── config/
│   └── config.py          # Quản lý cấu hình
├── profiles/              # Browser profiles (mỗi account một profile)
├── jobs/                  # Scheduled jobs (theo ngày)
└── logs/                  # File log
```

**Note:** Data directories (`logs/`, `profiles/`, `jobs/`) are runtime-only and excluded from repository. These directories are created automatically by the application and should not be committed to version control.

## Tài liệu

- **[CLI_USAGE.md](docs/CLI_USAGE.md)**: Hướng dẫn đầy đủ về CLI commands
- **[EXCEL_USAGE.md](docs/EXCEL_USAGE.md)**: Hướng dẫn sử dụng Excel để đăng bài
- **[SCHEDULER_WORKFLOW.md](docs/SCHEDULER_WORKFLOW.md)**: Chi tiết workflow của scheduler
- **[FLOW.md](docs/FLOW.md)**: Flow tổng quan của tool
- **[UI_USAGE.md](docs/UI_USAGE.md)**: Hướng dẫn sử dụng UI

## Chi tiết triển khai

### Browser Manager (`browser/manager.py`)

- Sử dụng `launch_persistent_context` để tự động lưu cookie/localStorage
- Chế độ headed (không headless) như yêu cầu
- Dọn dẹp đúng cách khi thoát
- Xử lý lỗi với structured logging

### Thread Composer (`threads/composer.py`)

- **Hành vi chống phát hiện**:
  - Delay ngẫu nhiên (0.5-2.0s)
  - Gõ theo chunk (4 ký tự mỗi chunk)
  - Click với offset ngẫu nhiên
  - Scroll trước khi click
  
- **Phát hiện trạng thái UI**:
  - Trạng thái loading
  - Trạng thái disabled
  - Trạng thái success
  - Trạng thái error
  - Shadow fail (đã click nhưng không đăng)

- **Logic retry**:
  - Tối đa 3 lần retry
  - Exponential backoff (1s, 2s, 4s)
  - Phát hiện shadow fail

### Login Guard (`browser/login_guard.py`)

- Nhiều fallback selectors để phát hiện đăng nhập
- Selectors có phiên bản (v1, v2)
- Luồng đăng nhập thủ công với timeout
- Tự động click nút "Continue with Instagram"

### Scheduler (`services/scheduler.py`)

- Job queue với priority (LOW, NORMAL, HIGH, URGENT)
- Lưu trữ theo ngày (`jobs/jobs_YYYY-MM-DD.json`)
- Retry logic với exponential backoff (2, 4, 8 phút)
- Auto cleanup expired jobs (quá 24h)
- Status tracking với detailed messages

## Cấu hình

Chỉnh sửa `config/config.py` để điều chỉnh:
- Cài đặt browser (slow_mo, timeout)
- Delay chống phát hiện
- Phiên bản selector
- Giới hạn an toàn

## Logging

Log được ghi vào thư mục `logs/` theo định dạng structured:

```
STEP=POST_THREAD RESULT=SUCCESS TIME=1234.56ms ACCOUNT=account_01 THREAD_ID=123456
```

## Tính năng an toàn

- Rate limiting (sẽ triển khai)
- Phát hiện nội dung trùng lặp (sẽ triển khai)
- Thực thi khoảng cách giữa các hành động (sẽ triển khai)
- Tự động tạm dừng khi rủi ro cao (sẽ triển khai)

## Kiến trúc

### Quy tắc `services/` Scope Freeze

Module `services/` chỉ chứa **shared infrastructure**:
- ✅ `logger` - Structured logging
- ✅ `scheduler` - Job scheduling
- ✅ `storage` - Data persistence (accounts, excel, selectors)
- ✅ `analytics` - Cross-module metrics

**❌ Cấm:** Business logic mới phải nằm trong `backend/app/modules/*/services/`, không được thêm vào `services/` root.

## Lưu ý

- **KHÔNG** tự động hóa đăng nhập với username/password
- **KHÔNG** sử dụng headless browser
- **KHÔNG** đăng hàng loạt hoặc spam
- Luôn giả định UI có thể thay đổi
- Tối ưu cho ổn định > tốc độ

## License

MIT
