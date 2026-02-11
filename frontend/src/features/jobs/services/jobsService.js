/**
 * Jobs API service.
 * 
 * Handles all API calls for jobs feature.
 * Uses BaseService for common HTTP methods.
 */

import { BaseService } from '@/core/api/baseService'

/**
 * Jobs service instance.
 * 
 * @class
 * @extends {BaseService}
 */
class JobsService extends BaseService {
  constructor() {
    super('/jobs')
  }

  /**
   * Get all jobs with optional filters and pagination.
   * 
   * @param {Object} [filters] - Filter options
   * @param {string} [filters.account_id] - Filter by account ID
   * @param {string} [filters.status] - Filter by status
   * @param {string} [filters.platform] - Filter by platform
   * @param {string} [filters.scheduled_from] - Filter by scheduled from date (YYYY-MM-DD)
   * @param {string} [filters.scheduled_to] - Filter by scheduled to date (YYYY-MM-DD)
   * @param {number} [filters.page] - Page number (1-based)
   * @param {number} [filters.limit] - Items per page
   * @param {boolean} [filters.reload] - Reload jobs from storage
   * @returns {Promise<Object>} API response with jobs data and pagination
   */
  async getAll(filters = {}) {
    const params = {}
    
    // Always include all provided params (don't skip falsy values that are explicitly set)
    if (filters.account_id !== undefined && filters.account_id !== null && filters.account_id !== '') {
      params.account_id = filters.account_id
    }
    if (filters.status !== undefined && filters.status !== null && filters.status !== '') {
      params.status = filters.status
    }
    if (filters.platform !== undefined && filters.platform !== null && filters.platform !== '') {
      params.platform = filters.platform
    }
    if (filters.scheduled_from !== undefined && filters.scheduled_from !== null && filters.scheduled_from !== '') {
      params.scheduled_from = filters.scheduled_from
    }
    if (filters.scheduled_to !== undefined && filters.scheduled_to !== null && filters.scheduled_to !== '') {
      params.scheduled_to = filters.scheduled_to
    }
    if (filters.page !== undefined && filters.page !== null) {
      params.page = filters.page
    }
    if (filters.limit !== undefined && filters.limit !== null) {
      params.limit = filters.limit
    }
    if (filters.reload !== undefined) {
      params.reload = filters.reload
    }
    
    const result = await this.get('', params)
    return result
  }

  /**
   * Get job by ID.
   * 
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>} API response with job data
   */
  async getById(jobId) {
    return this.get(`/${jobId}`)
  }

  /**
   * Create new job.
   * 
   * @param {JobCreateData} jobData - Job creation data
   * @returns {Promise<Object>} API response with created job
   */
  async create(jobData) {
    return this.post('', jobData)
  }

  /**
   * Update job.
   * 
   * @param {string} jobId - Job ID
   * @param {JobUpdateData} jobData - Updated job data
   * @returns {Promise<Object>} API response with updated job
   */
  async update(jobId, jobData) {
    return this.put(`/${jobId}`, jobData)
  }

  /**
   * Delete job.
   * 
   * @param {string} jobId - Job ID
   * @returns {Promise<Object>} API response
   */
  async delete(jobId) {
    try {
      // Call parent class delete method (HTTP DELETE)
      const result = await super.delete(`/${jobId}`)
      return result
    } catch (error) {
      throw error
    }
  }

  /**
   * Get job statistics.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @returns {Promise<Object>} API response with statistics
   */
  async getStats(accountId = null) {
    const params = {}
    if (accountId) params.account_id = accountId
    
    return this.get('/stats/summary', params)
  }
}

// Export singleton instance
export const jobsService = new JobsService()
