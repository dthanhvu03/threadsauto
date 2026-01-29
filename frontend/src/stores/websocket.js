import { defineStore } from 'pinia'
import WebSocketClient from '@/api/websocket'

export const useWebSocketStore = defineStore('websocket', {
  state: () => ({
    clients: {},
    connections: {}
  }),

  actions: {
    connect(room = 'default', accountId = null) {
      const key = `${room}_${accountId || 'all'}`
      
      if (this.clients[key]) {
        return this.clients[key]
      }

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsHost = import.meta.env.VITE_WS_URL || window.location.host.replace(':5173', ':8000')
      const wsUrl = `${wsProtocol}//${wsHost}/ws`

      const client = new WebSocketClient(wsUrl, {
        room,
        account_id: accountId
      })

      client.on('connect', () => {
        this.connections[key] = {
          room,
          accountId,
          connected: true
        }
      })

      client.on('disconnect', () => {
        if (this.connections[key]) {
          this.connections[key].connected = false
        }
      })

      client.connect()
      this.clients[key] = client

      return client
    },

    disconnect(room = 'default', accountId = null) {
      const key = `${room}_${accountId || 'all'}`
      
      if (this.clients[key]) {
        this.clients[key].disconnect()
        delete this.clients[key]
        delete this.connections[key]
      }
    },

    getClient(room = 'default', accountId = null) {
      const key = `${room}_${accountId || 'all'}`
      return this.clients[key]
    },

    isConnected(room = 'default', accountId = null) {
      const key = `${room}_${accountId || 'all'}`
      return this.connections[key]?.connected || false
    }
  }
})
