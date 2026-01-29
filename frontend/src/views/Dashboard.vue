<template>
  <div>
    <div class="mb-4 md:mb-6">
      <h1 class="text-xl md:text-2xl lg:text-3xl font-semibold text-gray-900 mb-1">📊 Dashboard</h1>
      <p v-if="selectedAccount" class="text-xs md:text-sm text-gray-600">
        Tài khoản: <strong>{{ selectedAccount }}</strong>
      </p>
    </div>

    <Alert
      v-if="error"
      type="error"
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <div v-if="loading" class="flex justify-center py-12">
      <LoadingSpinner size="lg" />
    </div>

    <div v-else>
      <!-- Filters -->
      <FilterBar
        v-model="filters"
        :show-account-filter="true"
        @change="handleFilterChange"
      />

      <!-- Stats Cards -->
      <!-- Grid: Mobile 1 column, Tablet 2 columns, Desktop 4 columns, Large Desktop 6 columns -->
      <div v-if="stats" class="grid grid-cols-1 gap-3 md:gap-4 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 mb-4 md:mb-6">
        <StatsCard
          label="Total Jobs"
          :value="stats.total_jobs"
          icon="📋"
          color="primary"
          :loading="loading"
          :trend="totalJobsTrend"
        />
        <StatsCard
          label="Pending"
          :value="stats.pending_jobs"
          icon="⏳"
          color="warning"
          :loading="loading"
        />
        <StatsCard
          label="Completed"
          :value="stats.completed_jobs"
          icon="✅"
          color="success"
          :loading="loading"
          :trend="completedTrend"
        />
        <StatsCard
          label="Success Rate"
          :value="stats.success_rate"
          icon="📈"
          color="info"
          format="percentage"
          :loading="loading"
        />
        <StatsCard
          v-if="stats.running_jobs > 0"
          label="Running"
          :value="stats.running_jobs"
          icon="🔄"
          color="primary"
          :loading="loading"
        />
        <StatsCard
          v-if="stats.failed_jobs > 0"
          label="Failed"
          :value="stats.failed_jobs"
          icon="❌"
          color="danger"
          :loading="loading"
        />
        <StatsCard
          v-if="analyticsMetrics && analyticsMetrics.summary.totalLikes > 0"
          label="Total Likes"
          :value="analyticsMetrics.summary.totalLikes"
          icon="❤️"
          color="danger"
          :loading="loading"
        />
        <StatsCard
          v-if="analyticsMetrics && analyticsMetrics.summary.totalReplies > 0"
          label="Total Replies"
          :value="analyticsMetrics.summary.totalReplies"
          icon="💬"
          color="info"
          :loading="loading"
        />
        <StatsCard
          v-if="analyticsMetrics && analyticsMetrics.summary.avgEngagementRate > 0"
          label="Engagement Rate"
          :value="analyticsMetrics.summary.avgEngagementRate"
          icon="📊"
          color="success"
          format="percentage"
          :loading="loading"
        />
      </div>

      <!-- Charts Section -->
      <Card class="mb-4 md:mb-6">
        <template #header>
          <div class="flex flex-wrap gap-1 md:gap-2">
            <button
              v-for="tab in chartTabs"
              :key="tab.id"
              @click="activeChartTab = tab.id"
              :class="[
                'px-3 py-2.5 md:py-2 font-medium text-xs md:text-sm rounded-md transition-colors min-h-[44px] md:min-h-[36px]',
                activeChartTab === tab.id
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              ]"
            >
              {{ tab.label }}
            </button>
          </div>
        </template>
        <div class="mt-4 md:mt-6">
          <!-- Trends Tab -->
          <div v-if="activeChartTab === 'trends'" class="space-y-4 md:space-y-6">
            <Card padding="sm">
              <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Posts Timeline</h4>
              <AreaChart
                :chart-data="postsTimelineData"
                :loading="loading"
                height="250px"
              />
            </Card>
            <Card padding="sm">
              <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Hourly Distribution</h4>
              <BarChart
                :chart-data="hourlyDistributionData"
                :loading="loading"
                height="250px"
              />
            </Card>
            <!-- Analytics Charts (only show if analytics data available) -->
            <template v-if="analyticsMetrics">
              <Card padding="sm">
                <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Likes Over Time</h4>
                <LineChart
                  :chart-data="analyticsMetrics.likesOverTimeChart"
                  :loading="loading"
                  height="250px"
                />
              </Card>
              <Card padding="sm">
                <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Engagement Rate Over Time</h4>
                <AreaChart
                  :chart-data="analyticsMetrics.engagementOverTimeChart"
                  :loading="loading"
                  height="250px"
                />
              </Card>
              <Card padding="sm">
                <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Replies vs Reposts</h4>
                <BarChart
                  :chart-data="analyticsMetrics.repliesVsRepostsChart"
                  :loading="loading"
                  height="250px"
                />
              </Card>
            </template>
          </div>

          <!-- Status Tab -->
          <div v-if="activeChartTab === 'status'" class="space-y-4 md:space-y-6">
            <Card padding="sm">
              <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Job Status Distribution</h4>
              <BarChart
                :chart-data="statusDistributionData"
                :loading="loading"
                height="250px"
              />
            </Card>
            <Card padding="sm">
              <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Success Rate Trend</h4>
              <LineChart
                :chart-data="successRateData"
                :loading="loading"
                height="250px"
              />
            </Card>
          </div>

          <!-- Performance Tab -->
          <div v-if="activeChartTab === 'performance'" class="space-y-4 md:space-y-6">
            <!-- Performance Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-4">
              <StatsCard
                label="Avg Execution Time"
                :value="performanceMetrics.avgExecutionTime"
                icon="⏱️"
                color="info"
                format="duration"
                :loading="loading"
              />
              <StatsCard
                label="Total Retries"
                :value="performanceMetrics.totalRetries"
                icon="🔄"
                color="warning"
                :loading="loading"
              />
              <StatsCard
                label="Error Rate"
                :value="performanceMetrics.errorRate"
                icon="⚠️"
                color="danger"
                format="percentage"
                :loading="loading"
              />
              <StatsCard
                label="Success Rate"
                :value="stats ? stats.success_rate : 0"
                icon="✅"
                color="success"
                format="percentage"
                :loading="loading"
              />
            </div>

            <!-- Performance Charts -->
            <Card padding="sm">
              <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Execution Time Distribution</h4>
              <BarChart
                :chart-data="performanceMetrics.executionTimeDistribution"
                :loading="loading"
                height="250px"
              />
            </Card>
            <Card padding="sm">
              <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Retry Rate Over Time</h4>
              <LineChart
                :chart-data="performanceMetrics.retryRateOverTime"
                :loading="loading"
                height="250px"
              />
            </Card>
            <Card padding="sm">
              <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Error Rate Trend</h4>
              <AreaChart
                :chart-data="performanceMetrics.errorRateTrend"
                :loading="loading"
                height="250px"
              />
            </Card>
            <Card padding="sm">
              <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Success vs Failure Timeline</h4>
              <AreaChart
                :chart-data="performanceMetrics.successVsFailureTimeline"
                :loading="loading"
                height="250px"
              />
            </Card>
          </div>

          <!-- Platform Tab -->
          <div v-if="activeChartTab === 'platform'" class="space-y-4 md:space-y-6">
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 md:gap-6">
              <Card padding="sm">
                <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Platform Distribution</h4>
                <PieChart
                  :chart-data="platformDistributionData"
                  :loading="loading"
                  height="250px"
                />
              </Card>
              <Card padding="sm">
                <h4 class="text-sm md:text-base font-semibold mb-3 md:mb-4">Platform Success Rates</h4>
                <BarChart
                  :chart-data="platformSuccessRatesData"
                  :loading="loading"
                  height="250px"
                />
              </Card>
            </div>
          </div>
        </div>
      </Card>

      <!-- Recent Activity -->
      <Card class="mt-4 md:mt-6">
        <template #header>
          <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 md:gap-0">
            <div class="flex items-center space-x-2">
              <h3 class="text-base md:text-lg font-semibold">Recent Activity</h3>
              <div
                v-if="wsConnected"
                class="w-2 h-2 rounded-full bg-green-500 animate-pulse"
                title="Real-time updates enabled"
              />
              <span v-if="lastUpdated" class="text-xs text-gray-500">
                Cập nhật: {{ formatLastUpdated(lastUpdated) }}
              </span>
            </div>
            <Button size="sm" variant="outline" @click="refresh" class="w-full sm:w-auto">🔄 Refresh</Button>
          </div>
        </template>
        <div v-if="activity.length === 0" class="py-8">
          <EmptyState
            title="No activity"
            description="No recent activity to display"
          />
        </div>
        <div v-else>
          <Table
            :columns="activityColumns"
            :data="filteredActivity"
          >
            <template #cell-status="{ value }">
              <span
                :class="[
                  'px-2 py-1 rounded-full text-xs font-medium',
                  getStatusBadgeClass(value)
                ]"
              >
                {{ value }}
              </span>
            </template>
            <template #cell-created_at="{ value }">
              {{ value ? formatDateTimeVN(value) : '-' }}
            </template>
          </Table>
          <div v-if="filteredActivity.length < activity.length" class="mt-3 text-center">
            <Button size="sm" variant="outline" @click="showAllActivity = !showAllActivity">
              {{ showAllActivity ? 'Hiển thị ít hơn' : `Hiển thị tất cả (${activity.length})` }}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed, ref, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useDashboard } from '@/features/dashboard/composables/useDashboard'
