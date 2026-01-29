/**
 * @deprecated This API file is kept for backward compatibility.
 * New code should use the service: @/features/accounts/services/accountsService
 * 
 * This file will be removed in a future version.
 * Please migrate to using accountsService or useAccounts composable.
 */

import apiClient from './client'

export const accountsApi = {
  getAll: () => {
    return apiClient.get('/accounts')
  },

  getById: (accountId) => {
    return apiClient.get(`/accounts/${accountId}`)
  },

  getStats: (accountId) => {
    return apiClient.get(`/accounts/${accountId}/stats`)
  },

  create: (accountData) => {
    return apiClient.post('/accounts', accountData)
  },

  delete: (accountId) => {
    return apiClient.delete(`/accounts/${accountId}`)
  }
}
