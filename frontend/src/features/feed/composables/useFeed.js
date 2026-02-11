/**
 * Feed composable.
 * 
 * Provides business logic and state management for feed feature.
 */

import { ref, computed } from 'vue'
import { feedService } from '../services/feedService'
import { getErrorMessage } from '@/core/utils/errors'

/**
 * Composable for feed feature business logic.
 * 
 * @returns {Object} Composable return object
 */
export function useFeed() {
  const loading = ref(false)  // Keep for backward compatibility
  const loadingStats = ref(false)  // Separate loading state for Check Session
  const loadingFeed = ref(false)  // Separate loading state for Refresh Feed
  const error = ref(null)
  const feedItems = ref([])
  const stats = ref(null)
  const config = ref(null)
  
  // Pagination state
  const currentPage = ref(1)
  const pageSize = ref(20)
  const totalItems = ref(0)
  
  // Filters
  const filters = ref({
    min_likes: null,
    max_likes: null,
    min_replies: null,
    min_reposts: null,
    min_shares: null,
    has_media: null,
    username: null,
    text_contains: null,
    after_timestamp: null,
    before_timestamp: null,
    limit: null
  })
  
  // Account ID
  const accountId = ref(null)
  
  // Profile Path (Browser profile path - client-side, optional)
  const profilePath = ref(null)

  /**
   * Load feed items.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @param {Object} [options.filters] - Feed filters
   * @returns {Promise<void>}
   */
  const loadFeed = async (options = {}) => {
    // #region agent log
    const finalAccountId = options.account_id || accountId.value;
    const finalProfilePath = options.profile_path || profilePath.value;
    fetch('http://127.0.0.1:7250/ingest/f9f4fb4d-fc87-4720-b414-d5b7f9def9b2',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useFeed.js:loadFeed',message:'loadFeed called',data:{accountIdFromOptions:options.account_id,accountIdFromRef:accountId.value,finalAccountId,profilePath:finalProfilePath},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    loadingFeed.value = true
    loading.value = true  // For backward compatibility
    error.value = null

    try {
      const response = await feedService.getFeed({
        account_id: finalAccountId,
        profile_path: finalProfilePath,
        profile_dir: options.profile_dir,
        profile_id: options.profile_id,
        base_directory: options.base_directory,
        filters: options.filters || filters.value
      })
      
      if (response && response.data) {
        feedItems.value = response.data
      } else if (Array.isArray(response)) {
        feedItems.value = response
      } else {
        feedItems.value = []
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      feedItems.value = []
      throw err
    } finally {
      loadingFeed.value = false
      loading.value = false  // For backward compatibility
    }
  }

  /**
   * Load user posts.
   * 
   * @param {string} username - Username
   * @param {Object} [options] - Options
   * @returns {Promise<void>}
   */
  const loadUserPosts = async (username, options = {}) => {
    loading.value = true
    error.value = null

    try {
      const response = await feedService.getUserPosts(username, {
        account_id: options.account_id || accountId.value,
        profile_path: options.profile_path || profilePath.value,
        filters: options.filters || filters.value
      })
      
      if (response && response.data) {
        feedItems.value = response.data
      } else if (Array.isArray(response)) {
        feedItems.value = response
      } else {
        feedItems.value = []
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      feedItems.value = []
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Refresh feed.
   * 
   * @param {Object} [options] - Options
   * @returns {Promise<void>}
   */
  const refreshFeed = async (options = {}) => {
    loading.value = true
    error.value = null

    try {
      const response = await feedService.refreshFeed({
        account_id: options.account_id || accountId.value,
        profile_path: options.profile_path || profilePath.value,
        filters: options.filters || filters.value
      })
      
      if (response && response.data) {
        feedItems.value = response.data
      } else if (Array.isArray(response)) {
        feedItems.value = response
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Load stats.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID for session isolation
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<void>}
   */
  const loadStats = async (options = {}) => {
    // #region agent log
    const stackTrace = new Error().stack
    console.error('[DEBUG] useFeed.loadStats CALLED - THIS WILL CALL QRTOOLS AND OPEN BROWSER', {
      options,
      accountId: accountId.value,
      profilePath: profilePath.value,
      stackTrace: stackTrace?.split('\n').slice(0,15).join(' | ')
    })
    fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useFeed.js:loadStats',message:'loadStats CALLED - THIS WILL OPEN BROWSER',data:{options,accountId:accountId.value,profilePath:profilePath.value,stackTrace:stackTrace?.split('\n').slice(0,15).join(' | ')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'J'})}).catch(()=>{});
    // #endregion
    loadingStats.value = true
    loading.value = true  // For backward compatibility
    error.value = null

    try {
      const finalAccountId = options.account_id || accountId.value
      const finalProfilePath = options.profile_path || profilePath.value
      // #region agent log
      console.error('[DEBUG] useFeed.loadStats about to call feedService.getStats - THIS WILL OPEN BROWSER')
      fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useFeed.js:loadStats',message:'About to call feedService.getStats',data:{finalAccountId,finalProfilePath},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'J'})}).catch(()=>{});
      // #endregion
      const response = await feedService.getStats({
        account_id: finalAccountId,
        profile_path: finalProfilePath,
        profile_dir: options.profile_dir,
        profile_id: options.profile_id,
        base_directory: options.base_directory
      })
      stats.value = response.data || response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      loadingStats.value = false
      loading.value = false  // For backward compatibility
    }
  }

  /**
   * Load config.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID (optional, for logging)
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<void>}
   */
  const loadConfig = async (options = {}) => {
    loading.value = true
    error.value = null

    try {
      const finalAccountId = options.account_id || accountId.value
      const finalProfilePath = options.profile_path || profilePath.value
      const response = await feedService.getConfig({
        account_id: finalAccountId,
        profile_path: finalProfilePath,
        profile_dir: options.profile_dir,
        profile_id: options.profile_id,
        base_directory: options.base_directory
      })
      config.value = response.data || response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Load health check.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID (optional, for logging)
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>}
   */
  const loadHealth = async (options = {}) => {
    loading.value = true
    error.value = null

    try {
      const finalAccountId = options.account_id || accountId.value
      const finalProfilePath = options.profile_path || profilePath.value
      const response = await feedService.getHealth({
        account_id: finalAccountId,
        profile_path: finalProfilePath,
        profile_dir: options.profile_dir,
        profile_id: options.profile_id,
        base_directory: options.base_directory
      })
      return response.data || response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
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
   * @returns {Promise<void>}
   */
  const clearCache = async (options = {}) => {
    loading.value = true
    error.value = null

    try {
      const finalAccountId = options.account_id || accountId.value
      const finalProfilePath = options.profile_path || profilePath.value
      await feedService.clearCache({
        username: options.username,
        account_id: finalAccountId,
        profile_path: finalProfilePath,
        profile_dir: options.profile_dir,
        profile_id: options.profile_id,
        base_directory: options.base_directory
      })
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Apply filters.
   * 
   * @param {Object} newFilters - New filter values
   */
  const applyFilters = (newFilters) => {
    Object.assign(filters.value, newFilters)
  }

  /**
   * Reset filters.
   */
  const resetFilters = () => {
    filters.value = {
      min_likes: null,
      max_likes: null,
      min_replies: null,
      min_reposts: null,
      min_shares: null,
      has_media: null,
      username: null,
      text_contains: null,
      after_timestamp: null,
      before_timestamp: null,
      limit: null
    }
  }

  // Post Interactions
  /**
   * Like a post.
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const likePost = async (postId, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.likePost(postId, options.account_id || accountId.value, {
      ...options,
      profile_path: finalProfilePath
    })
  }

  /**
   * Unlike a post.
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const unlikePost = async (postId, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.unlikePost(postId, options.account_id || accountId.value, finalProfilePath)
  }

  /**
   * Comment on a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} comment - Comment text
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const commentOnPost = async (postId, comment, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.commentOnPost(postId, options.account_id || accountId.value, comment, {
      ...options,
      profile_path: finalProfilePath
    })
  }

  /**
   * Repost a post.
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const repostPost = async (postId, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.repostPost(postId, options.account_id || accountId.value, {
      ...options,
      profile_path: finalProfilePath
    })
  }

  /**
   * Quote a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} quote - Quote text
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const quotePost = async (postId, quote, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.quotePost(postId, options.account_id || accountId.value, quote, {
      ...options,
      profile_path: finalProfilePath
    })
  }

  /**
   * Get feed post by ID.
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>}
   */
  const getFeedPost = async (postId, options = {}) => {
    try {
      const finalAccountId = options.account_id || accountId.value
      const finalProfilePath = options.profile_path || profilePath.value
      const response = await feedService.getFeedPost(postId, {
        account_id: finalAccountId,
        profile_path: finalProfilePath,
        profile_dir: options.profile_dir,
        profile_id: options.profile_id,
        base_directory: options.base_directory
      })
      return response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    }
  }

  /**
   * Unrepost a post.
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const unrepostPost = async (postId, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.unrepostPost(postId, options.account_id || accountId.value, finalProfilePath)
  }

  /**
   * Get post interactions.
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const getPostInteractions = async (postId, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.getPostInteractions(postId, options.account_id || accountId.value, finalProfilePath)
  }

  /**
   * Get repost status.
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const getRepostStatus = async (postId, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.getRepostStatus(postId, options.account_id || accountId.value, {
      ...options,
      profile_path: finalProfilePath
    })
  }

  /**
   * Share a post.
   * 
   * @param {string} postId - Post ID
   * @param {string} [platform='copy'] - Platform
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const sharePost = async (postId, platform = 'copy', options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.sharePost(postId, options.account_id || accountId.value, platform, finalProfilePath)
  }

  // User Interactions
  /**
   * Follow a user.
   * 
   * @param {string} username - Username
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const followUser = async (username, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.followUser(username, options.account_id || accountId.value, finalProfilePath)
  }

  /**
   * Unfollow a user.
   * 
   * @param {string} username - Username
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const unfollowUser = async (username, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.unfollowUser(username, options.account_id || accountId.value, finalProfilePath)
  }

  /**
   * Get user follow status.
   * 
   * @param {string} username - Username
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const getUserFollowStatus = async (username, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.getUserFollowStatus(username, options.account_id || accountId.value, finalProfilePath)
  }

  // Feed Browsing
  /**
   * Browse and comment.
   * 
   * @param {Object} config - Browse and comment configuration
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const browseAndComment = async (config, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    const configWithProfilePath = {
      ...config,
      profile_path: finalProfilePath
    }
    return feedService.browseAndComment(options.account_id || accountId.value, configWithProfilePath)
  }

  /**
   * Select user and comment.
   * 
   * @param {Object} config - Select user and comment configuration
   * @param {Object} [options] - Options
   * @returns {Promise<Object>}
   */
  const selectUserAndComment = async (config, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalProfilePath = options.profile_path || profilePath.value
    const configWithProfilePath = {
      ...config,
      profile_path: finalProfilePath
    }
    return feedService.selectUserAndComment(options.account_id || accountId.value, configWithProfilePath)
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
   * @returns {Promise<Object>}
   */
  const login = async (username, password, options = {}) => {
    const finalAccountId = options.account_id || accountId.value
    const finalProfilePath = options.profile_path || profilePath.value
    return feedService.login(username, password, {
      account_id: finalAccountId,
      profile_path: finalProfilePath,
      profile_dir: options.profile_dir,
      profile_id: options.profile_id,
      base_directory: options.base_directory
    })
  }

  /**
   * List all profiles in base directory.
   * 
   * @param {string} baseDirectory - Base directory path on client machine
   * @returns {Promise<Object>}
   */
  const listProfiles = async (baseDirectory) => {
    loading.value = true
    error.value = null

    try {
      const response = await feedService.listProfiles(baseDirectory)
      return response.data || response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Get profile info by ID.
   * 
   * @param {string} profileId - Profile ID
   * @param {string} baseDirectory - Base directory path on client machine
   * @returns {Promise<Object>}
   */
  const getProfile = async (profileId, baseDirectory) => {
    loading.value = true
    error.value = null

    try {
      const response = await feedService.getProfile(profileId, baseDirectory)
      return response.data || response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Bulk login multiple accounts.
   * 
   * @param {Object} request - Bulk login request
   * @param {string} request.base_directory - Base directory path on client machine
   * @param {Array} request.accounts - List of accounts to login
   * @param {Object} [request.options] - Bulk login options
   * @returns {Promise<Object>}
   */
  const bulkLogin = async (request) => {
    loading.value = true
    error.value = null

    try {
      const response = await feedService.bulkLogin(request)
      return response.data || response
    } catch (err) {
      error.value = getErrorMessage(err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Comment on posts from a user.
   * 
   * @param {string} username - Username (with or without @)
   * @param {Object} config - Comment posts configuration
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID
   * @param {string} [options.profile_path] - Browser profile path (client-side, optional)
   * @param {string} [options.profile_dir] - Browser profile directory (alias for profile_path)
   * @param {string} [options.profile_id] - Profile ID (requires base_directory)
   * @param {string} [options.base_directory] - Base directory for profile_id
   * @returns {Promise<Object>}
   */
  const commentUserPosts = async (username, config, options = {}) => {
    if (!accountId.value && !options.account_id) {
      throw new Error('Account ID is required')
    }
    const finalAccountId = options.account_id || accountId.value
    const finalProfilePath = options.profile_path || profilePath.value
    const configWithProfile = {
      ...config,
      profile_path: finalProfilePath,
      profile_dir: options.profile_dir,
      profile_id: options.profile_id,
      base_directory: options.base_directory
    }
    return feedService.commentUserPosts(username, finalAccountId, configWithProfile)
  }

  /**
   * Load saved feed items from database.
   * 
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID filter
   * @param {number} [options.limit] - Limit number of results
   * @param {number} [options.offset] - Offset for pagination
   * @param {Object} [options.filters] - Feed filters (min_likes, max_likes, min_replies, etc.)
   * @returns {Promise<Object>} Object with items and metadata { items, total, filtered_total }
   */
  const loadSavedFeed = async (options = {}) => {
    const stackTrace = new Error().stack
    console.log('[useFeed] loadSavedFeed: Starting - this should ONLY call /api/feed/saved (database), NO Qrtools')
    console.error('[DEBUG] useFeed.loadSavedFeed CALLED - Database only, NO browser', {
      options,
      accountId: accountId.value,
      stackTrace: stackTrace?.split('\n').slice(0,15).join(' | ')
    })
    fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useFeed.js:loadSavedFeed',message:'loadSavedFeed CALLED - Database only, NO browser',data:{options,accountId:accountId.value,stackTrace:stackTrace?.split('\n').slice(0,15).join(' | ')},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'L'})}).catch(()=>{});
    loading.value = true
    error.value = null

    try {
      // #region agent log
      console.error('[DEBUG] useFeed.loadSavedFeed about to call feedService.getSavedFeed - Database only, NO browser')
      fetch('http://127.0.0.1:7251/ingest/51f0fb7e-17cd-490d-9237-943abd387122',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'useFeed.js:loadSavedFeed',message:'About to call feedService.getSavedFeed',data:{accountId:options.account_id || accountId.value},timestamp:Date.now(),sessionId:'debug-session',runId:'run1',hypothesisId:'L'})}).catch(()=>{});
      // #endregion
      const response = await feedService.getSavedFeed({
        account_id: options.account_id || accountId.value,
        limit: options.limit || 100,
        offset: options.offset || 0,
        filters: options.filters
      })
      console.log('[useFeed] loadSavedFeed: Successfully received response from /api/feed/saved', response)
      
      // Parse response - handle different response structures
      // Expected structure: { success: true, data: { success: true, data: [...], meta: {...} } }
      let items = []
      
      if (response && response.data) {
        const responseData = response.data
        
        // Case 1: response.data is the FeedResponse object with nested data
        // Structure: { success: true, data: [...], meta: {...}, timestamp: "..." }
        if (responseData.data && Array.isArray(responseData.data)) {
          items = responseData.data
          console.log(`[useFeed] loadSavedFeed: Found ${items.length} items in response.data.data (FeedResponse structure)`)
        }
        // Case 2: response.data is directly an array
        // Structure: [...]
        else if (Array.isArray(responseData)) {
          items = responseData
          console.log(`[useFeed] loadSavedFeed: Found ${items.length} items in response.data (direct array)`)
        }
        // Case 3: response.data is an object with nested data property
        // Structure: { data: [...] }
        else if (responseData.data && Array.isArray(responseData.data)) {
          items = responseData.data
          console.log(`[useFeed] loadSavedFeed: Found ${items.length} items in response.data.data (nested)`)
        }
        else {
          console.warn('[useFeed] loadSavedFeed: Unexpected response structure', {
            response,
            responseData,
            responseDataType: typeof responseData,
            isArray: Array.isArray(responseData),
            hasData: responseData && 'data' in responseData
          })
        }
      } else {
        console.warn('[useFeed] loadSavedFeed: No response.data found', response)
      }
      
      feedItems.value = items
      console.log(`[useFeed] loadSavedFeed: Set feedItems.value to ${feedItems.value.length} items`)
      
      // Extract metadata from response
      // Response structure after axios interceptor:
      // - If array: { data: [...], _meta: {...}, _pagination: {...} }
      // - If object: { ...data, _meta: {...}, _pagination: {...} }
      let meta = null
      if (response && response.data) {
        // Check for _meta (from axios interceptor)
        if (response._meta) {
          meta = response._meta
        }
        // Check for response.data.meta (FeedResponse structure before interceptor)
        else if (response.data.meta) {
          meta = response.data.meta
        }
        // Check for response.data._meta (if data is object)
        else if (response.data._meta) {
          meta = response.data._meta
        }
        // Also check if response.data itself is the FeedResponse
        else if (response.data.success && response.data.meta) {
          meta = response.data.meta
        }
      }
      
      if (meta) {
        totalItems.value = meta.total || items.length
        console.log(`[useFeed] loadSavedFeed: Pagination meta extracted:`, {
          total: meta.total,
          filtered_total: meta.filtered_total,
          count: meta.count,
          limit: meta.limit,
          offset: meta.offset,
          has_more: meta.has_more,
          source: meta.source
        })
      } else {
        // Fallback: use items length if no meta
        console.warn(`[useFeed] loadSavedFeed: No metadata found in response. Response structure:`, {
          hasResponse: !!response,
          hasResponseData: !!(response && response.data),
          responseDataKeys: response?.data ? Object.keys(response.data) : [],
          responseStructure: JSON.stringify(response).substring(0, 500)
        })
        totalItems.value = items.length
      }
      
      // Return metadata for use in FeedExplorer
      // If filtered_total is not provided, it means no filters were applied, so it equals total
      const total = meta?.total || items.length
      const filtered_total = meta?.filtered_total !== undefined ? meta.filtered_total : total
      
      console.log(`[useFeed] loadSavedFeed: Returning metadata:`, {
        total,
        filtered_total,
        items_count: items.length,
        has_meta: !!meta
      })
      
      return {
        items,
        total,
        filtered_total,
        meta
      }
      
      if (items.length === 0) {
        console.warn(`[useFeed] loadSavedFeed: No items found in response`)
        console.warn(`[useFeed] loadSavedFeed: Response structure:`, {
          response,
          responseData: response?.data,
          hasData: response?.data?.data,
          isArray: Array.isArray(response?.data?.data)
        })
      }
    } catch (err) {
      error.value = getErrorMessage(err)
      feedItems.value = []
      
      // Log detailed error information for debugging
      console.error('[useFeed] loadSavedFeed: Error details:', {
        message: err.message,
        code: err.code,
        response: err.response,
        request: err.request,
        config: err.config
      })
      
      // If it's a network error, provide helpful message
      if (err.message?.includes('Network error') || err.message?.includes('Cannot connect')) {
        console.error('[useFeed] loadSavedFeed: Backend API is not reachable')
        console.error('[useFeed] loadSavedFeed: Please ensure backend server is running')
        console.error('[useFeed] loadSavedFeed: Expected endpoint:', err.config?.baseURL + err.config?.url)
      }
      
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Load post history (all fetched_at timestamps).
   * 
   * @param {string} postId - Post ID
   * @param {Object} [options] - Options
   * @param {string} [options.account_id] - Account ID filter
   * @returns {Promise<Array>} Post history array
   */
  const loadPostHistory = async (postId, options = {}) => {
    try {
      const response = await feedService.getPostHistory(postId, {
        account_id: options.account_id || accountId.value
      })
      
      if (response && response.data) {
        return response.data
      }
      return []
    } catch (err) {
      error.value = getErrorMessage(err)
      return []
    }
  }

  return {
    // State
    loading,
    loadingStats,  // Separate loading state for Check Session
    loadingFeed,   // Separate loading state for Refresh Feed
    error,
    feedItems,
    stats,
    config,
    filters,
    accountId,
    profilePath,
    
    // Pagination state
    currentPage,
    pageSize,
    totalItems,
    
    // Methods
    loadFeed,
    loadUserPosts,
    loadSavedFeed,
    loadPostHistory,
    refreshFeed,
    loadStats,
    loadConfig,
    loadHealth,
    clearCache,
    applyFilters,
    resetFilters,
    
    // Post Interactions
    likePost,
    unlikePost,
    commentOnPost,
    repostPost,
    quotePost,
    unrepostPost,
    getPostInteractions,
    getRepostStatus,
    sharePost,
    
    // User Interactions
    followUser,
    unfollowUser,
    getUserFollowStatus,
    
    // Feed Browsing
    browseAndComment,
    selectUserAndComment,
    
    // Feed Post
    getFeedPost,
    
    // Authentication
    login,
    
    // Profile Management
    listProfiles,
    getProfile,
    bulkLogin,
    
    // User Comment Posts
    commentUserPosts
  }
}