import { useJobs } from '@/features/jobs/composables/useJobs'
import { useAccountsStore } from '@/stores/accounts'
import { useWebSocketStore } from '@/stores/websocket'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Table from '@/components/common/Table.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LineChart from '@/components/dashboard/LineChart.vue'
import BarChart from '@/components/dashboard/BarChart.vue'
import PieChart from '@/components/dashboard/PieChart.vue'
import AreaChart from '@/components/dashboard/AreaChart.vue'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import FilterBar from '@/components/dashboard/FilterBar.vue'
import {
  chartColors,
  platformColors,
  statusColors,
  formatChartDate,
  aggregateByKey
} from '@/utils/chartConfig'
import { formatDateTimeVN } from '@/utils/datetime'

const route = useRoute()
const {
  stats,
  metrics,
  activity,
  loading,
  error,
  fetchStats,
  fetchMetrics,
  fetchActivity,
  refreshAll,
  clearError,
  postsTimelineData,
  hourlyDistributionData,
  statusDistributionData,
  successRateData,
  platformDistributionData,
  platformSuccessRatesData,
  comparisonMetrics,
  calculateTrend,
  performanceMetrics,
  analyticsMetrics
} = useDashboard()

const accountsStore = useAccountsStore()
const { fetchJobs } = useJobs()
const wsStore = useWebSocketStore()

