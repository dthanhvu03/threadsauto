# Threads Automation - FastAPI Backend

FastAPI REST API backend cho Threads Automation Tool.

## Setup

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Development

```bash
python main.py
```

Hoặc với uvicorn:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API sẽ chạy tại `http://localhost:8000`

### API Documentation

Sau khi start server, truy cập:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
backend/
├── api/
│   ├── routes/           # API route handlers
│   │   ├── jobs.py
│   │   ├── accounts.py
│   │   ├── dashboard.py
│   │   ├── excel.py
│   │   ├── scheduler.py
│   │   ├── config.py
│   │   └── selectors.py
│   ├── adapters/         # API adapters (orchestration layer)
│   │   ├── jobs_adapter.py
│   │   ├── accounts_adapter.py
│   │   ├── analytics_adapter.py
│   │   ├── metrics_adapter.py
│   │   ├── safety_adapter.py
│   │   ├── selectors_adapter.py
│   │   ├── job_serializer.py
│   │   └── jobs_helpers.py
│   ├── dependencies.py    # Shared dependencies
│   └── responses.py       # Response helpers
├── main.py                # FastAPI app entry
└── requirements.txt
```

## API Endpoints

### Jobs

- `GET /api/jobs` - List jobs
- `GET /api/jobs/{job_id}` - Get job by ID
- `POST /api/jobs` - Create job
- `PUT /api/jobs/{job_id}` - Update job
- `DELETE /api/jobs/{job_id}` - Delete job

### Accounts

- `GET /api/accounts` - List accounts
- `GET /api/accounts/{account_id}` - Get account by ID
- `GET /api/accounts/{account_id}/stats` - Get account stats
- `POST /api/accounts` - Create account
- `DELETE /api/accounts/{account_id}` - Delete account

### Dashboard

- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/metrics` - Get dashboard metrics
- `GET /api/dashboard/activity` - Get recent activity

### Excel

- `POST /api/excel/upload` - Upload Excel file
- `GET /api/excel/template` - Download template

### Scheduler

- `POST /api/scheduler/start` - Start scheduler
- `POST /api/scheduler/stop` - Stop scheduler
- `GET /api/scheduler/status` - Get scheduler status
- `GET /api/scheduler/jobs` - Get active jobs

### Config

- `GET /api/config` - Get configuration
- `PUT /api/config` - Update configuration

### Selectors

- `GET /api/selectors` - Get selectors
- `PUT /api/selectors` - Update selectors

## Response Format

Tất cả responses follow standard format:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "message": "Optional message"
}
```

## Error Handling

- HTTP status codes được sử dụng đúng chuẩn
- Error messages trong response body
- Exception handlers cho validation errors và general errors
- Structured logging với `StructuredLogger`

## CORS

CORS được cấu hình để cho phép requests từ:

- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative port)

## Integration

Backend wrap các existing API classes:

- `ui.api.jobs_api.JobsAPI`
- `ui.api.accounts_api.AccountsAPI`
- Và các classes khác từ existing codebase

Business logic được giữ nguyên, chỉ thêm REST API layer.
