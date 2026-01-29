/**
 * Vue composable for WebSocket.
 * 
 * Provides reactive WebSocket connection state và methods.
 */

import { ref, onUnmounted } from 'vue'
import WebSocketClient from '@/api/websocket'

export function useWebSocket(room = 'default', accountId = null) {
  const isConnected = ref(false)
  const isConnecting = ref(false)
  const error = ref(null)
  const lastMessage = ref(null)

  // Determine WebSocket URL
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsHost = import.meta.env.VITE_WS_URL || window.location.host.replace(':5173', ':8000')
  const wsUrl = `${wsProtocol}//${wsHost}/ws`

  const client = new WebSocketClient(wsUrl, {
    room,
    account_id: accountId
  })

  // Setup event listeners
  client.on('connect', () => {
    isConnected.value = true
    isConnecting.value = false
    error.value = null
  })

  client.on('disconnect', () => {
    isConnected.value = false
  })

  client.on('error', (err) => {
    error.value = err
    isConnecting.value = false
  })

  client.on('message', (message) => {
    lastMessage.value = message
  })

  // Connect on creation
  isConnecting.value = true
  client.connect()

  // Cleanup on unmount
  onUnmounted(() => {
    client.disconnect()
  })

  return {
    isConnected,
    isConnecting,
    error,
    lastMessage,
    send: (type, data) => client.send(type, data),
    on: (event, callback) => client.on(event, callback),
    off: (event, callback) => client.off(event, callback),
    reconnect: () => {
      client.disconnect()
      isConnecting.value = true
      client.connect()
    }
  }
}
