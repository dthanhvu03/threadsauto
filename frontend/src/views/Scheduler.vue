<template>
  <div>
    <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 md:gap-0">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-gray-900 mb-1">⏰ Scheduler</h1>
        <p class="text-xs md:text-sm text-gray-600">Control and monitor the scheduler</p>
      </div>
      <div class="flex flex-col md:flex-row gap-2 md:space-x-3 w-full md:w-auto">
        <Button
          v-if="!status.running"
          variant="success"
          @click="handleStart"
          :loading="loading"
          class="w-full md:w-auto"
        >
          Start Scheduler
        </Button>
        <Button
          v-else
          variant="danger"
          @click="handleStop"
          :loading="loading"
          class="w-full md:w-auto"
        >
          Stop Scheduler
        </Button>
        <Button variant="outline" @click="refreshStatus" class="w-full md:w-auto">🔄 Refresh</Button>
      </div>
    </div>

    <Alert
      v-if="error"
      type="error"
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <!-- Status Card -->
    <Card class="mb-4 md:mb-6">
      <template #header>
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 md:gap-0">
          <h3 class="text-base md:text-lg font-semibold">Scheduler Status</h3>
          <div class="flex items-center space-x-2">
            <div
              :class="[
                'w-2 h-2 rounded-full',
                wsConnected ? 'bg-green-500' : 'bg-gray-400'
              ]"
              :title="wsConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'"
            />
            <span class="text-xs text-gray-500">
              {{ wsConnected ? 'Live' : 'Offline' }}
            </span>
          </div>
        </div>
      </template>
      <div class="space-y-4">
        <div class="flex items-center space-x-4">
          <div class="flex items-center">
            <div
              :class="[
                'w-3 h-3 rounded-full mr-2',
                status.running ? 'bg-green-500' : 'bg-gray-400'
              ]"
            />
            <span class="text-sm font-medium">
              Status: {{ status.running ? 'Running' : 'Stopped' }}
            </span>
          </div>
        </div>
        <div>
          <p class="text-sm text-gray-600">
            Active Jobs: <strong>{{ status.activeJobsCount }}</strong>
          </p>
        </div>
      </div>
    </Card>

    <!-- Active Jobs -->
    <Card>
      <template #header>
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 md:gap-0">
          <h3 class="text-base md:text-lg font-semibold">Active Jobs</h3>
          <Button size="sm" variant="outline" @click="refreshActiveJobs" class="w-full md:w-auto">🔄 Refresh</Button>
        </div>
      </template>
      <div v-if="loading" class="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
      <div v-else-if="activeJobs.length === 0" class="py-8">
        <EmptyState
          title="No active jobs"
          description="No jobs are currently being processed"
        />
      </div>
      <Table
        v-else
        :columns="activeJobColumns"
        :data="activeJobs"
      >
        <template #cell-scheduled_time="{ value }">
          {{ value ? formatDateTimeVN(value) : '-' }}
        </template>
        <template #cell-status_message="{ value }">
          <span class="text-xs text-gray-600">{{ value || '-' }}</span>
        </template>
      </Table>
    </Card>

    <!-- Realtime Automation Logs -->
    <div class="mt-4 md:mt-6">
      <RealtimeLogViewer room="scheduler" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useScheduler } from '@/features/scheduler/composables/useScheduler'
import { useWebSocketStore } from '@/stores/websocket'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Table from '@/components/common/Table.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import RealtimeLogViewer from '@/components/common/RealtimeLogViewer.vue'
import { formatDateTimeVN } from '@/utils/datetime'

const {
  status,
  activeJobs,
  loading,
  error,
  fetchStatus,
  fetchActiveJobs,
  start,
  stop,
  clearError
} = useScheduler()

const wsStore = useWebSocketStore()

const wsConnected = ref(false)

const activeJobColumns = [
  { key: 'job_id', label: 'Job ID' },
  { key: 'account_id', label: 'Account' },
  { key: 'status', label: 'Status' },
  { key: 'scheduled_time', label: 'Scheduled Time' },
  { key: 'status_message', label: 'Status Message' }
]

const handleStart = async () => {
  await start()
}

const handleStop = async () => {
  await stop()
}

const refreshStatus = async () => {
  await fetchStatus()
  await fetchActiveJobs()
}

const refreshActiveJobs = async () => {
  await fetchActiveJobs()
}

// WebSocket setup
let wsClient = null

const setupWebSocket = () => {
  wsClient = wsStore.connect('scheduler')
  
  wsClient.on('connect', () => {
    wsConnected.value = true
  })

  wsClient.on('disconnect', () => {
    wsConnected.value = false
  })

  wsClient.on('scheduler.status', async (data) => {
    try {
      if (data && typeof data === 'object') {
        // Refresh status from API to ensure consistency
        await fetchStatus()
      }
    } catch (error) {
      console.error('Error handling scheduler.status:', error)
    }
  })

  // Listen for job.created event (e.g., from Excel upload)
  wsClient.on('job.created', async (data) => {
    try {
      // Refresh both status and active jobs when new jobs are created
      await refreshStatus()
      await refreshActiveJobs()
    } catch (error) {
      console.error('Error refreshing on job.created event:', error)
    }
  })

  wsClient.on('job.updated', () => {
    try {
      refreshActiveJobs()
    } catch (error) {
      console.error('Error refreshing active jobs:', error)
    }
  })

  wsClient.on('job.completed', () => {
    try {
      refreshStatus()
    } catch (error) {
      console.error('Error refreshing status:', error)
    }
  })
}

onMounted(async () => {
  await refreshStatus()
  setupWebSocket()
})

onUnmounted(() => {
  if (wsClient) {
    wsStore.disconnect('scheduler')
  }
})
</script>
