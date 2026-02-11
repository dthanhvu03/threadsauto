# Migration 005: Create feed_items Table

## Description

Tạo table `feed_items` để lưu feed posts từ Threads với history tracking.

## Cách chạy migration

### Option 1: Chạy Python script (Recommended)

```bash
# Từ project root
python scripts/migration/run_feed_items_migration.py
```

Script sẽ tự động:
- Load MySQL config từ `.env`
- Kiểm tra xem table đã tồn tại chưa
- Tạo table nếu chưa có
- Verify table đã được tạo thành công

### Option 2: Chạy SQL trực tiếp qua MySQL CLI

```bash
# Với Docker
docker-compose exec mysql mysql -u threads_user -p threads_analytics < docker/mysql/migrations/005_create_feed_items_table.sql

# Hoặc connect vào MySQL và chạy
docker-compose exec mysql mysql -u threads_user -p threads_analytics
# Sau đó copy/paste nội dung file 005_create_feed_items_table.sql
```

### Option 3: Restart MySQL container (nếu chưa có data)

Nếu MySQL container chưa có data, có thể restart để init script tự động chạy:

```bash
docker-compose restart mysql
```

**Lưu ý:** Chỉ restart nếu chưa có data quan trọng, vì init script chỉ chạy khi database trống.

## Verify Migration

Sau khi chạy migration, kiểm tra:

```sql
-- Kiểm tra table đã được tạo
SHOW TABLES LIKE 'feed_items';

-- Kiểm tra structure
DESCRIBE feed_items;

-- Kiểm tra indexes
SHOW INDEXES FROM feed_items;
```

## Rollback (nếu cần)

Nếu cần rollback migration:

```sql
DROP TABLE IF EXISTS feed_items;
```

**Lưu ý:** Rollback sẽ xóa tất cả dữ liệu trong table. Chỉ rollback nếu chắc chắn.
