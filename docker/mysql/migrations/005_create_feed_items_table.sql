-- Migration 005: Create feed_items table
-- Date: 2024-12-XX
-- Description: Create feed_items table to store feed posts from Threads with history tracking

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
