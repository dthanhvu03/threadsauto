# Threads Automation - Vue.js Frontend

Vue.js 3 frontend application với Tailwind CSS cho Threads Automation Tool.

## Setup

### Prerequisites

- Node.js 18+ và npm/yarn/pnpm
- Backend API đang chạy tại `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Frontend sẽ chạy tại `http://localhost:5173`

### Build

```bash
npm run build
```

Build files sẽ được tạo trong `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client wrappers
│   ├── components/       # Vue components
│   │   ├── common/       # Reusable components
│   │   └── layout/       # Layout components
│   ├── router/          # Vue Router configuration
│   ├── stores/           # Pinia stores
│   ├── views/            # Page views (tabs)
│   ├── App.vue           # Root component
│   └── main.js           # Entry point
├── index.html
├── package.json
├── vite.config.js
└── tailwind.config.js
```

## Features

- 📊 Dashboard: Overview stats, charts, recent activity
- 📅 Jobs: List, create, update, delete jobs với filters
- 📤 Excel Upload: Upload và process Excel files
- ⏰ Scheduler: Control scheduler, view active jobs
- 👤 Accounts: Account management
- ⚙️ Configuration: Application settings
- 🎯 Selectors: CSS selector management

## API Integration

Frontend giao tiếp với FastAPI backend qua REST API:

- Base URL: `/api` (proxied to `http://localhost:8000`)
- All API calls được handle bởi `src/api/client.js`
- Response format: `{ success: bool, data: any, error: string | null }`

## State Management

Sử dụng Pinia stores:

- `jobs`: Jobs state management
- `accounts`: Accounts state
- `dashboard`: Dashboard data
- `scheduler`: Scheduler state
- `config`: Configuration state
- `selectors`: Selectors state

## Styling

- Tailwind CSS cho styling
- Design tokens từ `ui/design_system.py` được migrate sang Tailwind config
- Responsive design với mobile-first approach
- Dark mode support (optional, chưa implement)

## Development Notes

- Components sử dụng Composition API
- TypeScript có thể được thêm sau nếu cần
- Charts sẽ được implement với Chart.js (placeholder hiện tại)
- Real-time updates sử dụng polling (WebSocket optional)
