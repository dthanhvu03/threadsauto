-- Initialize threads_analytics database schema
-- This script runs automatically when MySQL container starts for the first time

USE threads_analytics;

-- Thread Metrics Table
CREATE TABLE IF NOT EXISTS thread_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    views INT DEFAULT NULL COMMENT 'Lượt xem',
    likes INT NOT NULL DEFAULT 0 COMMENT 'Thích',
    replies INT NOT NULL DEFAULT 0 COMMENT 'Trả lời',
    reposts INT NOT NULL DEFAULT 0 COMMENT 'Đăng lại',
    shares INT NOT NULL DEFAULT 0 COMMENT 'Chia sẻ',
    fetched_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_thread_fetch (thread_id, fetched_at),
    INDEX idx_thread_id (thread_id),
    INDEX idx_account_id (account_id),
    INDEX idx_fetched_at (fetched_at),
    INDEX idx_account_fetched (account_id, fetched_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Thread metrics (views, likes, replies, reposts, shares) over time';

-- Jobs Table (THAY THẾ JSON files)
CREATE TABLE IF NOT EXISTS jobs (
    job_id VARCHAR(255) PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    scheduled_time TIMESTAMP NOT NULL,
    priority INT NOT NULL DEFAULT 2,
    status VARCHAR(50) NOT NULL,
    platform VARCHAR(50) DEFAULT 'threads',
    max_retries INT NOT NULL DEFAULT 3,
    retry_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP NULL DEFAULT NULL,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    error TEXT NULL DEFAULT NULL,
    thread_id VARCHAR(255) NULL DEFAULT NULL,
    status_message TEXT NULL DEFAULT NULL,
    link_aff TEXT NULL DEFAULT NULL,
    
    INDEX idx_account_id (account_id),
    INDEX idx_status (status),
    INDEX idx_scheduled_time (scheduled_time),
    INDEX idx_completed_at (completed_at),
    INDEX idx_thread_id (thread_id),
    INDEX idx_account_status (account_id, status),
    INDEX idx_status_scheduled (status, scheduled_time),
    INDEX idx_platform (platform)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='All scheduled jobs (replaces JSON files)';

-- Jobs View (backward compatibility for analytics)
CREATE OR REPLACE VIEW jobs_view AS
SELECT 
    job_id,
    account_id,
    thread_id,
    content,
    scheduled_time,
    completed_at,
    status,
    platform,
    created_at,
    NOW() as updated_at
FROM jobs
WHERE status IN ('completed', 'failed', 'expired');

-- View: Jobs with Latest Metrics
CREATE OR REPLACE VIEW jobs_with_metrics AS
SELECT 
    j.job_id,
    j.account_id,
    j.thread_id,
    j.content,
    j.scheduled_time,
    j.completed_at,
    j.status,
    j.platform,
    m.views as latest_views,
    m.likes as latest_likes,
    m.replies as latest_replies,
    m.reposts as latest_reposts,
    m.shares as latest_shares,
    m.fetched_at as last_metrics_fetch,
    TIMESTAMPDIFF(HOUR, j.completed_at, NOW()) as hours_since_post
FROM jobs_view j
LEFT JOIN (
    SELECT 
        thread_id,
        views,
        likes,
        replies,
        reposts,
        shares,
        fetched_at,
        ROW_NUMBER() OVER (PARTITION BY thread_id ORDER BY fetched_at DESC) as rn
    FROM thread_metrics
) m ON j.thread_id = m.thread_id AND m.rn = 1
WHERE j.status = 'completed' AND j.thread_id IS NOT NULL;

-- View: Account Summary Statistics
CREATE OR REPLACE VIEW account_summary AS
SELECT 
    j.account_id,
    COUNT(DISTINCT j.job_id) as total_posts,
    COUNT(DISTINCT j.thread_id) as total_threads,
    SUM(m.latest_likes) as total_likes,
    SUM(m.latest_replies) as total_replies,
    SUM(m.latest_reposts) as total_reposts,
    SUM(m.latest_shares) as total_shares,
    AVG(m.latest_likes) as avg_likes_per_post,
    AVG(m.latest_replies) as avg_replies_per_post,
    AVG(m.latest_reposts) as avg_reposts_per_post,
    AVG(m.latest_shares) as avg_shares_per_post,
    MAX(j.completed_at) as last_post_at
FROM jobs_view j
LEFT JOIN jobs_with_metrics m ON j.job_id = m.job_id
WHERE j.status = 'completed' AND j.thread_id IS NOT NULL
GROUP BY j.account_id;

-- Accounts Table (Metadata only, profiles still on file system)
CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(255) PRIMARY KEY,
    profile_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSON,
    
    INDEX idx_is_active (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Account metadata (profile directories still on file system)';

-- Application Config Table
CREATE TABLE IF NOT EXISTS app_config (
    config_key VARCHAR(100) PRIMARY KEY,
    config_value JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    description TEXT,
    
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Application configuration storage';

-- Selectors Table
CREATE TABLE IF NOT EXISTS selectors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    version VARCHAR(50) NOT NULL,
    selector_name VARCHAR(100) NOT NULL,
    selector_value JSON NOT NULL,
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_platform_version_name (platform, version, selector_name),
    INDEX idx_platform (platform),
    INDEX idx_version (version),
    INDEX idx_platform_version (platform, version)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Selector definitions for different platforms and versions';

-- Excel Processed Files Table
CREATE TABLE IF NOT EXISTS excel_processed_files (
    file_hash VARCHAR(255) PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    total_jobs INT NOT NULL DEFAULT 0,
    scheduled_jobs INT NOT NULL DEFAULT 0,
    immediate_jobs INT NOT NULL DEFAULT 0,
    success_count INT NOT NULL DEFAULT 0,
    failed_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_account_id (account_id),
    INDEX idx_processed_at (processed_at),
    INDEX idx_file_name (file_name(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Excel files that have been processed (replaces JSON storage)';

-- Excel Processing Locks Table
CREATE TABLE IF NOT EXISTS excel_processing_locks (
    file_hash VARCHAR(255) PRIMARY KEY,
    file_name VARCHAR(500) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_expires_at (expires_at),
    INDEX idx_started_at (started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Processing locks for Excel files (prevents concurrent processing)';
