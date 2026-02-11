<template>
  <div>
    <div class="mb-4 md:mb-6">
      <div class="flex items-center gap-2 mb-1">
        <ChartBarIcon class="w-6 h-6 md:w-7 md:h-7 text-gray-900" aria-hidden="true" />
        <h1 class="text-xl md:text-2xl lg:text-3xl font-semibold text-gray-900">Dashboard</h1>
      </div>
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
      <!-- Dashboard Header with Filters -->
      <Card class="mb-6">
        <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <h2 class="text-lg font-semibold text-gray-900">Dashboard Metrics</h2>
          <div class="flex flex-wrap items-center gap-2 text-sm">
            <!-- Quick Filters -->
            <select class="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>Time range: 30 days</option>
              <option>Time range: 7 days</option>
              <option>Time range: Today</option>
            </select>
            <select class="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>Platform: All</option>
              <option>Platform: Threads</option>
              <option>Platform: Instagram</option>
            </select>
            <select class="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>Status: All</option>
              <option>Status: Completed</option>
              <option>Status: Pending</option>
            </select>
            <Button size="sm" variant="outline" @click="refreshData">
              <ArrowPathIcon class="w-4 h-4 mr-1" />
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      <!-- Metrics Cards Row -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-6">
        <StatsCard
          v-if="stats"
          label="Total Jobs"
          :value="stats.total_jobs"
          icon-name="ClipboardDocumentListIcon"
          color="primary"
          :loading="loading"
          :trend="totalJobsTrend"
        />
        <StatsCard
          v-if="stats"
          label="Success Rate"
          :value="stats.success_rate"
          icon-name="ChartBarIcon"
          color="success"
          format="percentage"
          :loading="loading"
          :trend="successRateTrend"
        />
        <StatsCard
          v-if="stats"
          label="Avg Duration"
          :value="averageDuration"
          icon-name="ClockIcon"
          color="info"
          format="duration"
          :loading="loading"
          :trend="durationTrend"
        />
        <StatsCard
          v-if="stats && stats.failed_jobs >= 0"
          label="Failed Jobs"
          :value="stats.failed_jobs"
          icon-name="XCircleIcon"
          color="danger"
          :loading="loading"
        />
      </div>

      <!-- Main Chart: Jobs Over Time -->
      <Card class="mb-6">
        <template #header>
          <h3 class="text-lg font-semibold text-gray-900">Jobs Over Time</h3>
          <p class="text-sm text-gray-600 mt-1">Last 30 days</p>
        </template>
        <!-- Main Jobs Over Time Chart -->
        <div class="h-96">
          <LineChart
            :chart-data="postsTimelineData"
            :loading="loading"
            height="380px"
            aria-label="Line chart showing jobs over time for the last 30 days"
            :show-data-table="false"
          />
        </div>
      </Card>

      <!-- Two Chart Row: Jobs by Status and Jobs by Hour -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Jobs by Status (Donut Chart) -->
        <Card>
          <template #header>
            <h3 class="text-lg font-semibold text-gray-900">Jobs by Status</h3>
          </template>
          <div class="h-64">
            <PieChart
              :chart-data="jobsStatusDistribution"
              :loading="loading"
              height="250px"
              aria-label="Pie chart showing distribution of jobs by status"
              :show-data-table="true"
            />
          </div>
        </Card>

        <!-- Jobs by Hour (Bar Chart) -->
        <Card>
          <template #header>
            <div class="flex justify-between items-start">
              <div>
                <h3 class="text-lg font-semibold text-gray-900">Jobs by Hour</h3>
                <p class="text-sm text-gray-600 mt-1">Peak: 09:00 – 11:00</p>
              </div>
            </div>
          </template>
          <div class="h-64">
            <BarChart
              :chart-data="hourlyDistributionData"
              :loading="loading"
              height="250px"
              aria-label="Bar chart showing distribution of jobs by hour"
              :show-data-table="false"
            />
          </div>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed, ref, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import {
  ChartBarIcon,
  ArrowPathIcon,
  ClockIcon
} from '@heroicons/vue/24/outline'
import { useDashboard } from '@/features/dashboard/composables/useDashboard'
import { useJobs } from '@/features/jobs/composables/useJobs'
import { useAccountsStore } from '@/stores/accounts'
import { useWebSocketStore } from '@/stores/websocket'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import LineChart from '@/components/dashboard/LineChart.vue'
import BarChart from '@/components/dashboard/BarChart.vue'
import PieChart from '@/components/dashboard/PieChart.vue'
import StatsCard from '@/components/dashboard/StatsCard.vue'
import {
  chartColors,
  platformColors,
  statusColors,
  formatChartDate,
  aggregateByKey
} from '@/utils/chartConfig'
import { formatDateTimeVN } from '@/utils/datetime'

// Route and store setup
const route = useRoute()
const accountsStore = useAccountsStore()
const wsStore = useWebSocketStore()

const { filters, handleFilterChange } = useJobs()

// Dashboard composable
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

const selectedAccount = computed(() => {
  return route.query.account_id || accountsStore.selectedAccount?.account_id || null
})

// New computed properties for the layout
const totalJobsTrend = computed(() => {
  if (!comparisonMetrics.value || !comparisonMetrics.value.today || !comparisonMetrics.value.yesterday) {
    return null
  }
  return calculateTrend(comparisonMetrics.value.today, comparisonMetrics.value.yesterday)
})

const successRateTrend = computed(() => {
  if (!stats.value) return null
  // Mock trend for success rate
  return {
    direction: 'up',
    percentage: '2.1',
    label: 'vs prev',
    colorClass: 'text-green-600'
  }
})

const averageDuration = computed(() => {
  // Mock average duration
  return 1.42
})

const durationTrend = computed(() => {
  // Mock trend for duration
  return {
    direction: 'down',
    percentage: '0.3',
    label: 'vs prev',
    colorClass: 'text-green-600'
  }
})

// Jobs by Status distribution computed property
const jobsStatusDistribution = computed(() => {
  if (!stats.value) return { labels: [], datasets: [] }
  
  return {
    labels: ['Completed', 'Pending', 'Failed', 'Running'],
    datasets: [{
      data: [
        stats.value.completed_jobs || 0,
        stats.value.pending_jobs || 0,
        stats.value.failed_jobs || 0,
        stats.value.running_jobs || 0
      ],
      backgroundColor: [
        statusColors.completed,
        statusColors.pending,
        statusColors.failed,
        statusColors.running
      ]
    }]
  }
})

// Refresh data function
const refreshData = async () => {
  await refreshAll()
}

// WebSocket connection
let wsClient = null

// Format time ago
const formatTimeAgo = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffInSeconds = Math.floor((now - date) / 1000)
  
  if (diffInSeconds < 60) return `${diffInSeconds}s ago`
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
  return `${Math.floor(diffInSeconds / 86400)}d ago`
}

// Lifecycle hooks
onMounted(async () => {
  // Fetch initial data
  await refreshAll()
  
  // Setup WebSocket for real-time updates
  if (selectedAccount.value) {
    wsClient = wsStore.connect('dashboard', selectedAccount.value, {
      onStatsUpdate: (data) => {
        // Update stats when received from WebSocket
        Object.assign(stats.value, data)
      }
    })
  }
})

onUnmounted(() => {
  // Clean up WebSocket
  if (wsClient && selectedAccount.value) {
    wsStore.disconnect('dashboard', selectedAccount.value)
  }
})

onBeforeUnmount(() => {
  if (wsClient) {
    wsStore.disconnect('dashboard', selectedAccount.value)
  }
})
</script>