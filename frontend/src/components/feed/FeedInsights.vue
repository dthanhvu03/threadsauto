<template>
  <Modal
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="📊 Feed Insights"
    size="xl"
  >
    <template #header>
      <div class="flex items-center justify-between">
        <h3 class="text-lg font-semibold text-gray-900">Feed Insights</h3>
        <button
          @click="$emit('update:modelValue', false)"
          class="text-gray-400 hover:text-gray-600 transition-colors"
          aria-label="Close"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </template>

    <!-- Empty State -->
    <div v-if="feedItems.length === 0" class="text-center py-12">
      <svg class="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
      <p class="text-gray-600 text-lg font-medium mb-2">No data available</p>
      <p class="text-gray-500 text-sm">Load feed items to see insights and analytics.</p>
    </div>

    <!-- Insights Content -->
    <div v-else class="space-y-6">
      <!-- Engagement Analysis -->
      <div class="bg-white border border-gray-200 rounded-lg p-4 sm:p-6">
        <h4 class="text-base font-semibold text-gray-900 mb-4">Engagement Analysis</h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <!-- Likes -->
          <div class="border border-gray-200 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-600 mb-3">Likes</div>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Min:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.likes.min) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Max:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.likes.max) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Average:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.likes.avg) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Median:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.likes.median) }}</span>
              </div>
            </div>
          </div>

          <!-- Replies -->
          <div class="border border-gray-200 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-600 mb-3">Replies</div>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Min:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.replies.min) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Max:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.replies.max) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Average:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.replies.avg) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Median:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.replies.median) }}</span>
              </div>
            </div>
          </div>

          <!-- Reposts -->
          <div class="border border-gray-200 rounded-lg p-4">
            <div class="text-sm font-medium text-gray-600 mb-3">Reposts</div>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Min:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.reposts.min) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Max:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.reposts.max) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Average:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.reposts.avg) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-xs text-gray-500">Median:</span>
                <span class="text-sm font-semibold">{{ formatNumber(engagementStats.reposts.median) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Time Distribution -->
      <div class="bg-white border border-gray-200 rounded-lg p-4 sm:p-6">
        <h4 class="text-base font-semibold text-gray-900 mb-4">Time Distribution</h4>
        
        <!-- Hourly Distribution -->
        <div class="mb-6">
          <h5 class="text-sm font-medium text-gray-700 mb-3">Posts by Hour of Day</h5>
          <div class="flex items-end gap-1 h-32">
            <div
              v-for="(count, hour) in hourlyDistribution"
              :key="hour"
              class="flex-1 flex flex-col items-center group"
            >
              <div
                class="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600 relative"
                :style="{ height: maxHourlyCount > 0 ? `${(count / maxHourlyCount) * 100}%` : '0%', minHeight: count > 0 ? '4px' : '0' }"
                :title="`${hour}:00 - ${count} posts`"
              >
                <span
                  v-if="count > 0"
                  class="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap"
                >
                  {{ count }}
                </span>
              </div>
              <span class="text-xs text-gray-500 mt-1">{{ hour }}</span>
            </div>
          </div>
        </div>

        <!-- Daily Distribution (Last 7 Days) -->
        <div>
          <h5 class="text-sm font-medium text-gray-700 mb-3">Posts by Day (Last 7 Days)</h5>
          <div class="flex items-end gap-2 h-32">
            <div
              v-for="(dayData, index) in dailyDistribution"
              :key="index"
              class="flex-1 flex flex-col items-center group"
            >
              <div
                class="w-full bg-purple-500 rounded-t transition-all hover:bg-purple-600 relative"
                :style="{ height: maxDailyCount > 0 ? `${(dayData.count / maxDailyCount) * 100}%` : '0%', minHeight: dayData.count > 0 ? '4px' : '0' }"
                :title="`${dayData.label} - ${dayData.count} posts`"
              >
                <span
                  v-if="dayData.count > 0"
                  class="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap"
                >
                  {{ dayData.count }}
                </span>
              </div>
              <span class="text-xs text-gray-500 mt-1 text-center">{{ dayData.label }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Top Performing Posts -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <!-- Top Posts by Likes -->
        <div class="bg-white border border-gray-200 rounded-lg p-4 sm:p-6">
          <h4 class="text-base font-semibold text-gray-900 mb-4">Top Posts by Likes</h4>
          <div v-if="topPostsByLikes.length === 0" class="text-sm text-gray-500 text-center py-4">
            No posts with likes
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="(post, index) in topPostsByLikes"
              :key="post.post_id"
              class="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
            >
              <div class="flex items-start justify-between gap-2 mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-semibold text-gray-400">#{{ index + 1 }}</span>
                  <span class="text-sm font-medium text-gray-900">@{{ post.username }}</span>
                </div>
                <span class="text-sm font-semibold text-blue-600">{{ formatNumber(post.like_count) }} ❤️</span>
              </div>
              <p class="text-xs text-gray-600 line-clamp-2">{{ post.text || 'No text content' }}</p>
            </div>
          </div>
        </div>

        <!-- Top Posts by Replies -->
        <div class="bg-white border border-gray-200 rounded-lg p-4 sm:p-6">
          <h4 class="text-base font-semibold text-gray-900 mb-4">Top Posts by Replies</h4>
          <div v-if="topPostsByReplies.length === 0" class="text-sm text-gray-500 text-center py-4">
            No posts with replies
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="(post, index) in topPostsByReplies"
              :key="post.post_id"
              class="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 transition-colors"
            >
              <div class="flex items-start justify-between gap-2 mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-semibold text-gray-400">#{{ index + 1 }}</span>
                  <span class="text-sm font-medium text-gray-900">@{{ post.username }}</span>
                </div>
                <span class="text-sm font-semibold text-green-600">{{ formatNumber(post.reply_count) }} 💬</span>
              </div>
              <p class="text-xs text-gray-600 line-clamp-2">{{ post.text || 'No text content' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Media Breakdown -->
      <div class="bg-white border border-gray-200 rounded-lg p-4 sm:p-6">
        <h4 class="text-base font-semibold text-gray-900 mb-4">Media Breakdown</h4>
        <div class="space-y-4">
          <!-- Posts with Media -->
          <div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm text-gray-700">Posts with Media</span>
              <span class="text-sm font-semibold text-gray-900">
                {{ mediaBreakdown.withMedia }} / {{ feedItems.length }} ({{ mediaBreakdown.withMediaPercent }}%)
              </span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-3">
              <div
                class="bg-blue-500 h-3 rounded-full transition-all"
                :style="{ width: `${mediaBreakdown.withMediaPercent}%` }"
              ></div>
            </div>
          </div>

          <!-- Posts without Media -->
          <div>
            <div class="flex justify-between items-center mb-2">
              <span class="text-sm text-gray-700">Posts without Media</span>
              <span class="text-sm font-semibold text-gray-900">
                {{ mediaBreakdown.withoutMedia }} / {{ feedItems.length }} ({{ mediaBreakdown.withoutMediaPercent }}%)
              </span>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-3">
              <div
                class="bg-gray-400 h-3 rounded-full transition-all"
                :style="{ width: `${mediaBreakdown.withoutMediaPercent}%` }"
              ></div>
            </div>
          </div>

          <!-- Media Type Breakdown -->
          <div v-if="mediaBreakdown.withMedia > 0" class="pt-4 border-t border-gray-200">
            <div class="grid grid-cols-2 gap-4">
              <!-- Images -->
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm text-gray-700">Images</span>
                  <span class="text-sm font-semibold text-gray-900">
                    {{ mediaBreakdown.images }} ({{ mediaBreakdown.imagesPercent }}%)
                  </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div
                    class="bg-green-500 h-3 rounded-full transition-all"
                    :style="{ width: `${mediaBreakdown.imagesPercent}%` }"
                  ></div>
                </div>
              </div>

              <!-- Videos -->
              <div>
                <div class="flex justify-between items-center mb-2">
                  <span class="text-sm text-gray-700">Videos</span>
                  <span class="text-sm font-semibold text-gray-900">
                    {{ mediaBreakdown.videos }} ({{ mediaBreakdown.videosPercent }}%)
                  </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-3">
                  <div
                    class="bg-red-500 h-3 rounded-full transition-all"
                    :style="{ width: `${mediaBreakdown.videosPercent}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Modal>
</template>

<script setup>
import { computed } from 'vue'
import Modal from '@/components/common/Modal.vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  feedItems: {
    type: Array,
    default: () => []
  }
})

defineEmits(['update:modelValue'])

// Helper function to format numbers
const formatNumber = (num) => {
  if (num === null || num === undefined || isNaN(num)) return '0'
  return new Intl.NumberFormat('en-US').format(Math.round(num))
}

// Helper function to calculate median
const calculateMedian = (values) => {
  if (!values || values.length === 0) return 0
  const sorted = [...values].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid]
}

// Engagement Stats
const engagementStats = computed(() => {
  if (props.feedItems.length === 0) {
    return {
      likes: { min: 0, max: 0, avg: 0, median: 0 },
      replies: { min: 0, max: 0, avg: 0, median: 0 },
      reposts: { min: 0, max: 0, avg: 0, median: 0 }
    }
  }

  const likes = props.feedItems.map(item => item.like_count || 0)
  const replies = props.feedItems.map(item => item.reply_count || 0)
  const reposts = props.feedItems.map(item => item.repost_count || 0)

  const calculateStats = (values) => {
    const validValues = values.filter(v => v !== null && v !== undefined && !isNaN(v))
    if (validValues.length === 0) {
      return { min: 0, max: 0, avg: 0, median: 0 }
    }
    const sum = validValues.reduce((a, b) => a + b, 0)
    return {
      min: Math.min(...validValues),
      max: Math.max(...validValues),
      avg: sum / validValues.length,
      median: calculateMedian(validValues)
    }
  }

  return {
    likes: calculateStats(likes),
    replies: calculateStats(replies),
    reposts: calculateStats(reposts)
  }
})

// Hourly Distribution
const hourlyDistribution = computed(() => {
  const hours = new Array(24).fill(0)
  
  props.feedItems.forEach(item => {
    let date
    if (item.timestamp_iso) {
      date = new Date(item.timestamp_iso)
    } else if (item.timestamp) {
      date = new Date(item.timestamp * 1000)
    } else {
      return // Skip if no timestamp
    }
    
    if (!isNaN(date.getTime())) {
      const hour = date.getUTCHours()
      hours[hour]++
    }
  })
  
  return hours
})

const maxHourlyCount = computed(() => {
  return Math.max(...hourlyDistribution.value, 1)
})

// Daily Distribution (Last 7 Days)
const dailyDistribution = computed(() => {
  const days = []
  const now = new Date()
  
  // Create array for last 7 days
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now)
    date.setUTCDate(date.getUTCDate() - i)
    date.setUTCHours(0, 0, 0, 0)
    
    const label = date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
    days.push({ date, label, count: 0 })
  }
  
  // Count posts per day
  props.feedItems.forEach(item => {
    let postDate
    if (item.timestamp_iso) {
      postDate = new Date(item.timestamp_iso)
    } else if (item.timestamp) {
      postDate = new Date(item.timestamp * 1000)
    } else {
      return // Skip if no timestamp
    }
    
    if (!isNaN(postDate.getTime())) {
      postDate.setUTCHours(0, 0, 0, 0)
      
      // Find matching day
      const dayIndex = days.findIndex(day => {
        return day.date.getTime() === postDate.getTime()
      })
      
      if (dayIndex !== -1) {
        days[dayIndex].count++
      }
    }
  })
  
  return days
})

