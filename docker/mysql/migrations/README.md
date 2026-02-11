# Database Migrations

Migration scripts để cập nhật database schema.

## Migration 003: Add Engagement Job Support

**File:** `003_add_engagement_job_fields.sql`

**Date:** 2024-12-17

**Description:** Thêm hỗ trợ cho engagement jobs (like, comment, follow) vào bảng `jobs`.

### Changes

1. **Thêm cột `job_type`**
   - Type: `VARCHAR(50)`
   - Default: `'post'`
   - Values: `'post'` hoặc `'engagement'`
   - Position: Sau cột `platform`

2. **Thêm cột `engagement_data`**
   - Type: `JSON`
   - Nullable: Yes
   - Description: Lưu engagement criteria (like_criteria, comment_criteria, follow_criteria)
   - Position: Sau cột `job_type`

3. **Thêm indexes**
   - `idx_job_type`: Index trên `job_type`
   - `idx_account_job_type`: Composite index trên `(account_id, job_type)`

4. **Backward Compatibility**
   - Tự động update tất cả jobs hiện có để có `job_type = 'post'`

## Cách chạy migration

### Option 1: Chạy SQL script trực tiếp

```bash
# Với Docker
docker-compose exec mysql mysql -u threads_user -p threads_analytics < docker/mysql/migrations/003_add_engagement_job_fields.sql

# Hoặc copy script vào container và chạy
docker-compose exec mysql mysql -u threads_user -p threads_analytics -e "source /path/to/003_add_engagement_job_fields.sql"
```

### Option 2: Chạy Python migration script (Recommended)

```bash
# Chạy với config từ .env
python scripts/migration/run_engagement_migration.py

# Hoặc với custom credentials
python scripts/migration/run_engagement_migration.py \
    --host localhost \
    --port 3306 \
    --user threads_user \
    --password "your_password" \
    --database threads_analytics
```

### Option 3: Chạy qua MySQL CLI

```bash
# Connect to MySQL
docker-compose exec mysql mysql -u threads_user -p threads_analytics

# Copy và paste nội dung file 003_add_engagement_job_fields.sql
```

## Verify Migration

Sau khi chạy migration, kiểm tra:

```sql
-- Kiểm tra columns đã được thêm
DESCRIBE jobs;

-- Kiểm tra indexes
SHOW INDEXES FROM jobs WHERE Key_name IN ('idx_job_type', 'idx_account_job_type');

-- Kiểm tra existing jobs có job_type
SELECT job_id, account_id, job_type, engagement_data 
FROM jobs 
LIMIT 10;
```

## Rollback (nếu cần)

Nếu cần rollback migration:

```sql
-- Xóa indexes
DROP INDEX idx_account_job_type ON jobs;
DROP INDEX idx_job_type ON jobs;

-- Xóa columns
ALTER TABLE jobs DROP COLUMN engagement_data;
ALTER TABLE jobs DROP COLUMN job_type;
```

**Lưu ý:** Rollback sẽ mất dữ liệu trong các cột này. Chỉ rollback nếu chắc chắn.

## Migration 004: Add Engagement Post History Table

**File:** `004_add_engagement_post_history.sql`

**Date:** 2024-12-17

**Description:** Tạo table `engagement_post_history` để track posts đã thực hiện engagement (tránh duplicate likes/comments/follows).

### Changes

1. **Tạo table `engagement_post_history`**
   - Columns: `id`, `account_id`, `post_id`, `action_type`, `action_date`, `metadata`
   - Unique constraint: `(account_id, post_id, action_type)` - tránh duplicate
   - Indexes: `idx_account_id`, `idx_post_id`, `idx_action_type`, `idx_action_date`, `idx_account_action`

2. **Thêm index `idx_target_id` trên `engagement_actions`**
   - Index trên `target_id` để cải thiện query performance

## Cách chạy migration 004

### Option 1: Chạy Python migration script (Recommended)

```bash
# Chạy với config từ .env
python scripts/migration/run_engagement_post_history_migration.py

# Hoặc với custom credentials
python scripts/migration/run_engagement_post_history_migration.py \
    --host localhost \
    --port 3306 \
    --user threads_user \
    --password "your_password" \
    --database threads_analytics
```

### Option 2: Chạy SQL script trực tiếp

```bash
# Với Docker
docker-compose exec mysql mysql -u threads_user -p threads_analytics < docker/mysql/migrations/004_add_engagement_post_history.sql

# Hoặc copy script vào container và chạy
docker-compose exec mysql mysql -u threads_user -p threads_analytics -e "source /path/to/004_add_engagement_post_history.sql"
```

### Option 3: Chạy qua MySQL CLI

```bash
# Connect to MySQL
docker-compose exec mysql mysql -u threads_user -p threads_analytics

# Copy và paste nội dung file 004_add_engagement_post_history.sql
```

## Verify Migration 004

Sau khi chạy migration, kiểm tra:

```sql
-- Kiểm tra table đã được tạo
SHOW TABLES LIKE 'engagement_post_history';

-- Kiểm tra structure
DESCRIBE engagement_post_history;

-- Kiểm tra indexes
SHOW INDEXES FROM engagement_post_history;

-- Kiểm tra index trên engagement_actions
SHOW INDEXES FROM engagement_actions WHERE Key_name = 'idx_target_id';
```

## Notes

- Migration script sử dụng `IF NOT EXISTS` pattern để an toàn khi chạy nhiều lần
- Existing jobs sẽ được tự động set `job_type = 'post'` để backward compatible
- Migration không ảnh hưởng đến dữ liệu hiện có
- Table `engagement_post_history` sẽ được tự động populate khi engagement actions được thực hiện