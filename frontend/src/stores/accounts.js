/**
 * Accounts store - State management only.
 * 
 * @deprecated This store is kept for backward compatibility.
 * New code should use the composable: @/features/accounts/composables/useAccounts
 * 
 * Business logic is in useAccounts composable.
 * This store only manages state.
 */

import { defineStore } from 'pinia'

export const useAccountsStore = defineStore('accounts', {
  state: () => ({
    accounts: [],
    selectedAccount: null,
    accountStats: {},
    error: null
  }),

  getters: {
    /**
     * Get account by ID.
     * 
     * @param {Object} state - Store state
     * @returns {Function} Function to get account by ID
     */
    accountById: (state) => {
      return (id) => state.accounts.find(acc => acc.account_id === id)
    }
  },

  actions: {
    /**
     * Set accounts.
     * Called by useAccounts composable.
     * 
     * @param {Account[]} accounts - Accounts array
     */
    setAccounts(accounts) {
      this.accounts = accounts
    },

    /**
     * Set selected account.
     * Called by useAccounts composable.
     * 
     * @param {Account|null} account - Selected account
     */
    setSelectedAccount(account) {
      this.selectedAccount = account
    },

    /**
     * Set account statistics.
     * Called by useAccounts composable.
     * 
     * @param {string} accountId - Account ID
     * @param {AccountStats} stats - Account statistics
     */
    setAccountStats(accountId, stats) {
      this.accountStats[accountId] = stats
    },

    /**
     * Remove account by ID.
     * Called by useAccounts composable.
     * 
     * @param {string} accountId - Account ID
     */
    removeAccount(accountId) {
      this.accounts = this.accounts.filter(acc => acc.account_id !== accountId)
      if (this.selectedAccount?.account_id === accountId) {
        this.selectedAccount = null
      }
    },

    /**
     * Set error.
     * Called by useAccounts composable.
     * 
     * @param {string|null} error - Error message
     */
    setError(error) {
      this.error = error
    },

    /**
     * Reset store state.
     */
    reset() {
      this.accounts = []
      this.selectedAccount = null
      this.accountStats = {}
      this.error = null
    }
  }
})