const maxDailyCount = computed(() => {
  return Math.max(...dailyDistribution.value.map(d => d.count), 1)
})

// Top Posts by Likes
const topPostsByLikes = computed(() => {
  return [...props.feedItems]
    .filter(item => (item.like_count || 0) > 0)
    .sort((a, b) => (b.like_count || 0) - (a.like_count || 0))
    .slice(0, 10)
})

// Top Posts by Replies
const topPostsByReplies = computed(() => {
  return [...props.feedItems]
    .filter(item => (item.reply_count || 0) > 0)
    .sort((a, b) => (b.reply_count || 0) - (a.reply_count || 0))
    .slice(0, 10)
})

// Media Breakdown
const mediaBreakdown = computed(() => {
  const total = props.feedItems.length
  if (total === 0) {
    return {
      withMedia: 0,
      withoutMedia: 0,
      withMediaPercent: 0,
      withoutMediaPercent: 0,
      images: 0,
      videos: 0,
      imagesPercent: 0,
      videosPercent: 0
    }
  }

  let withMedia = 0
  let withoutMedia = 0
  let images = 0
  let videos = 0

  props.feedItems.forEach(item => {
    const hasMedia = (item.media_count && item.media_count > 0) || 
                     (item.media_urls && item.media_urls.length > 0) ||
                     (item.media_type !== null && item.media_type !== undefined)
    
    if (hasMedia) {
      withMedia++
      
      // Check media type (1 = image, 2 = video)
      if (item.media_type === 1) {
        images++
      } else if (item.media_type === 2) {
        videos++
      }
    } else {
      withoutMedia++
    }
  })

  const withMediaPercent = total > 0 ? Math.round((withMedia / total) * 100) : 0
  const withoutMediaPercent = total > 0 ? Math.round((withoutMedia / total) * 100) : 0
  const imagesPercent = withMedia > 0 ? Math.round((images / withMedia) * 100) : 0
  const videosPercent = withMedia > 0 ? Math.round((videos / withMedia) * 100) : 0

  return {
    withMedia,
    withoutMedia,
    withMediaPercent,
    withoutMediaPercent,
    images,
    videos,
    imagesPercent,
    videosPercent
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
