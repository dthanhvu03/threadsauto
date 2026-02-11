# Hướng Dẫn Chạy Migration 004: Engagement Post History

## Migration này làm gì?

Tạo table `engagement_post_history` để track posts đã thực hiện engagement (tránh duplicate likes/comments/follows).

## Cách Chạy

### Option 1: Chạy Python Script (Khuyến nghị)

```bash
# Từ thư mục gốc của project
python scripts/migration/run_engagement_post_history_migration.py
```

Nếu có lỗi về credentials, có thể chỉ định:

```bash
python scripts/migration/run_engagement_post_history_migration.py \
    --host localhost \
    --port 3306 \
    --user threads_user \
    --password "" \
    --database threads_analytics
```

### Option 2: Chạy qua Docker Compose

```bash
# Copy SQL file vào container và chạy
docker-compose exec mysql mysql -u threads_user -p threads_analytics < docker/mysql/migrations/004_add_engagement_post_history.sql
```

Hoặc:

```bash
# Vào MySQL container
docker-compose exec mysql bash

# Trong container, chạy:
mysql -u threads_user -p threads_analytics < /path/to/004_add_engagement_post_history.sql
```

### Option 3: Chạy SQL trực tiếp

1. Connect vào MySQL:
```bash
docker-compose exec mysql mysql -u threads_user -p threads_analytics
```

2. Copy và paste nội dung file `docker/mysql/migrations/004_add_engagement_post_history.sql`

## Verify Migration

Sau khi chạy, kiểm tra:

```sql
-- Kiểm tra table đã được tạo
SHOW TABLES LIKE 'engagement_post_history';

-- Kiểm tra structure
DESCRIBE engagement_post_history;

-- Kiểm tra indexes
SHOW INDEXES FROM engagement_post_history;
```

## Kết Quả Mong Đợi

- ✅ Table `engagement_post_history` được tạo
- ✅ Index `idx_target_id` được thêm vào `engagement_actions` (nếu chưa có)
- ✅ Tất cả indexes được tạo thành công

## Troubleshooting

Nếu gặp lỗi "Table already exists":
- Migration đã được chạy trước đó
- Table đã tồn tại, không cần chạy lại

Nếu gặp lỗi connection:
- Kiểm tra MySQL đang chạy: `docker-compose ps`
- Kiểm tra credentials trong `.env` hoặc `config.yaml`
