<template>
  <Card class="mb-6">
    <template #header>
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <AdjustmentsHorizontalIcon class="w-5 h-5 text-gray-600" aria-hidden="true" />
          <h3 class="text-lg font-semibold text-gray-900">Filters</h3>
        </div>
        <div class="flex items-center gap-2">
          <Button 
            size="sm" 
            variant="ghost" 
            @click="resetFilters"
            :disabled="!hasActiveFilters"
          >
            <ArrowPathIcon class="w-4 h-4 mr-1" aria-hidden="true" />
            Reset
          </Button>
          <Button 
            size="sm" 
            variant="outline" 
            @click="toggleCollapsed"
          >
            <ChevronUpIcon 
              v-if="!collapsed" 
              class="w-4 h-4" 
              aria-hidden="true" 
            />
            <ChevronDownIcon 
              v-else 
              class="w-4 h-4" 
              aria-hidden="true" 
            />
          </Button>
        </div>
      </div>
    </template>

    <div v-show="!collapsed" class="space-y-4">
      <!-- Date Range Filter -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Date Range -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Date Range
          </label>
          <select 
            v-model="localFilters.dateRange"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            @change="emitFilters"
          >
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="last-7-days">Last 7 days</option>
            <option value="last-30-days">Last 30 days</option>
            <option value="this-month">This month</option>
            <option value="last-month">Last month</option>
            <option value="custom">Custom range</option>
          </select>
        </div>

        <!-- Job Type Filter -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Job Type
          </label>
          <select 
            v-model="localFilters.jobType"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            @change="emitFilters"
          >
            <option value="">All Types</option>
            <option value="post">Post Thread</option>
            <option value="reply">Reply</option>
            <option value="like">Like</option>
            <option value="follow">Follow</option>
            <option value="unfollow">Unfollow</option>
          </select>
        </div>

        <!-- Platform Filter -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Platform
          </label>
          <select 
            v-model="localFilters.platform"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            @change="emitFilters"
          >
            <option value="">All Platforms</option>
            <option value="threads">Threads</option>
            <option value="instagram">Instagram</option>
            <option value="facebook">Facebook</option>
          </select>
        </div>

        <!-- Status Filter -->
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Status
          </label>
          <select 
            v-model="localFilters.status"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            @change="emitFilters"
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      <!-- Custom Date Range (only show when custom is selected) -->
      <div v-if="localFilters.dateRange === 'custom'" class="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-gray-200">
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            Start Date
          </label>
          <input 
            v-model="localFilters.startDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            @change="emitFilters"
          />
        </div>
        <div class="space-y-2">
          <label class="block text-sm font-medium text-gray-700">
            End Date
          </label>
          <input 
            v-model="localFilters.endDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-sm"
            @change="emitFilters"
          />
        </div>
      </div>

      <!-- Active Filters Display -->
      <div v-if="hasActiveFilters" class="pt-3 border-t border-gray-200">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-sm font-medium text-gray-700">Active Filters:</span>
        </div>
        <div class="flex flex-wrap gap-2">
          <span 
            v-for="filter in activeFiltersList" 
            :key="filter.key"
            class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
          >
            {{ filter.label }}: {{ filter.value }}
            <button 
              @click="removeFilter(filter.key)"
              class="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full text-primary-400 hover:bg-primary-200 hover:text-primary-600 focus:outline-none focus:bg-primary-200"
            >
              <XMarkIcon class="w-3 h-3" aria-hidden="true" />
            </button>
          </span>
        </div>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { 
  AdjustmentsHorizontalIcon, 
  ArrowPathIcon,
  ChevronUpIcon,
  ChevronDownIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  collapsed: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'update:collapsed', 'change'])

const collapsed = ref(props.collapsed)
const localFilters = ref({
  dateRange: 'last-7-days',
  jobType: '',
  platform: '',
  status: '',
  startDate: '',
  endDate: '',
  ...props.modelValue
})

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  localFilters.value = {
    dateRange: 'last-7-days',
    jobType: '',
    platform: '',
    status: '',
    startDate: '',
    endDate: '',
    ...newValue
  }
}, { deep: true })

// Check if any filters are active (non-default)
const hasActiveFilters = computed(() => {
  return localFilters.value.dateRange !== 'last-7-days' ||
         localFilters.value.jobType !== '' ||
         localFilters.value.platform !== '' ||
         localFilters.value.status !== '' ||
         localFilters.value.startDate !== '' ||
         localFilters.value.endDate !== ''
})

// Get list of active filters for display
const activeFiltersList = computed(() => {
  const filters = []
  
  if (localFilters.value.dateRange !== 'last-7-days') {
    const dateRangeLabels = {
      'today': 'Today',
      'yesterday': 'Yesterday',
      'last-7-days': 'Last 7 days',
      'last-30-days': 'Last 30 days',
      'this-month': 'This month',
      'last-month': 'Last month',
      'custom': 'Custom range'
    }
    filters.push({
      key: 'dateRange',
      label: 'Date Range',
      value: dateRangeLabels[localFilters.value.dateRange] || localFilters.value.dateRange
    })
  }
  
  if (localFilters.value.jobType) {
    const jobTypeLabels = {
      'post': 'Post Thread',
      'reply': 'Reply',
      'like': 'Like',
      'follow': 'Follow',
      'unfollow': 'Unfollow'
    }
    filters.push({
      key: 'jobType',
      label: 'Job Type',
      value: jobTypeLabels[localFilters.value.jobType] || localFilters.value.jobType
    })
  }
  
  if (localFilters.value.platform) {
    filters.push({
      key: 'platform',
      label: 'Platform',
      value: localFilters.value.platform.charAt(0).toUpperCase() + localFilters.value.platform.slice(1)
    })
  }
  
  if (localFilters.value.status) {
    filters.push({
      key: 'status',
      label: 'Status',
      value: localFilters.value.status.charAt(0).toUpperCase() + localFilters.value.status.slice(1)
    })
  }
  
  return filters
})

const toggleCollapsed = () => {
  collapsed.value = !collapsed.value
  emit('update:collapsed', collapsed.value)
}

const resetFilters = () => {
  localFilters.value = {
    dateRange: 'last-7-days',
    jobType: '',
    platform: '',
    status: '',
    startDate: '',
    endDate: ''
  }
  emitFilters()
}

const removeFilter = (filterKey) => {
  if (filterKey === 'dateRange') {
    localFilters.value.dateRange = 'last-7-days'
  } else {
    localFilters.value[filterKey] = ''
  }
  emitFilters()
}

const emitFilters = () => {
  emit('update:modelValue', { ...localFilters.value })
  emit('change', { ...localFilters.value })
}

onMounted(() => {
  // Emit initial filters if they have values
  if (hasActiveFilters.value) {
    emitFilters()
  }
})
</script>

<style scoped>
/* Custom styles for filter inputs */
select:focus,
input:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* Smooth transitions */
.space-y-4 > * {
  transition: all 0.2s ease-in-out;
}
</style>