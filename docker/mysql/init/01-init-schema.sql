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
    job_type VARCHAR(50) DEFAULT 'post' COMMENT 'post or engagement',
    engagement_data JSON NULL DEFAULT NULL COMMENT 'Engagement criteria (like_criteria, comment_criteria, follow_criteria)',
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
    INDEX idx_platform (platform),
    INDEX idx_job_type (job_type),
    INDEX idx_account_job_type (account_id, job_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='All scheduled jobs (replaces JSON files) - supports both POST and ENGAGEMENT jobs';

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

-- Engagement Actions Table
CREATE TABLE IF NOT EXISTS engagement_actions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL COMMENT 'like, comment, or follow',
    target_id VARCHAR(255) NULL DEFAULT NULL COMMENT 'post_id, user_id, etc.',
    success BOOLEAN NOT NULL DEFAULT TRUE,
    error TEXT NULL DEFAULT NULL,
    metadata JSON NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_account_id (account_id),
    INDEX idx_action_type (action_type),
    INDEX idx_success (success),
    INDEX idx_created_at (created_at),
    INDEX idx_account_action (account_id, action_type),
    INDEX idx_account_created (account_id, created_at),
    INDEX idx_target_id (target_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Engagement actions executed (likes, comments, follows)';

-- Engagement Post History Table (tránh like trùng)
CREATE TABLE IF NOT EXISTS engagement_post_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(255) NOT NULL,
    post_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL COMMENT 'like, comment, or follow',
    action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON NULL DEFAULT NULL,
    
    UNIQUE KEY unique_account_post_action (account_id, post_id, action_type),
    INDEX idx_account_id (account_id),
    INDEX idx_post_id (post_id),
    INDEX idx_action_type (action_type),
    INDEX idx_action_date (action_date),
    INDEX idx_account_action (account_id, action_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Track posts đã thực hiện engagement (tránh duplicate)';

-- Feed Items Table (lưu feed posts từ Threads)
CREATE TABLE IF NOT EXISTS feed_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id VARCHAR(255) NOT NULL,
    account_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    text TEXT,
    like_count INT DEFAULT 0,
    reply_count INT DEFAULT 0,
    repost_count INT DEFAULT 0,
    share_count INT DEFAULT 0,
    view_count INT DEFAULT NULL,
    media_urls JSON NULL DEFAULT NULL,
    timestamp BIGINT NOT NULL COMMENT 'Unix timestamp (seconds)',
    timestamp_iso VARCHAR(50) NOT NULL COMMENT 'ISO 8601 timestamp',
    user_id VARCHAR(255) NOT NULL,
    user_display_name VARCHAR(255) NULL DEFAULT NULL,
    user_avatar_url TEXT NULL DEFAULT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    post_url TEXT NOT NULL,
    shortcode VARCHAR(255) NOT NULL,
    is_reply BOOLEAN DEFAULT FALSE,
    parent_post_id VARCHAR(255) NULL DEFAULT NULL,
    thread_id VARCHAR(255) NOT NULL,
    quoted_post JSON NULL DEFAULT NULL,
    hashtags JSON NULL DEFAULT NULL COMMENT 'Array of hashtags',
    mentions JSON NULL DEFAULT NULL COMMENT 'Array of mentions',
    links JSON NULL DEFAULT NULL COMMENT 'Array of links',
    media_type INT NULL DEFAULT NULL COMMENT '1=image, 2=video',
    video_duration INT NULL DEFAULT NULL COMMENT 'Video duration (seconds)',
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When this feed item was fetched',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_post_account_fetch (post_id, account_id, fetched_at),
    INDEX idx_post_id (post_id),
    INDEX idx_account_id (account_id),
    INDEX idx_username (username),
    INDEX idx_timestamp (timestamp),
    INDEX idx_fetched_at (fetched_at),
    INDEX idx_account_fetched (account_id, fetched_at),
    INDEX idx_thread_id (thread_id),
    INDEX idx_is_reply (is_reply),
    INDEX idx_parent_post_id (parent_post_id),
    FULLTEXT INDEX idx_text_fulltext (text)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Feed items fetched from Threads (with history tracking)';
