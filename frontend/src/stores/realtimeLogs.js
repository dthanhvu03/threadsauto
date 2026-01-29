import { defineStore } from 'pinia'

export const useRealtimeLogsStore = defineStore('realtimeLogs', {
  state: () => ({
    logs: [],
    maxLogs: 1000,
    autoScroll: true,
    paused: false
  }),

  getters: {
    filteredLogs: (state) => {
      // Return logs directly without filtering
      return state.logs
    },

    logsByJob: (state) => (jobId) => {
      return state.logs.filter(log => log.job_id === jobId)
    },

    logsByAccount: (state) => (accountId) => {
      return state.logs.filter(log => log.account_id === accountId)
    },

    recentLogs: (state) => (count = 50) => {
      return state.logs.slice(-count)
    }
  },

  actions: {
    addLog(log) {
      // Add timestamp if not present
      if (!log.timestamp) {
        log.timestamp = new Date().toISOString()
      }

      // Deduplication: Check if this log already exists
      // Compare based on step, result, timestamp (within 1 second), account_id, and job_id
      const isDuplicate = this.logs.some(existingLog => {
        const sameStep = existingLog.step === log.step || 
                        (existingLog.action === log.action && existingLog.action) ||
                        (existingLog.operation === log.operation && existingLog.operation)
        const sameResult = existingLog.result === log.result || 
                          (existingLog.status === log.status && existingLog.status) ||
                          (existingLog.success === log.success && existingLog.success !== undefined)
        const sameAccount = (!existingLog.account_id && !log.account_id) || 
                           (existingLog.account_id === log.account_id)
        const sameJob = (!existingLog.job_id && !log.job_id) || 
                       (existingLog.job_id === log.job_id)
        
        // Check if timestamps are within 1 second (to handle rapid duplicates)
        const existingTime = new Date(existingLog.timestamp).getTime()
        const newTime = new Date(log.timestamp).getTime()
        const timeDiff = Math.abs(newTime - existingTime)
        
        return sameStep && sameResult && sameAccount && sameJob && timeDiff < 1000
      })

      // Skip if duplicate
      if (isDuplicate) {
        return
      }

      // Add to logs array
      this.logs.push(log)

      // Limit logs to maxLogs
      if (this.logs.length > this.maxLogs) {
        this.logs.shift() // Remove oldest log
      }
    },

    clearLogs() {
      this.logs = []
    },

    getLogsByJob(jobId) {
      return this.logs.filter(log => log.job_id === jobId)
    },

    getLogsByAccount(accountId) {
      return this.logs.filter(log => log.account_id === accountId)
    },

    setAutoScroll(enabled) {
      this.autoScroll = enabled
    },

    togglePause() {
      this.paused = !this.paused
    }
  }
})
