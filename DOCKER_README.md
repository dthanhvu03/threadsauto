# Docker Setup Guide

Hướng dẫn chạy ứng dụng với Docker.

## Prerequisites

- Docker >= 20.10
- Docker Compose >= 2.0

## Development Mode

Chạy với hot reload và volume mounts:

```bash
docker-compose -f docker-compose.dev.yml up --build
```

Frontend: http://localhost:5173  
Backend: http://localhost:8000

## Production Mode

Build và chạy production containers:

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

Frontend: http://localhost  
Backend: http://localhost:8000

## Standard Mode

Chạy với docker-compose.yml (default):

```bash
docker-compose up --build
```

## Useful Commands

```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart service
docker-compose restart backend

# Execute command in container
docker-compose exec backend python -m pytest

# Remove containers và volumes
docker-compose down -v

# Rebuild specific service
docker-compose build --no-cache frontend
```

## Environment Variables

Tạo `.env` file trong root directory:

```env
# Database
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=threads_automation

# Application
LOG_LEVEL=info
PORT=8000
```

## Troubleshooting

### Port already in use
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use different host port
```

### Permission errors
```bash
# Fix permissions
sudo chown -R $USER:$USER profiles/ logs/ jobs/
```

### Container won't start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild
docker-compose build --no-cache
```
