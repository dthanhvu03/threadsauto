/**
 * Accounts API service.
 * 
 * Handles all API calls for accounts feature.
 * Uses BaseService for common HTTP methods.
 */

import { BaseService } from '@/core/api/baseService'

/**
 * Accounts service instance.
 * 
 * @class
 * @extends {BaseService}
 */
class AccountsService extends BaseService {
  constructor() {
    super('/accounts')
  }

  /**
   * Get all accounts.
   * 
   * @returns {Promise<Array>} API response with accounts data
   */
  async getAll() {
    return this.get('')
  }

  /**
   * Get account by ID.
   * 
   * @param {string} accountId - Account ID
   * @returns {Promise<Object>} API response with account data
   */
  async getById(accountId) {
    return this.get(`/${accountId}`)
  }

  /**
   * Get account statistics.
   * 
   * @param {string} accountId - Account ID
   * @returns {Promise<Object>} API response with account stats
   */
  async getStats(accountId) {
    return this.get(`/${accountId}/stats`)
  }

  /**
   * Create new account.
   * 
   * @param {Object} accountData - Account creation data
   * @returns {Promise<Object>} API response with created account
   */
  async create(accountData) {
    return this.post('', accountData)
  }

  /**
   * Delete account.
   * 
   * @param {string} accountId - Account ID
   * @returns {Promise<Object>} API response
   */
  async delete(accountId) {
    return this.delete(`/${accountId}`)
  }
}

// Export singleton instance
export const accountsService = new AccountsService()
