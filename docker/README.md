# 🐳 Docker Setup cho MySQL

Quick start guide cho MySQL với Docker Compose.

## Quick Start

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env với credentials của bạn (optional, defaults are fine for dev)
nano .env

# 3. Run setup script (hoặc start manually)
./scripts/docker_mysql_setup.sh

# Hoặc manually:
docker-compose up -d mysql
```

## Services

### MySQL 8.0
- **Container:** `threads_mysql`
- **Port:** `3306` (configurable in .env)
- **Database:** `threads_analytics`
- **User:** `threads_user` (configurable)

### phpMyAdmin (Optional)
- **Container:** `threads_phpmyadmin`
- **Port:** `8080` (configurable in .env)
- **URL:** http://localhost:8080

## Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose stop

# View logs
docker-compose logs -f mysql

# Access MySQL CLI
docker-compose exec mysql mysql -u threads_user -p threads_analytics

# Backup database
docker-compose exec mysql mysqldump -u root -p threads_analytics > backup.sql

# Restore database
docker-compose exec -T mysql mysql -u root -p threads_analytics < backup.sql
```

## Files Structure

```
docker/
├── mysql/
│   ├── init/
│   │   └── 01-init-schema.sql  # Auto-run on first start
│   └── my.cnf                   # MySQL configuration
└── .dockerignore
```

## Environment Variables

See `.env.example` for all available variables.

## Troubleshooting

See [DOCKER_MYSQL_MIGRATION_PLAN.md](../docs/DOCKER_MYSQL_MIGRATION_PLAN.md) for detailed troubleshooting guide.
