-- Migration: Update VIEWs to include reposts
-- Date: 2024
-- Description: Update jobs_with_metrics and account_summary VIEWs to include reposts column

-- Update jobs_with_metrics VIEW (use CREATE OR REPLACE to avoid privilege issues)
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

-- Update account_summary VIEW
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