const activeChartTab = ref('trends')
const wsConnected = ref(false)
const lastUpdated = ref(null)
const showAllActivity = ref(false)
const isFilterChanging = ref(false)
const filters = ref({
  accountId: '',
  platform: '',
  status: '',
  dateRange: { start: null, end: null }
})

// Filter and limit activity
const filteredActivity = computed(() => {
  let result = activity.value || []
  
  // Apply filters
  if (filters.value.status) {
    result = result.filter(a => a.status === filters.value.status)
  }
  if (filters.value.platform) {
    result = result.filter(a => (a.platform || '').toLowerCase() === filters.value.platform.toLowerCase())
  }
  
  // Limit display
  if (!showAllActivity.value) {
    result = result.slice(0, 10)
  }
  
  return result
})

// Status badge classes
const getStatusBadgeClass = (status) => {
  const statusLower = (status || '').toLowerCase()
  if (statusLower === 'completed') return 'bg-green-100 text-green-800'
  if (statusLower === 'pending' || statusLower === 'scheduled') return 'bg-yellow-100 text-yellow-800'
  if (statusLower === 'failed') return 'bg-red-100 text-red-800'
  if (statusLower === 'running') return 'bg-blue-100 text-blue-800'
  return 'bg-gray-100 text-gray-800'
}

const chartTabs = [
  { id: 'trends', label: '📈 Trends' },
  { id: 'status', label: '📊 Status' },
  { id: 'performance', label: '🎯 Performance' },
  { id: 'platform', label: '🌐 Platform' }
]

