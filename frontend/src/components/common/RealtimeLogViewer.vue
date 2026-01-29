<template>
  <Card>
    <template #header>
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-3 md:gap-0">
        <div class="flex flex-col md:flex-row md:items-center gap-2 md:space-x-2">
          <h3 class="text-base md:text-lg font-semibold text-gray-900">Realtime Automation Logs</h3>
          <span
            v-if="isConnected"
            class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
          >
            <span class="w-2 h-2 bg-green-500 rounded-full mr-1 animate-pulse"></span>
            Connected
          </span>
          <span
            v-else
            class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800"
          >
            <span class="w-2 h-2 bg-gray-500 rounded-full mr-1"></span>
            Disconnected
          </span>
        </div>
        <div class="flex flex-row gap-2 md:space-x-2">
          <Button
            v-if="logsStore.autoScroll"
            @click="logsStore.setAutoScroll(false)"
            size="sm"
            variant="outline"
            class="min-h-[44px] md:min-h-[36px]"
          >
            Pause Scroll
          </Button>
          <Button
            v-else
            @click="handleResumeScroll"
            size="sm"
            variant="outline"
            class="min-h-[44px] md:min-h-[36px]"
          >
            Resume Scroll
          </Button>
          <Button
            @click="logsStore.clearLogs()"
            size="sm"
            variant="outline"
            class="min-h-[44px] md:min-h-[36px]"
          >
            Clear
          </Button>
        </div>
      </div>
    </template>

    <!-- Logs List -->
    <div
      ref="logsContainer"
      class="bg-gray-50 rounded-lg border border-gray-200 p-4 max-h-96 overflow-y-auto font-mono text-sm"
      style="scroll-behavior: smooth;"
    >
      <div v-if="logs.length === 0" class="text-center text-gray-500 py-8">
        <div class="text-sm">Waiting for automation logs...</div>
        <div v-if="!isConnected" class="text-xs text-gray-400 mt-2">WebSocket disconnected</div>
      </div>
      <div
        v-for="(log, index) in logs"
        :key="`log-${index}-${log.timestamp}`"
        :class="[
          getLogClasses(log),
          index === logs.length - 1 ? 'ring-2 ring-blue-300 animate-pulse' : ''
        ]"
        class="mb-2 p-2 rounded border-l-4 transition-all"
      >
        <div class="flex items-start space-x-2">
          <span class="text-gray-500 text-xs flex-shrink-0 w-16">
            {{ formatTime(log.timestamp) }}
          </span>
          <span class="flex-shrink-0 text-lg">{{ getLogIcon(log) }}</span>
          <div class="flex-1 min-w-0">
            <div class="flex items-center space-x-2 flex-wrap">
              <span class="font-semibold text-gray-900">{{ translateStepName(log.step || log.action || log.operation || 'UNKNOWN') }}</span>
              <span :class="getResultClasses(log.result || log.status || log.success)" class="px-2 py-0.5 rounded text-xs">
                {{ translateResult(log.result || log.status || (log.success !== undefined ? (log.success ? 'SUCCESS' : 'FAILED') : '')) }}
              </span>
            </div>
            <div v-if="log.account_id || log.job_id" class="text-xs text-gray-600 mt-1">
              <span v-if="log.account_id">Account: {{ log.account_id }}</span>
              <span v-if="log.account_id && log.job_id"> • </span>
              <span v-if="log.job_id">Job: {{ log.job_id.substring(0, 8) }}...</span>
              <span v-if="log.thread_id"> • Thread: {{ log.thread_id }}</span>
            </div>
            <div v-if="log.error" class="text-xs text-red-600 mt-1 font-medium">
              ⚠️ {{ log.error }}
            </div>
            <div v-if="log.time_ms" class="text-xs text-gray-500 mt-1">
              ⏱️ {{ log.time_ms.toFixed(2) }}ms
            </div>
          </div>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import Card from './Card.vue'
import Button from './Button.vue'
import { useRealtimeLogsStore } from '@/stores/realtimeLogs'
import { useRealtimeLogs } from '@/composables/useRealtimeLogs'
import { translateStepName, translateResult } from '@/utils/logTranslations'

const props = defineProps({
  room: {
    type: String,
    default: 'scheduler'
  },
  accountId: {
    type: String,
    default: null
  }
})

