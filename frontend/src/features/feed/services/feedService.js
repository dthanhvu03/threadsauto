/**
 * Feed API service.
 * 
 * Handles all API calls for feed feature.
 * Uses BaseService for common HTTP methods.
 */

import { BaseService } from '@/core/api/baseService'

/**
 * Feed service instance.
 * 
 * @class
 * @extends {BaseService}
 */
class FeedService extends BaseService {
  constructor() {
    super('/feed')
  }

  /**
   * Prepare query parameters with account_id and profile options.
   * 
   * @param {Object} options - Options
   * @param {string} [options.account_id] - Account ID
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Object} Query parameters
   */
  _prepareParams(options = {}) {
    const params = {}
    if (options.account_id) {
      params.account_id = options.account_id
    }
    if (options.profile_path) {
      params.profile_path = options.profile_path
    }
    if (options.profile_dir) {
      params.profile_dir = options.profile_dir
    }
    if (options.profile_id) {
      params.profile_id = options.profile_id
    }
    if (options.base_directory) {
      params.base_directory = options.base_directory
    }
    return params
  }

  /**
   * Prepare headers with account_id and profile options.
   * 
   * @param {Object} options - Options
   * @param {string} [options.account_id] - Account ID
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Object} Headers
   */
  _prepareHeaders(options = {}) {
    const headers = {}
    if (options.account_id) {
      headers['X-Account-ID'] = options.account_id
      headers['account-id'] = options.account_id
    }
    if (options.profile_path) {
      headers['X-Profile-Path'] = options.profile_path
      headers['profile-path'] = options.profile_path
    }
    if (options.profile_id) {
      headers['X-Profile-Id'] = options.profile_id
    }
    if (options.base_directory) {
      headers['X-Base-Directory'] = options.base_directory
    }
    return headers
  }

  /**
   * Make GET request with custom headers support.
   * 
   * @param {string} path - Endpoint path
   * @param {Object} [params] - Query parameters
   * @param {Object} [headers] - Custom headers
   * @returns {Promise<*>}
   */
  async _getWithHeaders(path = '', params = {}, headers = {}) {
    try {
      console.log(`[feedService] _getWithHeaders: Calling GET ${this.basePath}${path}`, { params, headers })
      const response = await this.client.get(
        `${this.basePath}${path}`,
        { params, headers }
      )
      console.log(`[feedService] _getWithHeaders: Successfully received response from ${this.basePath}${path}`, {
        status: response?.status,
        hasData: !!response?.data,
        dataKeys: response?.data ? Object.keys(response.data) : []
      })
      return response
    } catch (error) {
      console.error(`[feedService] _getWithHeaders: Error calling ${this.basePath}${path}`, {
        message: error.message,
        code: error.code,
        response: error.response?.data,
        status: error.response?.status
      })
      this._handleError('GET', path, error)
      throw error
    }
  }

  /**
   * Make POST request with custom headers support.
   * 
   * @param {string} path - Endpoint path
   * @param {Object} [data] - Request body
   * @param {Object} [params] - Query parameters
   * @param {Object} [headers] - Custom headers
   * @param {number} [timeout] - Request timeout in milliseconds (optional, overrides default)
   * @returns {Promise<*>}
   */
  async _postWithHeaders(path = '', data = {}, params = {}, headers = {}, timeout = null) {
    try {
      const config = { params, headers }
      // Override timeout if provided
      if (timeout !== null) {
        config.timeout = timeout
      }
      const response = await this.client.post(
        `${this.basePath}${path}`,
        data,
        config
      )
      return response
    } catch (error) {
      this._handleError('POST', path, error)
      throw error
    }
  }

