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
- ✅ **Git CLI Tool**: Interactive menu để quản lý Git operations dễ dàng
- 🚧 **Safety Guard**: Rate limiting và phát hiện trùng lặp (đang phát triển)

## Yêu cầu

- Python 3.11+
- Node.js 18+ (cho feed extraction)
- Playwright (Python và Node.js)
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

# 4. Cài đặt Playwright browsers (Python)
playwright install chromium

# 5. Cài đặt Node.js dependencies (cho feed extraction)
cd scripts
npm install
npx playwright install chromium
cd ..
```

## Sử dụng nhanh

### Threads Automation

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

### Git CLI Tool

```bash
# Chạy interactive menu
python scripts/cli/git_cli.py --menu
# hoặc đơn giản
python scripts/cli/git_cli.py

# Hoặc sử dụng command-line arguments
python scripts/cli/git_cli.py status
python scripts/cli/git_cli.py add --all
python scripts/cli/git_cli.py commit "My commit message"
python scripts/cli/git_cli.py push

# Quick push (add + commit + push)
python scripts/cli/git_cli.py quick "My commit message"

# Setup repository lần đầu
python scripts/cli/git_cli.py setup https://github.com/user/repo.git
```

**Git CLI Features:**
- 📋 **Interactive Menu**: Menu nhóm với 4 categories (Basic, Push/Pull, Setup, Advanced)
- 🔧 **Auto Setup**: Tự động setup Git user config nếu chưa có
- 🔐 **SSH Support**: Tự động setup SSH host keys cho GitHub
- ⚠️ **Error Handling**: Xử lý các lỗi phổ biến (unrelated histories, merge conflicts, authentication)
- 🚀 **Quick Push**: One-command để add, commit và push

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

---

## Cấu trúc dự án

```
threads_tool/
├── main.py                 # Entry point chính
├── scripts.py              # Scripts entry point
├── setup.sh                # Setup script
├── requirements.txt        # Python dependencies
├── pytest.ini              # Pytest configuration
├── LICENSE                 # License file
├── DOCKER_README.md        # Docker documentation
├── docker-compose.yml      # Docker Compose config
├── docker-compose.dev.yml  # Docker Compose dev config
├── docker-compose.prod.yml # Docker Compose prod config
├── Dockerfile.backend      # Backend Dockerfile
├── Dockerfile.frontend     # Frontend Dockerfile
├── cli/                    # CLI module
│   ├── parser.py          # Argument parser
│   └── commands/          # Command handlers
│       ├── excel.py       # Excel commands
│       ├── jobs.py        # Job management commands
│       ├── post.py        # Post thread command
│       └── schedule.py    # Schedule & scheduler commands
├── scripts/               # Utility scripts
│   ├── cli/               # CLI tools
│   │   ├── git_cli.py     # Git CLI với interactive menu
│   │   └── jobs_cli.py    # Jobs CLI
│   ├── utility/           # Utility scripts
│   │   ├── archive_old_jobs.py
│   │   ├── cleanup_old_logs.py
│   │   ├── fetch_all_metrics.py
│   │   ├── sync_jobs_from_logs.py
│   │   └── ...
│   ├── test/              # Test scripts
│   ├── analysis/          # Analysis scripts
│   ├── check/             # Check scripts
│   ├── cleanup/           # Cleanup scripts
│   ├── debug/             # Debug scripts
│   ├── archive/            # Archive scripts
│   ├── backup/            # Backup scripts
│   ├── migration/         # Migration scripts
│   ├── sh/                # Shell scripts
│   └── common.py          # Common utilities
├── browser/               # Browser automation
│   ├── manager.py         # Quản lý vòng đời browser
│   └── login_guard.py     # Phát hiện trạng thái đăng nhập
├── threads/               # Threads automation
│   ├── composer.py        # Đăng thread với anti-detection
│   ├── verifier.py        # Xác minh đăng bài
│   ├── types.py           # Types & constants
│   ├── selectors.py       # UI selectors
│   ├── behavior.py        # Anti-detection behavior
│   └── ui_state.py        # UI state detection
├── facebook/              # Facebook automation
│   ├── composer.py        # Facebook post composer
│   ├── navigation.py      # Navigation helpers
│   ├── selectors.py       # UI selectors
│   └── ...
├── services/              # Shared services
│   ├── logger.py          # Structured logging
│   ├── scheduler.py       # Job scheduler
│   └── exceptions.py     # Custom exceptions
├── content/               # Content processing
│   └── excel_loader.py    # Excel file loader
├── config/                # Configuration
│   ├── config.py          # Main config
│   ├── storage.py         # Storage config
│   └── selectors_storage.py
├── utils/                 # Utility modules
│   └── ...
├── backend/               # FastAPI backend
│   ├── main.py            # FastAPI entry point
│   ├── api/               # API layer
│   │   ├── adapters/      # Data adapters
│   │   ├── routes/        # API routes
│   │   └── websocket/     # WebSocket support
│   ├── app/               # Application layer
│   │   ├── core/          # Core utilities
│   │   ├── modules/       # Feature modules
│   │   │   ├── accounts/  # Accounts module
│   │   │   ├── jobs/      # Jobs module
│   │   │   ├── scheduler/ # Scheduler module
│   │   │   ├── excel/     # Excel module
│   │   │   ├── dashboard/ # Dashboard module
│   │   │   ├── config/    # Config module
│   │   │   └── selectors/ # Selectors module
│   │   └── shared/        # Shared base classes
│   ├── app_flask/         # Flask alternative
│   ├── tests/             # Backend tests
│   └── utils/             # Backend utilities
├── frontend/              # Vue.js frontend
│   ├── src/
│   │   ├── api/           # API clients
│   │   ├── components/    # Vue components
│   │   │   ├── common/    # Common components
│   │   │   ├── dashboard/ # Dashboard components
│   │   │   └── layout/    # Layout components
│   │   ├── composables/   # Vue composables
│   │   ├── core/          # Core utilities
│   │   ├── features/      # Feature modules
│   │   │   ├── accounts/  # Accounts feature
│   │   │   ├── jobs/      # Jobs feature
│   │   │   ├── scheduler/ # Scheduler feature
│   │   │   ├── excel/     # Excel feature
│   │   │   ├── dashboard/ # Dashboard feature
│   │   │   ├── config/    # Config feature
│   │   │   └── selectors/ # Selectors feature
│   │   ├── router/        # Vue Router
│   │   ├── stores/        # Pinia stores
│   │   ├── utils/         # Utility functions
│   │   └── views/         # Page views
│   ├── tests/             # Frontend tests
│   ├── package.json
│   └── vite.config.js
├── docker/                # Docker configurations
│   └── mysql/             # MySQL config
├── docs/                  # Documentation
├── profiles/              # Browser profiles (runtime - mỗi account một profile)
├── jobs/                  # Scheduled jobs (runtime - theo ngày)
└── logs/                  # Log files (runtime)
```

**Note:** 
- Data directories (`logs/`, `profiles/`, `jobs/`, `uploads/`) are runtime-only and excluded from repository. These directories are created automatically by the application and should not be committed to version control.
- Docker support: Xem [DOCKER_README.md](DOCKER_README.md) để biết cách sử dụng Docker Compose cho development và production.

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

### Git CLI Tool (`scripts/cli/git_cli.py`)

- **Interactive Menu System**:
  - Main menu với 4 nhóm operations (Basic, Push/Pull, Setup, Advanced)
  - Sub-menus cho từng nhóm với numbered options
  - Prompt cho parameters khi cần
  - Error handling với clear messages

- **Auto Setup Features**:
  - Tự động setup Git user config (`user.name`, `user.email`)
  - Tự động setup SSH host keys cho GitHub
  - Tự động convert HTTPS URLs sang SSH format (optional)

- **Error Handling**:
  - Xử lý "unrelated histories" với `--allow-unrelated-histories`
  - Xử lý "divergent branches" với merge strategy
  - Xử lý merge conflicts với hướng dẫn rõ ràng
  - Xử lý authentication errors với hướng dẫn PAT/SSH setup

- **Commands**:
  - `status`: Xem git status
  - `add`: Add files (--all hoặc specific files)
  - `commit`: Commit với message
  - `push`: Push lên remote
  - `pull`: Pull từ remote với error handling
  - `quick`: Quick push (add + commit + push)
  - `init`: Khởi tạo git repository
  - `setup-remote`: Setup remote repository
  - `setup`: Complete setup (init + remote + commit + push)

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

## Tính năng sắp tới (Roadmap)

- Rate limiting
- Phát hiện nội dung trùng lặp
- Thực thi khoảng cách giữa các hành động
- Tự động tạm dừng khi rủi ro cao

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
