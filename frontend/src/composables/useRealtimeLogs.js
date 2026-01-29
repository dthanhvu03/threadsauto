/**
 * Vue composable for realtime automation logs.
 * 
 * Connects to WebSocket và listens for automation events,
 * then adds logs to the realtimeLogs store.
 */

import { onUnmounted, ref, watch } from 'vue'
import { useRealtimeLogsStore } from '@/stores/realtimeLogs'
import { useWebSocket } from './useWebSocket'
import { sanitizeLogData } from '@/utils/sanitize'

export function useRealtimeLogs(room = 'scheduler', accountId = null) {
  const logsStore = useRealtimeLogsStore()
  const isConnected = ref(false)
  const error = ref(null)

  // Connect to WebSocket
  const ws = useWebSocket(room, accountId)
  
  // Watch WebSocket connection state
  watch(() => ws.isConnected.value, (connected) => {
    isConnected.value = connected
  }, { immediate: true })

  // Listen for automation events
  const handleAutomationStep = (data) => {
    if (!data || typeof data !== 'object') {
      console.warn('[RealtimeLogs] Invalid automation.step data')
      return
    }

    // Chỉ log các fields an toàn, không log toàn bộ data object
    const safeData = {
      step: data.step,
      result: data.result,
      time_ms: data.time_ms
    }
    console.log('[RealtimeLogs] Received automation.step:', sanitizeLogData(safeData))

    // Add log entry
    const logEntry = {
      type: 'step',
      step: data.step || 'UNKNOWN',
      result: data.result || 'UNKNOWN',
      time_ms: data.time_ms,
      error: data.error,
      account_id: data.account_id,
      job_id: data.job_id,
      thread_id: data.thread_id,
      timestamp: data.timestamp || new Date().toISOString(),
      ...data // Include any additional fields
    }
    logsStore.addLog(logEntry)
  }

  const handleAutomationAction = (data) => {
    if (!data || typeof data !== 'object') {
      return
    }

    logsStore.addLog({
      type: 'action',
      action: data.action || 'UNKNOWN',
      status: data.status || 'UNKNOWN',
      details: data.details || {},
      account_id: data.account_id,
      job_id: data.job_id,
      timestamp: data.timestamp || new Date().toISOString(),
      ...data
    })
  }

  const handleAutomationStart = (data) => {
    if (!data || typeof data !== 'object') {
      return
    }

    logsStore.addLog({
      type: 'start',
      operation: data.operation || 'UNKNOWN',
      account_id: data.account_id,
      job_id: data.job_id,
      timestamp: data.timestamp || new Date().toISOString(),
      ...data
    })
  }

  const handleAutomationComplete = (data) => {
    if (!data || typeof data !== 'object') {
      return
    }

    logsStore.addLog({
      type: 'complete',
      operation: data.operation || 'UNKNOWN',
      success: data.success !== false,
      result: data.result || {},
      account_id: data.account_id,
      job_id: data.job_id,
      timestamp: data.timestamp || new Date().toISOString(),
      ...data
    })
  }

  const handleAutomationError = (data) => {
    if (!data || typeof data !== 'object') {
      return
    }

    logsStore.addLog({
      type: 'error',
      operation: data.operation || 'UNKNOWN',
      error: data.error || 'Unknown error',
      error_type: data.error_type,
      account_id: data.account_id,
      job_id: data.job_id,
      timestamp: data.timestamp || new Date().toISOString(),
      ...data
    })
  }

  // Setup event listeners - chỉ dùng typed events, không dùng generic message để tránh duplicate
  ws.on('automation.step', handleAutomationStep)
  ws.on('automation.action', handleAutomationAction)
  ws.on('automation.start', handleAutomationStart)
  ws.on('automation.complete', handleAutomationComplete)
  ws.on('automation.error', handleAutomationError)

  // Debug: Log connection state
  ws.on('connect', () => {
    console.log('[RealtimeLogs] WebSocket connected to room:', room)
  })

  ws.on('disconnect', () => {
    console.log('[RealtimeLogs] WebSocket disconnected')
  })

  ws.on('error', (err) => {
    console.error('[RealtimeLogs] WebSocket error:', err)
    error.value = err
  })

  // Cleanup on unmount
  onUnmounted(() => {
    ws.off('automation.step', handleAutomationStep)
    ws.off('automation.action', handleAutomationAction)
    ws.off('automation.start', handleAutomationStart)
    ws.off('automation.complete', handleAutomationComplete)
    ws.off('automation.error', handleAutomationError)
    ws.off('connect')
    ws.off('disconnect')
    ws.off('error')
  })

  return {
    isConnected,
    error,
    logs: logsStore.logs,
    clearLogs: () => logsStore.clearLogs()
  }
}
