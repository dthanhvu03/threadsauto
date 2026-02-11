/**
 * Accounts composable.
 * 
 * Provides business logic and state management for accounts feature.
 * Combines service calls with store state management.
 */

import { computed, ref } from 'vue'
import { useAccountsStore } from '../store/accountsStore'
import { accountsService } from '../services/accountsService'
import { getErrorMessage } from '@/core/utils/errors'

/**
 * Composable for accounts feature business logic.
 * 
 * @returns {Object} Composable return object
 */
export function useAccounts() {
  const store = useAccountsStore()
  const loading = ref(false)
  const error = ref(null)

  /**
   * Fetch all accounts.
   * 
   * @returns {Promise<Account[]>}
   */
  const fetchAccounts = async () => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      // But axios interceptor may wrap array in object: {data: [...], _pagination: ..., _meta: ...}
      const response = await accountsService.getAll()
      // Handle both array response and wrapped object response
      let accountsArray = []
      if (Array.isArray(response)) {
        accountsArray = response
      } else if (response && typeof response === 'object' && Array.isArray(response.data)) {
        accountsArray = response.data
      }
      store.setAccounts(accountsArray)
      return accountsArray
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch account by ID.
   * 
   * @param {string} accountId - Account ID
   * @returns {Promise<Account|null>}
   */
  const fetchAccountById = async (accountId) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const account = await accountsService.getById(accountId)
      store.setSelectedAccount(account)
      return account
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch account statistics.
   * 
   * @param {string} accountId - Account ID
   * @returns {Promise<AccountStats|null>}
   */
  const fetchAccountStats = async (accountId) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const stats = await accountsService.getStats(accountId)
      store.setAccountStats(accountId, stats)
      return stats
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Create new account.
   * 
   * @param {AccountCreateData} accountData - Account creation data
   * @returns {Promise<Account|null>}
   */
  const createAccount = async (accountData) => {
    loading.value = true
    error.value = null

    try {
      // Validate account data
      if (!accountData.account_id || !accountData.account_id.trim()) {
        throw new Error('Account ID is required')
      }

      // API client already extracts data from success response
      const result = await accountsService.create(accountData)
      // Refresh accounts list
      await fetchAccounts()
      return result
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete account.
   * 
   * @param {string} accountId - Account ID
   * @returns {Promise<boolean>}
   */
  const deleteAccount = async (accountId) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      await accountsService.delete(accountId)
      // Remove from local state
      store.removeAccount(accountId)
      return true
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear error.
   */
  const clearError = () => {
    error.value = null
    store.setError(null)
  }

  return {
    // State
    accounts: computed(() => store.accounts),
    selectedAccount: computed(() => store.selectedAccount),
    accountStats: computed(() => store.accountStats),
    loading,
    error,
    // Methods
    fetchAccounts,
    fetchAccountById,
    fetchAccountStats,
    createAccount,
    deleteAccount,
    clearError
  }
}