const selectedAccount = computed(() => {
  return route.query.account_id || accountsStore.selectedAccount?.account_id || null
})

const activityColumns = [
  { key: 'job_id', label: 'Job ID' },
  { key: 'account_id', label: 'Account' },
  { key: 'status', label: 'Status' },
  { key: 'created_at', label: 'Created' }
]

// Format last updated time
const formatLastUpdated = (date) => {
  if (!date) return ''
  const formatted = formatDateTimeVN(date)
  return formatted || ''
}

// Calculate trends for stats cards
const totalJobsTrend = computed(() => {
  if (!comparisonMetrics.value || !comparisonMetrics.value.today || !comparisonMetrics.value.yesterday) {
    return null
  }
  return calculateTrend(comparisonMetrics.value.today, comparisonMetrics.value.yesterday)
})

const completedTrend = computed(() => {
  if (!comparisonMetrics.value || !comparisonMetrics.value.today || !comparisonMetrics.value.yesterday) {
    return null
  }
  const todayCompleted = comparisonMetrics.value.today.completed
  const yesterdayCompleted = comparisonMetrics.value.yesterday.completed
  if (yesterdayCompleted === 0) return null
  const change = ((todayCompleted - yesterdayCompleted) / yesterdayCompleted) * 100
  return {
    direction: change > 0 ? 'up' : change < 0 ? 'down' : 'neutral',
    percentage: Math.abs(change).toFixed(1),
    label: 'vs yesterday',
    colorClass: change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'
  }
})

// Chart data computations are now in useDashboard composable
// Additional chart data that depends on jobs can be computed here if needed

// Global refresh state to prevent concurrent refreshes
let isGlobalRefreshing = false
let globalRefreshPromise = null

const refresh = async () => {
  // Skip if already refreshing or filter is changing
  if (isGlobalRefreshing || isFilterChanging.value) {
    if (globalRefreshPromise) {
      await globalRefreshPromise
    }
    return
  }
  
  isGlobalRefreshing = true
  globalRefreshPromise = (async () => {
    try {
      await refreshAll(selectedAccount.value)
      await fetchJobs({ accountId: selectedAccount.value })
      lastUpdated.value = new Date()
    } catch (error) {
      console.error('Error in refresh:', error)
      throw error
    } finally {
      isGlobalRefreshing = false
      globalRefreshPromise = null
    }
  })()
  
  await globalRefreshPromise
}

// Debounce timer for filter changes
let filterDebounceTimer = null
let isRefreshing = false
let refreshPromise = null

// Debounce timer for WebSocket events
let wsRefreshDebounceTimer = null

