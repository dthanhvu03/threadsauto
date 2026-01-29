/**
 * Dashboard composable.
 * 
 * Provides business logic and state management for dashboard feature.
 * Combines service calls with store state management.
 */

import { computed, ref } from 'vue'
import { useDashboardStore } from '../store/dashboardStore'
import { useJobsStore } from '@/features/jobs/store/jobsStore'
import { dashboardService } from '../services/dashboardService'
import { getErrorMessage } from '@/core/utils/errors'
import { statusColors, chartColors, platformColors } from '@/utils/chartConfig'
import { formatDateVN, toVietnamTimezone } from '@/utils/datetime'

/**
 * Composable for dashboard feature business logic.
 * 
 * @returns {Object} Composable return object
 */
export function useDashboard() {
  const store = useDashboardStore()
  const jobsStore = useJobsStore()
  const loading = ref(false)
  const error = ref(null)

  /**
   * Fetch dashboard statistics.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @returns {Promise<DashboardStats>}
   */
  const fetchStats = async (accountId = null) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const stats = await dashboardService.getStats(accountId)
      store.setStats(stats)
      return stats
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch dashboard metrics.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @returns {Promise<DashboardMetrics>}
   */
  const fetchMetrics = async (accountId = null) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const metrics = await dashboardService.getMetrics(accountId)
      store.setMetrics(metrics)
      return metrics
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch recent activity.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @param {number} [limit=10] - Number of activities to return
   * @returns {Promise<Activity[]>}
   */
  const fetchActivity = async (accountId = null, limit = 10) => {
    loading.value = true
    error.value = null

    try {
      // API client already extracts data from success response
      const activity = await dashboardService.getActivity(accountId, limit)
      store.setActivity(Array.isArray(activity) ? activity : [])
      return activity
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      error.value = errorMessage
      store.setError(errorMessage)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Refresh all dashboard data.
   * 
   * @param {string} [accountId] - Optional account ID filter
   * @returns {Promise<void>}
   */
  const refreshAll = async (accountId = null) => {
    try {
      await Promise.all([
        fetchStats(accountId),
        fetchMetrics(accountId),
        fetchActivity(accountId)
      ])
    } catch (error) {
      throw error
    }
  }

  /**
   * Clear error.
   */
  const clearError = () => {
    error.value = null
    store.setError(null)
  }

  // Chart data computations
  const postsTimelineData = computed(() => {
    if (!jobsStore.jobs || jobsStore.jobs.length === 0) {
      return { labels: [], datasets: [] }
    }

    // Group jobs by date and platform
    const datePlatformMap = {}
    jobsStore.jobs.forEach(job => {
      if (job.completed_at) {
        // Format date using Vietnam timezone
        const date = formatDateVN(job.completed_at)
        const platform = job.platform || 'THREADS'
        
        if (!datePlatformMap[date]) {
          datePlatformMap[date] = {}
        }
        datePlatformMap[date][platform] = (datePlatformMap[date][platform] || 0) + 1
      }
    })

    const dates = Object.keys(datePlatformMap).sort()
    const platforms = [...new Set(jobsStore.jobs.map(j => j.platform || 'THREADS'))]

    const datasets = platforms.map(platform => ({
      label: platform,
      data: dates.map(date => datePlatformMap[date][platform] || 0),
      backgroundColor: platformColors[platform] || platformColors.default,
      borderColor: platformColors[platform] || platformColors.default,
      fill: true
    }))

    return {
      labels: dates,
      datasets
    }
  })

  const hourlyDistributionData = computed(() => {
    if (!jobsStore.jobs || jobsStore.jobs.length === 0) {
      return { labels: [], datasets: [] }
    }

    const hourlyCount = {}
    jobsStore.jobs.forEach(job => {
      if (job.created_at) {
        // Convert to Vietnam timezone first, then get hour
        const vnDate = toVietnamTimezone(job.created_at)
        if (vnDate) {
          const hour = vnDate.getHours() // Use local hours after timezone conversion
          hourlyCount[hour] = (hourlyCount[hour] || 0) + 1
        }
      }
    })

    const hours = Array.from({ length: 24 }, (_, i) => i)
    const labels = hours.map(h => `${h}:00`)
    const data = hours.map(h => hourlyCount[h] || 0)

    return {
      labels,
      datasets: [{
        label: 'Jobs',
        data,
        backgroundColor: chartColors.primary,
        borderColor: chartColors.primary
      }]
    }
  })

  const statusDistributionData = computed(() => {
    if (!store.stats) {
      return { labels: [], datasets: [] }
    }

    const statusData = {
      Pending: store.stats.pending_jobs || 0,
      Completed: store.stats.completed_jobs || 0,
      Failed: store.stats.failed_jobs || 0
    }

    const labels = Object.keys(statusData).filter(k => statusData[k] > 0)
    const data = labels.map(l => statusData[l])
    const backgroundColors = labels.map(l => statusColors[l.toLowerCase()] || chartColors.gray[500])

    return {
      labels,
      datasets: [{
        label: 'Jobs',
        data,
        backgroundColor: backgroundColors,
        borderColor: backgroundColors
      }]
    }
  })

  const successRateData = computed(() => {
    if (!store.stats) {
      return { labels: [], datasets: [] }
    }

    const labels = ['Today']
    const data = [store.stats.success_rate || 0]

    return {
      labels,
      datasets: [{
        label: 'Success Rate (%)',
        data,
        borderColor: chartColors.success,
        backgroundColor: chartColors.success + '20',
        fill: true
      }]
    }
  })

  const platformDistributionData = computed(() => {
    if (!store.metrics?.jobs_by_platform) {
      return { labels: [], datasets: [] }
    }

    const platformData = store.metrics.jobs_by_platform
    const labels = Object.keys(platformData)
    const data = Object.values(platformData)
    const backgroundColors = labels.map(p => platformColors[p] || platformColors.default)

    return {
      labels,
      datasets: [{
        data,
        backgroundColor: backgroundColors,
        borderColor: backgroundColors
      }]
    }
  })

  const platformSuccessRatesData = computed(() => {
    if (!store.metrics?.jobs_by_platform) {
      return { labels: [], datasets: [] }
    }

    const platforms = Object.keys(store.metrics.jobs_by_platform)
    const labels = platforms
    const data = platforms.map(() => store.stats?.success_rate || 0)

    return {
      labels,
      datasets: [{
        label: 'Success Rate (%)',
        data,
        backgroundColor: chartColors.success,
        borderColor: chartColors.success
      }]
    }
  })

  // Comparison metrics
  const comparisonMetrics = computed(() => {
    if (!jobsStore.jobs || jobsStore.jobs.length === 0) {
      return {
        today: null,
        yesterday: null,
        thisWeek: null,
        lastWeek: null,
        thisMonth: null,
        lastMonth: null
      }
    }

    const now = new Date()
    const vnNow = toVietnamTimezone(now)
    if (!vnNow) return null

    const today = new Date(vnNow.getFullYear(), vnNow.getMonth(), vnNow.getDate())
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)

    const thisWeekStart = new Date(today)
    thisWeekStart.setDate(today.getDate() - today.getDay())
    const lastWeekStart = new Date(thisWeekStart)
    lastWeekStart.setDate(lastWeekStart.getDate() - 7)
    const lastWeekEnd = new Date(thisWeekStart)
    lastWeekEnd.setDate(lastWeekEnd.getDate() - 1)

    const thisMonthStart = new Date(vnNow.getFullYear(), vnNow.getMonth(), 1)
    const lastMonthStart = new Date(vnNow.getFullYear(), vnNow.getMonth() - 1, 1)
    const lastMonthEnd = new Date(vnNow.getFullYear(), vnNow.getMonth(), 0)

    const filterJobsByDateRange = (startDate, endDate) => {
      return jobsStore.jobs.filter(job => {
        if (!job.completed_at) return false
        const jobDate = toVietnamTimezone(job.completed_at)
        if (!jobDate) return false
        const jobDateOnly = new Date(jobDate.getFullYear(), jobDate.getMonth(), jobDate.getDate())
        return jobDateOnly >= startDate && jobDateOnly <= endDate
      })
    }

    const todayJobs = filterJobsByDateRange(today, today)
    const yesterdayJobs = filterJobsByDateRange(yesterday, yesterday)
    const thisWeekJobs = filterJobsByDateRange(thisWeekStart, today)
    const lastWeekJobs = filterJobsByDateRange(lastWeekStart, lastWeekEnd)
    const thisMonthJobs = filterJobsByDateRange(thisMonthStart, today)
    const lastMonthJobs = filterJobsByDateRange(lastMonthStart, lastMonthEnd)

    const calculateStats = (jobs) => {
      const completed = jobs.filter(j => j.status === 'completed').length
      const total = jobs.length
      return {
        total,
        completed,
        successRate: total > 0 ? (completed / total) * 100 : 0
      }
    }

    return {
      today: calculateStats(todayJobs),
      yesterday: calculateStats(yesterdayJobs),
      thisWeek: calculateStats(thisWeekJobs),
      lastWeek: calculateStats(lastWeekJobs),
      thisMonth: calculateStats(thisMonthJobs),
      lastMonth: calculateStats(lastMonthJobs)
    }
  })

  // Helper to calculate trend
  const calculateTrend = (current, previous) => {
    if (!current || !previous || previous.total === 0) {
      return null
    }
    const change = ((current.total - previous.total) / previous.total) * 100
    return {
      direction: change > 0 ? 'up' : change < 0 ? 'down' : 'neutral',
      percentage: Math.abs(change).toFixed(1),
      label: change > 0 ? 'vs yesterday' : change < 0 ? 'vs yesterday' : 'no change',
      colorClass: change > 0 ? 'text-green-600' : change < 0 ? 'text-red-600' : 'text-gray-600'
    }
  }

  // Analytics metrics
  const analyticsMetrics = computed(() => {
    if (!store.metrics?.analytics) {
      return null
    }

    const analytics = store.metrics.analytics
    const summary = analytics.summary || {}
    const topPosts = analytics.top_posts || []
    const charts = analytics.charts || {}

    // Format likes over time for chart
    const likesOverTime = charts.likes_over_time || []
    const likesLabels = likesOverTime.map(item => formatDateVN(item.date))
    const likesData = likesOverTime.map(item => item.likes || 0)

    // Format engagement over time
    const engagementOverTime = charts.engagement_over_time || []
    const engagementLabels = engagementOverTime.map(item => formatDateVN(item.date))
    const engagementData = engagementOverTime.map(item => item.engagement_rate || 0)

    // Format replies vs reposts
    const repliesOverTime = charts.replies_over_time || []
    const repliesLabels = repliesOverTime.map(item => formatDateVN(item.date))
    const repliesData = repliesOverTime.map(item => item.replies || 0)
    const repostsData = repliesOverTime.map(item => item.reposts || 0)

    return {
      summary: {
        totalPosts: summary.total_posts || 0,
        totalLikes: summary.total_likes || 0,
        totalReplies: summary.total_replies || 0,
        totalReposts: summary.total_reposts || 0,
        totalShares: summary.total_shares || 0,
        totalViews: summary.total_views || 0,
        avgLikesPerPost: summary.avg_likes_per_post || 0,
        avgRepliesPerPost: summary.avg_replies_per_post || 0,
        avgEngagementRate: summary.avg_engagement_rate || 0
      },
      topPosts: topPosts.slice(0, 10), // Top 10 posts
      likesOverTimeChart: {
        labels: likesLabels,
        datasets: [{
          label: 'Likes',
          data: likesData,
          borderColor: chartColors.primary,
          backgroundColor: chartColors.primary + '20',
          fill: true,
          tension: 0.4
        }]
      },
      engagementOverTimeChart: {
        labels: engagementLabels,
        datasets: [{
          label: 'Engagement Rate (%)',
          data: engagementData,
          borderColor: chartColors.success,
          backgroundColor: chartColors.success + '20',
          fill: true,
          tension: 0.4
        }]
      },
      repliesVsRepostsChart: {
        labels: repliesLabels,
        datasets: [
          {
            label: 'Replies',
            data: repliesData,
            backgroundColor: chartColors.info + '80',
            borderColor: chartColors.info
          },
          {
            label: 'Reposts',
            data: repostsData,
            backgroundColor: chartColors.secondary + '80',
            borderColor: chartColors.secondary
          }
        ]
      }
    }
  })

  // Performance metrics
  const performanceMetrics = computed(() => {
    if (!jobsStore.jobs || jobsStore.jobs.length === 0) {
      return {
        avgExecutionTime: 0,
        totalRetries: 0,
        errorRate: 0,
        executionTimeDistribution: { labels: [], datasets: [] },
        retryRateOverTime: { labels: [], datasets: [] },
        errorRateTrend: { labels: [], datasets: [] },
        successVsFailureTimeline: { labels: [], datasets: [] }
      }
    }

    const completedJobs = jobsStore.jobs.filter(j => j.status === 'completed' && j.started_at && j.completed_at)
    const failedJobs = jobsStore.jobs.filter(j => j.status === 'failed')
    const allJobsWithRetries = jobsStore.jobs.filter(j => j.retry_count !== undefined)

    // Calculate average execution time
    let totalExecutionTime = 0
    const executionTimes = []
    completedJobs.forEach(job => {
      try {
        const start = new Date(job.started_at)
        const end = new Date(job.completed_at)
        const duration = (end - start) / 1000 // seconds
        executionTimes.push(duration)
        totalExecutionTime += duration
      } catch (e) {
        // Skip invalid dates
      }
    })
    const avgExecutionTime = completedJobs.length > 0 ? totalExecutionTime / completedJobs.length : 0

    // Calculate total retries
    const totalRetries = allJobsWithRetries.reduce((sum, j) => sum + (j.retry_count || 0), 0)

    // Calculate error rate
    const totalJobs = jobsStore.jobs.length
    const errorRate = totalJobs > 0 ? (failedJobs.length / totalJobs) * 100 : 0

    // Execution time distribution (histogram)
    const timeBuckets = [0, 10, 30, 60, 120, 300, 600] // seconds: 0-10s, 10-30s, 30-60s, 60-120s, 120-300s, 300-600s, 600s+
    const bucketLabels = ['0-10s', '10-30s', '30-60s', '1-2m', '2-5m', '5-10m', '10m+']
    const bucketCounts = new Array(timeBuckets.length).fill(0)
    executionTimes.forEach(time => {
      for (let i = 0; i < timeBuckets.length; i++) {
        if (i === timeBuckets.length - 1 || time < timeBuckets[i + 1]) {
          bucketCounts[i]++
          break
        }
      }
    })

    // Retry rate over time (group by date)
    const retryByDate = {}
    allJobsWithRetries.forEach(job => {
      if (job.completed_at || job.created_at) {
        const date = formatDateVN(job.completed_at || job.created_at)
        if (!retryByDate[date]) {
          retryByDate[date] = { total: 0, retried: 0 }
        }
        retryByDate[date].total++
        if ((job.retry_count || 0) > 0) {
          retryByDate[date].retried++
        }
      }
    })
    const retryDates = Object.keys(retryByDate).sort()
    const retryRates = retryDates.map(date => {
      const data = retryByDate[date]
      return data.total > 0 ? (data.retried / data.total) * 100 : 0
    })

    // Error rate trend (group by date)
    const errorByDate = {}
    jobsStore.jobs.forEach(job => {
      if (job.completed_at || job.created_at) {
        const date = formatDateVN(job.completed_at || job.created_at)
        if (!errorByDate[date]) {
          errorByDate[date] = { total: 0, failed: 0 }
        }
        errorByDate[date].total++
        if (job.status === 'failed') {
          errorByDate[date].failed++
        }
      }
    })
    const errorDates = Object.keys(errorByDate).sort()
    const errorRates = errorDates.map(date => {
      const data = errorByDate[date]
      return data.total > 0 ? (data.failed / data.total) * 100 : 0
    })

    // Success vs Failure timeline
    const timelineByDate = {}
    jobsStore.jobs.forEach(job => {
      if (job.completed_at || (job.status === 'failed' && job.created_at)) {
        const date = formatDateVN(job.completed_at || job.created_at)
        if (!timelineByDate[date]) {
          timelineByDate[date] = { success: 0, failure: 0 }
        }
        if (job.status === 'completed') {
          timelineByDate[date].success++
        } else if (job.status === 'failed') {
          timelineByDate[date].failure++
        }
      }
    })
    const timelineDates = Object.keys(timelineByDate).sort()
    const successData = timelineDates.map(date => timelineByDate[date].success)
    const failureData = timelineDates.map(date => timelineByDate[date].failure)

    return {
      avgExecutionTime,
      totalRetries,
      errorRate,
      executionTimeDistribution: {
        labels: bucketLabels,
        datasets: [{
          label: 'Số lượng jobs',
          data: bucketCounts,
          backgroundColor: chartColors.primary + '80',
          borderColor: chartColors.primary,
          borderWidth: 1
        }]
      },
      retryRateOverTime: {
        labels: retryDates,
        datasets: [{
          label: 'Retry Rate (%)',
          data: retryRates,
          borderColor: chartColors.warning,
          backgroundColor: chartColors.warning + '20',
          fill: true,
          tension: 0.4
        }]
      },
      errorRateTrend: {
        labels: errorDates,
        datasets: [{
          label: 'Error Rate (%)',
          data: errorRates,
          borderColor: chartColors.error,
          backgroundColor: chartColors.error + '20',
          fill: true,
          tension: 0.4
        }]
      },
      successVsFailureTimeline: {
        labels: timelineDates,
        datasets: [
          {
            label: 'Success',
            data: successData,
            backgroundColor: chartColors.success + '80',
            borderColor: chartColors.success,
            fill: true
          },
          {
            label: 'Failure',
            data: failureData,
            backgroundColor: chartColors.error + '80',
            borderColor: chartColors.error,
            fill: true
          }
        ]
      }
    }
  })

  return {
    // State
    stats: computed(() => store.stats),
    metrics: computed(() => store.metrics),
    activity: computed(() => store.activity),
    isStale: computed(() => store.isStale),
    loading,
    error,
    // Methods
    fetchStats,
    fetchMetrics,
    fetchActivity,
    refreshAll,
    clearError,
    // Chart data
    postsTimelineData,
    hourlyDistributionData,
    statusDistributionData,
    successRateData,
    platformDistributionData,
    platformSuccessRatesData,
    // Comparison metrics
    comparisonMetrics,
    calculateTrend,
    // Performance metrics
    performanceMetrics,
    // Analytics metrics
    analyticsMetrics
  }
}
