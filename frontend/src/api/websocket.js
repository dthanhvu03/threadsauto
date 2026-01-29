/**
 * WebSocket client wrapper.
 * 
 * Provides WebSocket connection với auto-reconnect và event handling.
 */

class WebSocketClient {
  constructor(url, options = {}) {
    this.url = url
    this.options = {
      reconnectInterval: 3000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      ...options
    }
    this.ws = null
    this.reconnectAttempts = 0
    this.reconnectTimer = null
    this.heartbeatTimer = null
    this.listeners = new Map()
    this.isConnecting = false
    this.isConnected = false
  }

  connect() {
    if (this.isConnecting || this.isConnected) {
      return
    }

    this.isConnecting = true

    try {
      const wsUrl = new URL(this.url, window.location.origin)
      wsUrl.protocol = wsUrl.protocol === 'https:' ? 'wss:' : 'ws:'
      
      // Add query parameters
      if (this.options.room) {
        wsUrl.searchParams.set('room', this.options.room)
      }
      if (this.options.account_id) {
        wsUrl.searchParams.set('account_id', this.options.account_id)
      }

      this.ws = new WebSocket(wsUrl.toString())

      this.ws.onopen = () => {
        this.isConnecting = false
        this.isConnected = true
        this.reconnectAttempts = 0
        this.emit('connect')
        this.startHeartbeat()
      }

      this.ws.onmessage = (event) => {
        try {
          if (!event || !event.data) {
            console.warn('WebSocket: Empty message received')
            return
          }

          const message = JSON.parse(event.data)
          
          // Validate message structure
          if (!message || typeof message !== 'object') {
            console.warn('WebSocket: Invalid message format')
            return
          }
          
          // Handle pong
          if (message.type === 'pong') {
            return
          }

          // Emit message with safe data access
          this.emit('message', message)
          
          // Emit typed event with safe data
          if (message.type) {
            const eventData = message.data || message.payload || message
            this.emit(message.type, eventData)
          }
        } catch (error) {
          // Sanitize error trước khi log
          const sanitizedError = error instanceof Error ? error.message : String(error)
          console.error('Error parsing WebSocket message:', sanitizedError)
          this.emit('error', { error: 'Failed to parse message', originalError: sanitizedError })
        }
      }

      this.ws.onerror = (error) => {
        this.isConnecting = false
        // Suppress extension-related errors
        const errorMessage = error?.message || String(error)
        if (!errorMessage.includes('extension') && !errorMessage.includes('runtime.lastError')) {
          this.emit('error', error)
        }
      }

      this.ws.onclose = () => {
        this.isConnected = false
        this.isConnecting = false
        this.stopHeartbeat()
        this.emit('disconnect')
        this.attemptReconnect()
      }
    } catch (error) {
      this.isConnecting = false
      this.emit('error', error)
      this.attemptReconnect()
    }
  }

  disconnect() {
    this.stopHeartbeat()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.isConnected = false
  }

  send(type, data) {
    if (!this.isConnected || !this.ws) {
      console.warn('WebSocket not connected')
      return false
    }

    try {
      this.ws.send(JSON.stringify({ type, data }))
      return true
    } catch (error) {
      // Sanitize error trước khi log
      const sanitizedError = error instanceof Error ? error.message : String(error)
      console.error('Error sending WebSocket message:', sanitizedError)
      this.emit('error', { error: 'Failed to send message' })
      return false
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
  }

  off(event, callback) {
    if (!this.listeners.has(event)) {
      return
    }
    const callbacks = this.listeners.get(event)
    const index = callbacks.indexOf(callback)
    if (index > -1) {
      callbacks.splice(index, 1)
    }
  }

  emit(event, data) {
    if (!event) {
      return
    }
    
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          if (typeof callback === 'function') {
            callback(data)
          }
        } catch (error) {
          // Sanitize error trước khi log
          const sanitizedError = error instanceof Error ? error.message : String(error)
          console.error(`Error in WebSocket listener for ${event}:`, sanitizedError)
        }
      })
    }
  }

  attemptReconnect() {
    if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
      this.emit('reconnect_failed')
      return
    }

    this.reconnectAttempts++
    this.reconnectTimer = setTimeout(() => {
      this.connect()
    }, this.options.reconnectInterval)
  }

  startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.send('ping', {})
      }
    }, this.options.heartbeatInterval)
  }

  stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

export default WebSocketClient