const handleFilterChange = async (newFilters) => {
  
  // Deep comparison - skip if no actual change
  // Normalize dateRange for comparison (handle both Date objects and ISO strings)
  const normalizeForComparison = (filters) => {
    const normalized = { ...filters }
    if (normalized.dateRange) {
      normalized.dateRange = {
        start: normalized.dateRange.start ? (typeof normalized.dateRange.start === 'string' ? normalized.dateRange.start : normalized.dateRange.start.toISOString()) : null,
        end: normalized.dateRange.end ? (typeof normalized.dateRange.end === 'string' ? normalized.dateRange.end : normalized.dateRange.end.toISOString()) : null
      }
    }
    return normalized
  }
  
  const currentNormalized = normalizeForComparison(filters.value)
  const newNormalized = normalizeForComparison(newFilters)
  
  if (JSON.stringify(currentNormalized) === JSON.stringify(newNormalized)) {
    return // No change, skip
  }
  
  // Mark that filters are changing (pause auto-refresh)
  isFilterChanging.value = true
  
  // If already refreshing, wait for it to complete before starting a new one
  if (isRefreshing && refreshPromise) {
    try {
      await refreshPromise
    } catch (e) {
      // Ignore errors from previous refresh
    }
  }
  
  // Clear existing debounce timer
  if (filterDebounceTimer) {
    clearTimeout(filterDebounceTimer)
  }
  
  // Update filters immediately (for UI responsiveness)
  filters.value = newFilters
  
  // Debounce the actual API calls (1000ms delay - increased from 500ms)
  filterDebounceTimer = setTimeout(async () => {
    // Double-check if already refreshing (race condition protection)
    if (isRefreshing) {
      // Wait for current refresh to complete, then retry
      try {
        await refreshPromise
      } catch (e) {
        // Ignore errors from previous refresh
      }
      // Retry after previous refresh completes
      filterDebounceTimer = setTimeout(() => handleFilterChange(filters.value), 500)
      return
    }
    
    // Apply filters to data fetching
    const accountId = filters.value.accountId || selectedAccount.value
    
    isRefreshing = true
    refreshPromise = (async () => {
      try {
        await refreshAll(accountId)
        
        await fetchJobs({ 
          accountId,
          platform: filters.value.platform || undefined,
          status: filters.value.status || undefined
        })
        
        isFilterChanging.value = false
      } catch (error) {
        // Handle 429 errors gracefully - wait longer before retry
        if (error.status === 429 || (error.response && error.response.status === 429)) {
          console.warn('Rate limit exceeded. Waiting before retry...')
          // Wait 5 seconds before retry (rate limit is per minute)
          await new Promise(resolve => setTimeout(resolve, 5000))
          try {
            await refreshAll(accountId)
            await fetchJobs({ 
              accountId,
              platform: filters.value.platform || undefined,
              status: filters.value.status || undefined
            })
          } catch (retryError) {
            console.error('Error retrying after rate limit:', retryError)
          }
        } else {
          console.error('Error refreshing dashboard:', error)
        }
        
        isFilterChanging.value = false
        throw error
      } finally {
        isRefreshing = false
        refreshPromise = null
      }
    })()
    
    await refreshPromise
  }, 1000) // 1000ms debounce delay (increased from 500ms)
}

// WebSocket setup
let wsClient = null

const setupWebSocket = () => {
  wsClient = wsStore.connect('dashboard', selectedAccount.value)
  
  wsClient.on('connect', () => {
    wsConnected.value = true
  })

  wsClient.on('disconnect', () => {
    wsConnected.value = false
  })

  // Debounced refresh for WebSocket events (5 seconds debounce)
  const debouncedRefresh = () => {
    // Skip if already refreshing or filter is changing
    if (isGlobalRefreshing || isFilterChanging.value) {
      return
    }
    
    // Clear existing debounce timer
    if (wsRefreshDebounceTimer) {
      clearTimeout(wsRefreshDebounceTimer)
    }
    
    // Debounce refresh for 5 seconds
    wsRefreshDebounceTimer = setTimeout(async () => {
      // Double-check before refreshing
      if (isGlobalRefreshing || isFilterChanging.value) {
        return
      }
      
      try {
        await refresh()
      } catch (error) {
        console.error('Error refreshing on WebSocket event:', error)
      }
    }, 5000) // 5 seconds debounce
  }

  // Use debounced refresh for dashboard.stats event (was causing continuous refresh)
  wsClient.on('dashboard.stats', (data) => {
    if (data && typeof data === 'object') {
      debouncedRefresh()
    }
  })

  wsClient.on('job.created', debouncedRefresh)

  wsClient.on('job.updated', debouncedRefresh)
}

let autoRefreshInterval = null

onMounted(async () => {
  await refreshAll(selectedAccount.value)
  await fetchJobs({ accountId: selectedAccount.value })
  lastUpdated.value = new Date()
  setupWebSocket()
  
  // Auto-refresh every 60 seconds (increased from 30 to reduce load)
  autoRefreshInterval = setInterval(async () => {
    // Only refresh if tab is visible, not changing filters, and not already refreshing
    if (!document.hidden && !isFilterChanging.value && !isGlobalRefreshing) {
      try {
        await refresh()
      } catch (error) {
        console.error('Error in auto-refresh:', error)
      }
    }
  }, 60000) // 60 seconds (increased from 30)
})

onBeforeUnmount(() => {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
  }
  if (filterDebounceTimer) {
    clearTimeout(filterDebounceTimer)
  }
  if (wsRefreshDebounceTimer) {
    clearTimeout(wsRefreshDebounceTimer)
  }
})

onUnmounted(() => {
  if (wsClient) {
    wsStore.disconnect('dashboard', selectedAccount.value)
  }
})
</script>
