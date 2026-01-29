/**
 * Base service class.
 * 
 * Provides common patterns for API service classes.
 * All feature services should extend this class or use similar patterns.
 */

import apiClient from './client'
import { ApiError } from './types'

/**
 * Base service class.
 * 
 * @class
 */
export class BaseService {
  /**
   * Create base service.
   * 
   * @param {string} basePath - Base path for API endpoints (e.g., '/jobs')
   */
  constructor(basePath) {
    this.basePath = basePath
    this.client = apiClient
  }

  /**
   * GET request.
   * 
   * @param {string} path - Endpoint path (relative to basePath)
   * @param {Object} [params] - Query parameters
   * @returns {Promise<*>}
   */
  async get(path = '', params = {}) {
    try {
      // apiClient interceptor already returns data directly
      const response = await this.client.get(
        `${this.basePath}${path}`,
        { params }
      )
      return response
    } catch (error) {
      this._handleError('GET', path, error)
      throw error
    }
  }

  /**
   * POST request.
   * 
   * @param {string} path - Endpoint path (relative to basePath)
   * @param {Object} [data] - Request body
   * @returns {Promise<*>}
   */
  async post(path = '', data = {}) {
    try {
      // apiClient interceptor already returns data directly
      const response = await this.client.post(
        `${this.basePath}${path}`,
        data
      )
      return response
    } catch (error) {
      this._handleError('POST', path, error)
      throw error
    }
  }

  /**
   * PUT request.
   * 
   * @param {string} path - Endpoint path (relative to basePath)
   * @param {Object} [data] - Request body
   * @returns {Promise<*>}
   */
  async put(path = '', data = {}) {
    try {
      // apiClient interceptor already returns data directly
      const response = await this.client.put(
        `${this.basePath}${path}`,
        data
      )
      return response
    } catch (error) {
      this._handleError('PUT', path, error)
      throw error
    }
  }

  /**
   * DELETE request.
   * 
   * @param {string} path - Endpoint path (relative to basePath)
   * @returns {Promise<*>}
   */
  async delete(path = '') {
    try {
      // apiClient interceptor already returns data directly
      const response = await this.client.delete(
        `${this.basePath}${path}`
      )
      return response
    } catch (error) {
      this._handleError('DELETE', path, error)
      throw error
    }
  }

  /**
   * Handle error (can be overridden by subclasses).
   * 
   * @param {string} method - HTTP method
   * @param {string} path - Endpoint path
   * @param {Error} error - Error object
   * @protected
   */
  _handleError(method, path, error) {
    // Log error or perform common error handling
    console.error(`[${this.basePath}] ${method} ${path} failed:`, error)
  }
}