  /**
   * Make DELETE request with custom headers support.
   * 
   * @param {string} path - Endpoint path
   * @param {Object} [params] - Query parameters
   * @param {Object} [headers] - Custom headers
   * @returns {Promise<*>}
   */
  async _deleteWithHeaders(path = '', params = {}, headers = {}) {
    try {
      const response = await this.client.delete(
        `${this.basePath}${path}`,
        { params, headers }
      )
      return response
    } catch (error) {
      this._handleError('DELETE', path, error)
      throw error
    }
  }

  /**
   * Get feed items với filters.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID for browser context
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @param {Object} [options.filters] - Feed filters
   * @returns {Promise<Object>} API response with feed data
   */
  async getFeed(options = {}) {
    // #region agent log
    const params = this._prepareParams(options)
    if (options.filters) {
      Object.assign(params, options.filters)
    }
    fetch('http://127.0.0.1:7250/ingest/f9f4fb4d-fc87-4720-b414-d5b7f9def9b2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'feedService.js:getFeed',message:'getFeed API call',data:{account_id:params.account_id,profile_path:params.profile_path,allParams:params},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    const headers = this._prepareHeaders(options)
    return this._getWithHeaders('', params, headers)
  }

  /**
   * Get một post cụ thể theo ID.
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID for browser context
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response with post data
   */
  async getFeedPost(postId, options = {}) {
    const params = this._prepareParams(options)
    const headers = this._prepareHeaders(options)
    return this._getWithHeaders(`/${postId}`, params, headers)
  }

  /**
   * Get posts từ user profile.
   * 
   * @param {string} username - Username (with or without @)
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID for browser context
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @param {Object} [options.filters] - Feed filters
   * @returns {Promise<Object>} API response with user posts
   */
  async getUserPosts(username, options = {}) {
    const params = this._prepareParams(options)
    if (options.filters) {
      Object.assign(params, options.filters)
    }
    const headers = this._prepareHeaders(options)
    const usernameClean = username.replace(/^@/, '')
    return this._getWithHeaders(`/user/${usernameClean}/posts`, params, headers)
  }

  /**
   * Force refresh feed (bypass cache).
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID for browser context
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @param {Object} [options.filters] - Feed filters
   * @returns {Promise<Object>} API response with refreshed feed data
   */
  async refreshFeed(options = {}) {
    const data = {}
    if (options.filters) {
      Object.assign(data, options.filters)
    }
    const params = this._prepareParams(options)
    const headers = this._prepareHeaders(options)
    return this._postWithHeaders('/refresh', data, params, headers)
  }

  /**
   * Clear cache.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.username] - Username to clear cache for
   * @param {string} [options.account_id] - Account ID for session isolation
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async clearCache(options = {}) {
    const params = this._prepareParams(options)
    if (options.username) {
      params.username = options.username.replace(/^@/, '')
    }
    const headers = this._prepareHeaders(options)
    return this._deleteWithHeaders('/cache', params, headers)
  }

  /**
   * Get feed statistics.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID for session isolation
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response with stats
   */
  async getStats(options = {}) {
    // #region agent log
    const stackTrace = new Error().stack
    console.error('[DEBUG] feedService.getStats CALLED - THIS WILL CALL QRTOOLS API AND OPEN BROWSER', {
      options,
      stackTrace: stackTrace?.split('\n').slice(0,15).join(' | ')
    })
    fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'feedService.js:getStats',message:'getStats CALLED - THIS WILL OPEN BROWSER',data:{options,stackTrace:stackTrace?.split('\n').slice(0,15).join(' | ')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'K'})}).catch(()=>{});
    // #endregion
    
    // CRITICAL: Global guard - check if caller wants to skip stats (e.g., when on saved-feed tab)
    // This is a defensive check in case the wrapper didn't catch the call
    if (options.skipIfSavedFeed === true) {
      console.error('[DEBUG] feedService.getStats BLOCKED by skipIfSavedFeed flag')
      fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'feedService.js:getStats',message:'BLOCKED by skipIfSavedFeed flag',data:{options},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'K'})}).catch(()=>{});
      return {
        cache: { enabled: false, hasData: false },
        server: { qrtools_available: false },
        note: "Stats loading blocked - skipIfSavedFeed flag set"
      }
    }
    
    const params = this._prepareParams(options)
    const headers = this._prepareHeaders(options)
    // #region agent log
    console.error('[DEBUG] feedService.getStats about to make HTTP request to /stats - THIS WILL OPEN BROWSER')
    fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'feedService.js:getStats',message:'About to call _getWithHeaders /stats',data:{params,headers},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'K'})}).catch(()=>{});
    // #endregion
    return this._getWithHeaders('/stats', params, headers)
  }

  /**
   * Get Qrtools configuration.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID (optional, for logging)
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response with config
   */
  async getConfig(options = {}) {
    const params = this._prepareParams(options)
    const headers = this._prepareHeaders(options)
    return this._getWithHeaders('/config', params, headers)
  }

  /**
   * Get health check.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID (optional, for logging)
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response with health status
   */
  async getHealth(options = {}) {
    const params = this._prepareParams(options)
    const headers = this._prepareHeaders(options)
    return this._getWithHeaders('/health', params, headers)
  }

  // Post Interactions
  /**
   * Like a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Additional options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async likePost(postId, accountId, options = {}) {
    const { profile_path, profile_dir, profile_id, base_directory, ...restOptions } = options
    const params = this._prepareParams({ account_id: accountId, profile_path, profile_dir, profile_id, base_directory })
    const headers = this._prepareHeaders({ account_id: accountId, profile_path, profile_id, base_directory })
    const data = restOptions
    return this._postWithHeaders(`/post/${postId}/like`, data, params, headers)
  }

  /**
   * Unlike a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async unlikePost(postId, accountId, options = {}) {
    const params = this._prepareParams({ account_id: accountId, ...options })
    const headers = this._prepareHeaders({ account_id: accountId, ...options })
    return this._deleteWithHeaders(`/post/${postId}/like`, params, headers)
  }

  /**
   * Comment on a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {string} comment - Comment text
   * @param {Object} [options] - Additional options (username, shortcode, postUrl, profile_path, etc.)
   * @returns {Promise<Object>} API response
   */
  async commentOnPost(postId, accountId, comment, options = {}) {
    const { profile_path, profile_dir, profile_id, base_directory, ...restOptions } = options
    const params = this._prepareParams({ account_id: accountId, profile_path, profile_dir, profile_id, base_directory })
    const headers = this._prepareHeaders({ account_id: accountId, profile_path, profile_id, base_directory })
    const data = { comment, ...restOptions }
    return this._postWithHeaders(`/post/${postId}/comment`, data, params, headers)
  }

  /**
   * Repost a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Additional options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async repostPost(postId, accountId, options = {}) {
    const { profile_path, profile_dir, profile_id, base_directory, ...restOptions } = options
    const params = this._prepareParams({ account_id: accountId, profile_path, profile_dir, profile_id, base_directory, ...restOptions })
    const headers = this._prepareHeaders({ account_id: accountId, profile_path, profile_id, base_directory })
    const data = {}
    return this._postWithHeaders(`/post/${postId}/repost`, data, params, headers)
  }

  /**
   * Quote a post with comment.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {string} quote - Quote text
   * @param {Object} [options] - Additional options (username, shortcode, postUrl, profile_path, etc.)
   * @returns {Promise<Object>} API response
   */
  async quotePost(postId, accountId, quote, options = {}) {
    const { profile_path, profile_dir, profile_id, base_directory, ...restOptions } = options
    const params = this._prepareParams({ account_id: accountId, profile_path, profile_dir, profile_id, base_directory })
    const headers = this._prepareHeaders({ account_id: accountId, profile_path, profile_id, base_directory })
    const data = { quote, ...restOptions }
    return this._postWithHeaders(`/post/${postId}/quote`, data, params, headers)
  }

  /**
   * Unrepost a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async unrepostPost(postId, accountId, options = {}) {
    const params = this._prepareParams({ account_id: accountId, ...options })
    const headers = this._prepareHeaders({ account_id: accountId, ...options })
    return this._deleteWithHeaders(`/post/${postId}/repost`, params, headers)
  }

  /**
   * Get post interaction status.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async getPostInteractions(postId, accountId, options = {}) {
    const params = this._prepareParams({ account_id: accountId, ...options })
    const headers = this._prepareHeaders({ account_id: accountId, ...options })
    return this._getWithHeaders(`/post/${postId}/interactions`, params, headers)
  }

  /**
   * Get repost status.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Additional options (username, shortcode, postUrl, profile_path, etc.)
   * @returns {Promise<Object>} API response
   */
  async getRepostStatus(postId, accountId, options = {}) {
    const params = this._prepareParams({ account_id: accountId, ...options })
    const headers = this._prepareHeaders({ account_id: accountId, ...options })
    return this._getWithHeaders(`/post/${postId}/repost-status`, params, headers)
  }

  /**
   * Share a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} accountId - Account ID
   * @param {string} [platform='copy'] - Platform for share
   * @param {Object} [options] - Options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async sharePost(postId, accountId, platform = 'copy', options = {}) {
    const params = this._prepareParams({ account_id: accountId, platform, ...options })
    const headers = this._prepareHeaders({ account_id: accountId, ...options })
    return this._postWithHeaders(`/post/${postId}/share`, {}, params, headers)
  }

  // User Interactions
  /**
   * Follow a user.
   * 
   * @param {string} username - Username (with or without @)
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async followUser(username, accountId, options = {}) {
    const usernameClean = username.replace(/^@/, '')
    const params = this._prepareParams({ account_id: accountId, ...options })
    const headers = this._prepareHeaders({ account_id: accountId, ...options })
    return this._postWithHeaders(`/user/${usernameClean}/follow`, {}, params, headers)
  }

  /**
   * Unfollow a user.
   * 
   * @param {string} username - Username (with or without @)
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async unfollowUser(username, accountId, options = {}) {
    const usernameClean = username.replace(/^@/, '')
    const params = this._prepareParams({ account_id: accountId, ...options })
    const headers = this._prepareHeaders({ account_id: accountId, ...options })
    return this._deleteWithHeaders(`/user/${usernameClean}/follow`, params, headers)
  }

  /**
   * Get user follow status.
   * 
   * @param {string} username - Username (with or without @)
   * @param {string} accountId - Account ID
   * @param {Object} [options] - Options
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async getUserFollowStatus(username, accountId, options = {}) {
    const usernameClean = username.replace(/^@/, '')
    const params = this._prepareParams({ account_id: accountId, ...options })
    const headers = this._prepareHeaders({ account_id: accountId, ...options })
    return this._getWithHeaders(`/user/${usernameClean}/follow-status`, params, headers)
  }

  // Feed Browsing
  /**
   * Browse feed and auto comment.
   * 
   * @param {string} accountId - Account ID
   * @param {Object} config - Browse and comment configuration
   * @param {string} [config.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [config.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [config.profile_id] - Profile ID (requires base_directory)
   * @param {string} [config.base_directory] - Base directory for profile_id
   * @param {Object} [config.filter_criteria] - Filter criteria for posts
   * @param {number} [config.max_posts_to_comment] - Max posts to comment
   * @param {boolean} [config.random_selection] - Random selection
   * @param {string[]} [config.comment_templates] - Comment templates
   * @param {number} [config.comment_delay_min] - Min delay between comments (ms)
   * @param {number} [config.comment_delay_max] - Max delay between comments (ms)
   * @param {string} [config.target_url] - Target URL for feed extraction
   * @param {number} [config.max_items] - Max items to extract from feed
   * @returns {Promise<Object>} API response
   */
  async browseAndComment(accountId, config) {
    const { profile_path, profile_dir, profile_id, base_directory, ...restConfig } = config || {}
    const params = this._prepareParams({ account_id: accountId, profile_path, profile_dir, profile_id, base_directory })
    const headers = this._prepareHeaders({ account_id: accountId, profile_path, profile_id, base_directory })
    
    // Helper to clean filter criteria - remove null/undefined/empty/0 values
    // Note: 0 is treated as "no filter" for numeric fields
    const cleanFilterCriteria = (criteria) => {
      if (!criteria) return undefined
      const cleaned = {}
      for (const [key, value] of Object.entries(criteria)) {
        // Skip null, undefined, empty string, and 0 for numeric filters
        if (value !== null && value !== undefined && value !== '' && value !== 0) {
          cleaned[key] = value
        }
      }
      return Object.keys(cleaned).length > 0 ? cleaned : undefined
    }
    
    // Convert to camelCase for API consistency
    const apiConfig = {}
    const cleanedCriteria = cleanFilterCriteria(restConfig.filter_criteria)
    if (cleanedCriteria) {
      apiConfig.filterCriteria = cleanedCriteria
    }
    if (restConfig.max_posts_to_comment !== undefined && restConfig.max_posts_to_comment !== null) {
      apiConfig.maxPostsToComment = restConfig.max_posts_to_comment
    }
    if (restConfig.random_selection !== undefined) {
      apiConfig.randomSelection = restConfig.random_selection
    }
    if (restConfig.comment_templates && restConfig.comment_templates.length > 0) {
      apiConfig.commentTemplates = restConfig.comment_templates
    }
    if (restConfig.comment_delay_min !== undefined && restConfig.comment_delay_min !== null) {
      apiConfig.commentDelayMin = restConfig.comment_delay_min
    }
    if (restConfig.comment_delay_max !== undefined && restConfig.comment_delay_max !== null) {
      apiConfig.commentDelayMax = restConfig.comment_delay_max
    }
    if (restConfig.target_url) {
      apiConfig.targetUrl = restConfig.target_url
    }
    if (restConfig.max_items !== undefined && restConfig.max_items !== null) {
      apiConfig.maxItems = restConfig.max_items
    }
    
    return this._postWithHeaders('/browse-and-comment', apiConfig, params, headers)
  }

  /**
   * Select user from feed and comment on their posts.
   * 
   * @param {string} accountId - Account ID
   * @param {Object} config - Select user and comment configuration
   * @param {string} [config.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [config.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [config.profile_id] - Profile ID (requires base_directory)
   * @param {string} [config.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async selectUserAndComment(accountId, config) {
    const { profile_path, profile_dir, profile_id, base_directory, ...restConfig } = config || {}
    const params = this._prepareParams({ account_id: accountId, profile_path, profile_dir, profile_id, base_directory })
    const headers = this._prepareHeaders({ account_id: accountId, profile_path, profile_id, base_directory })
    // Use 150s timeout (backend has 120s timeout, add buffer)
    return this._postWithHeaders('/select-user-and-comment', restConfig, params, headers, 150000)
  }

  // Profile Management
  /**
   * List all profiles in base directory.
   * 
   * @param {string} baseDirectory - Base directory path on client machine
   * @returns {Promise<Object>} API response with profile list
   */
  async listProfiles(baseDirectory) {
    const params = { base_directory: baseDirectory }
    const headers = { 'X-Base-Directory': baseDirectory }
    return this._getWithHeaders('/profiles', params, headers)
  }

  /**
   * Get profile info by ID.
   * 
   * @param {string} profileId - Profile ID
   * @param {string} baseDirectory - Base directory path on client machine
   * @returns {Promise<Object>} API response with profile info
   */
  async getProfile(profileId, baseDirectory) {
    const params = { base_directory: baseDirectory }
    const headers = { 'X-Base-Directory': baseDirectory }
    return this._getWithHeaders(`/profiles/${profileId}`, params, headers)
  }

  // Authentication
  /**
   * Login to Threads.
   * 
   * @param {string} username - Threads username
   * @param {string} password - Threads password
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID for session isolation
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async login(username, password, options = {}) {
    const params = this._prepareParams(options)
    const headers = this._prepareHeaders(options)
    const data = { username, password }
    return this._postWithHeaders('/login', data, params, headers)
  }

  /**
   * Bulk login multiple accounts.
   * 
   * @param {Object} request - Bulk login request
   * @param {string} request.base_directory - Base directory path on client machine
   * @param {Array} request.accounts - List of accounts to login
   * @param {Object} [request.options] - Bulk login options
   * @returns {Promise<Object>} API response
   */
  async bulkLogin(request) {
    const { base_directory, ...restRequest } = request
    const params = base_directory ? { base_directory } : {}
    const headers = base_directory ? { 'X-Base-Directory': base_directory } : {}
    const data = { ...restRequest }
    if (base_directory) {
      data.base_directory = base_directory
    }
    return this._postWithHeaders('/login/bulk', data, params, headers)
  }

  /**
   * Comment on posts from a user.
   * 
   * @param {string} username - Username (with or without @)
   * @param {string} accountId - Account ID
   * @param {Object} config - Comment posts configuration
   * @param {string} [config.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [config.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [config.profile_id] - Profile ID (requires base_directory)
   * @param {string} [config.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>} API response
   */
  async commentUserPosts(username, accountId, config) {
    const usernameClean = username.replace(/^@/, '')
    const { profile_path, profile_dir, profile_id, base_directory, ...restConfig } = config || {}
    const params = this._prepareParams({ account_id: accountId, profile_path, profile_dir, profile_id, base_directory })
    const headers = this._prepareHeaders({ account_id: accountId, profile_path, profile_id, base_directory })
    return this._postWithHeaders(`/user/${usernameClean}/comment-posts`, restConfig, params, headers)
  }

  /**
   * Get saved feed items from database.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID filter
   * @param {number} [options.limit] - Limit number of results
   * @param {number} [options.offset] - Offset for pagination
   * @param {Object} [options.filters] - Feed filters (min_likes, max_likes, min_replies, etc.)
   * @returns {Promise<Object>} API response with saved feed data
   */
  async getSavedFeed(options = {}) {
    const stackTrace = new Error().stack
    const { account_id, limit, offset } = options
    console.error('[DEBUG] feedService.getSavedFeed CALLED - Database only, NO browser', {
      options,
      stackTrace: stackTrace?.split('\n').slice(0,15).join(' | ')
    })
    fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'feedService.js:getSavedFeed',message:'getSavedFeed CALLED - Database only, NO browser',data:{options,stackTrace:stackTrace?.split('\n').slice(0,15).join(' | ')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'M'})}).catch(()=>{});
    const params = {}
    if (account_id) params.account_id = account_id
    if (limit !== undefined) params.limit = limit
    if (offset !== undefined) params.offset = offset
    // Add filter parameters if provided
    if (options.filters) {
      Object.assign(params, options.filters)
    }
    // #region agent log
    console.error('[DEBUG] feedService.getSavedFeed about to call _getWithHeaders /saved - Database only, NO browser')
    fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'feedService.js:getSavedFeed',message:'About to call _getWithHeaders /saved',data:{params},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'M'})}).catch(()=>{});
    // #endregion
    return this._getWithHeaders('/saved', params, {})
  }

  /**
   * Get history of a post (all fetched_at timestamps).
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID filter
   * @returns {Promise<Object>} API response with post history
   */
  async getPostHistory(postId, options = {}) {
    const { account_id } = options
    const params = {}
    if (account_id) params.account_id = account_id
    return this._getWithHeaders(`/saved/${postId}/history`, params, {})
  }
}

// Export singleton instance
export const feedService = new FeedService()
