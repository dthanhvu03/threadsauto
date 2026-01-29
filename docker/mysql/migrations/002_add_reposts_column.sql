-- Migration: Add reposts column to thread_metrics table
-- Date: 2024
-- Description: Threads có 5 metrics: Views, Likes, Replies, Reposts (Đăng lại), Shares (Chia sẻ)
--               Cần tách "reposts" riêng biệt với "shares"

-- Add reposts column
ALTER TABLE thread_metrics 
ADD COLUMN reposts INT NOT NULL DEFAULT 0 AFTER replies;

-- Update COMMENT
ALTER TABLE thread_metrics 
MODIFY COLUMN shares INT NOT NULL DEFAULT 0 
COMMENT 'Chia sẻ (Share)';

ALTER TABLE thread_metrics 
MODIFY COLUMN reposts INT NOT NULL DEFAULT 0 
COMMENT 'Đăng lại (Repost)';

-- Update table comment
ALTER TABLE thread_metrics 
COMMENT = 'Thread metrics (views, likes, replies, reposts, shares) over time';

-- Update jobs_with_metrics VIEW
-- Use CREATE OR REPLACE instead of DROP to avoid privilege issues
CREATE OR REPLACE VIEW jobs_with_metrics AS
SELECT 
    j.job_id,
    j.account_id,
    j.content,
    j.thread_id,
    j.scheduled_at,
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

-- Update account_summary VIEW
-- Use CREATE OR REPLACE instead of DROP to avoid privilege issues
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
LEFT JOIN (
    SELECT 
        thread_id,
        likes as latest_likes,
        replies as latest_replies,
        reposts as latest_reposts,
        shares as latest_shares,
        ROW_NUMBER() OVER (PARTITION BY thread_id ORDER BY fetched_at DESC) as rn
    FROM thread_metrics
) m ON j.thread_id = m.thread_id AND m.rn = 1
WHERE j.status = 'completed'
GROUP BY j.account_id;