const logsStore = useRealtimeLogsStore()
const { isConnected } = useRealtimeLogs(props.room, props.accountId)

const logsContainer = ref(null)

const logs = computed(() => logsStore.logs)

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const getLogIcon = (log) => {
  const step = (log.step || log.action || log.operation || '').toUpperCase()
  
  if (step.includes('CLICK')) return '🖱️'
  if (step.includes('TYPE') || step.includes('INPUT')) return '⌨️'
  if (step.includes('POST') || step.includes('THREAD')) return '📝'
  if (log.result === 'SUCCESS' || log.success === true) return '✅'
  if (log.result === 'ERROR' || log.result === 'FAILED' || log.success === false) return '❌'
  if (log.result === 'WARNING') return '⚠️'
  return 'ℹ️'
}

const getLogClasses = (log) => {
  const result = log.result || log.status || (log.success !== undefined ? (log.success ? 'SUCCESS' : 'FAILED') : '')
  
  if (result === 'SUCCESS' || result === 'COMPLETED') {
    return 'bg-green-50 border-green-400'
  }
  if (result === 'ERROR' || result === 'FAILED') {
    return 'bg-red-50 border-red-400'
  }
  if (result === 'WARNING') {
    return 'bg-yellow-50 border-yellow-400'
  }
  if (result === 'IN_PROGRESS') {
    return 'bg-blue-50 border-blue-400'
  }
  return 'bg-white border-gray-300'
}

const getResultClasses = (result) => {
  if (result === 'SUCCESS' || result === 'COMPLETED') {
    return 'text-green-700 font-semibold'
  }
  if (result === 'ERROR' || result === 'FAILED') {
    return 'text-red-700 font-semibold'
  }
  if (result === 'WARNING') {
    return 'text-yellow-700 font-semibold'
  }
  if (result === 'IN_PROGRESS') {
    return 'text-blue-700 font-semibold'
  }
  return 'text-gray-700'
}

// Track if user manually scrolled up
const userScrolledUp = ref(false)

// Handle resume scroll button click
const handleResumeScroll = () => {
  logsStore.setAutoScroll(true)
  userScrolledUp.value = false // Reset flag when resuming
  // Immediately scroll to bottom
  nextTick(() => {
    if (logsContainer.value) {
      logsContainer.value.scrollTo({
        top: logsContainer.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

// Auto-scroll to bottom when new logs arrive
// Watch logs.length để trigger khi có log mới được thêm
watch(() => logs.length, (newLength, oldLength) => {
  if (newLength > (oldLength || 0) && logsStore.autoScroll) {
    // Use nextTick + setTimeout để đảm bảo DOM đã update hoàn toàn
    nextTick(() => {
      setTimeout(() => {
        if (logsContainer.value) {
          const container = logsContainer.value
          
          // Check if user is near bottom (within 50px threshold)
          const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 50
          
          // If autoScroll is enabled, always scroll to bottom
          // But respect user's manual scroll - if they scrolled up, don't force scroll
          if (isNearBottom || oldLength === 0 || !userScrolledUp.value) {
            container.scrollTo({
              top: container.scrollHeight,
              behavior: 'smooth'
            })
            userScrolledUp.value = false // Reset flag after auto-scrolling
          }
        }
      }, 50) // Reduced timeout for faster response
    })
  }
})

// Watch for manual scroll to detect if user scrolled up
const handleScroll = () => {
  if (logsContainer.value) {
    const container = logsContainer.value
    const isAtBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 10
    
    // If user scrolled away from bottom, mark as scrolled up
    if (!isAtBottom) {
      userScrolledUp.value = true
    } else {
      // If user scrolled back to bottom, reset flag
      userScrolledUp.value = false
    }
  }
}

onMounted(() => {
  // Initial scroll to bottom
  nextTick(() => {
    if (logsContainer.value) {
      const container = logsContainer.value
      container.scrollTop = container.scrollHeight
      
      // Add scroll event listener to detect manual scrolling
      container.addEventListener('scroll', handleScroll)
    }
  })
})

// Cleanup scroll listener on unmount
onUnmounted(() => {
  if (logsContainer.value) {
    logsContainer.value.removeEventListener('scroll', handleScroll)
  }
})
</script>
