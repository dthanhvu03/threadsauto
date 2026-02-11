/**
 * Job type definitions.
 * 
 * JSDoc types for job-related data structures.
 */

/**
 * Job status values.
 * 
 * @typedef {'pending'|'scheduled'|'running'|'completed'|'failed'|'cancelled'} JobStatus
 */

/**
 * Job priority values.
 * 
 * @typedef {'NORMAL'|'HIGH'|'URGENT'} JobPriority
 */

/**
 * Platform values.
 * 
 * @typedef {'THREADS'|'FACEBOOK'} Platform
 */

/**
 * Job object structure.
 * 
 * @typedef {Object} Job
 * @property {string} job_id - Job identifier
 * @property {string} account_id - Account identifier
 * @property {string} content - Job content
 * @property {string} [content_full] - Full content (if truncated)
 * @property {string|null} scheduled_time - Scheduled time (ISO format)
 * @property {JobStatus} status - Job status
 * @property {string} [status_message] - Status message
 * @property {string|null} thread_id - Thread ID (if posted)
 * @property {JobPriority} [priority] - Job priority
 * @property {Platform} [platform] - Platform
 * @property {number} [retry_count] - Retry count
 * @property {string|null} created_at - Creation time (ISO format)
 * @property {string|null} started_at - Start time (ISO format)
 * @property {string|null} completed_at - Completion time (ISO format)
 * @property {Object|null} [running_duration] - Running duration info
 * @property {string|null} [link_aff] - Affiliate link
 * @property {Object} [error] - Error information (if failed)
 */

/**
 * Job creation data.
 * 
 * @typedef {Object} JobCreateData
 * @property {string} account_id - Account ID (required)
 * @property {string} content - Job content (required)
 * @property {string} scheduled_time - Scheduled time in ISO format (required)
 * @property {JobPriority} [priority] - Job priority (default: 'NORMAL')
 * @property {Platform} [platform] - Platform (default: 'THREADS')
 * @property {string} [link_aff] - Optional affiliate link
 */

/**
 * Job update data.
 * 
 * @typedef {Object} JobUpdateData
 * @property {string} [content] - Updated content
 * @property {string} [scheduled_time] - Updated scheduled time
 * @property {JobPriority} [priority] - Updated priority
 * @property {Platform} [platform] - Updated platform
 * @property {string} [link_aff] - Updated affiliate link
 */

/**
 * Job filters.
 * 
 * @typedef {Object} JobFilters
 * @property {string|null} accountId - Filter by account ID
 * @property {JobStatus|null} status - Filter by status
 * @property {Platform|null} platform - Filter by platform
 */

/**
 * Job statistics.
 * 
 * @typedef {Object} JobStats
 * @property {number} total - Total jobs
 * @property {number} completed - Completed jobs
 * @property {number} failed - Failed jobs
 * @property {number} pending - Pending jobs
 * @property {number} running - Running jobs
 * @property {number} today_posts - Today's posts
 * @property {number} success_rate - Success rate percentage
 */
