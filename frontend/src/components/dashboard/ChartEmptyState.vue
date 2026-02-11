<template>
  <div class="flex flex-col items-center justify-center py-8 px-4 text-center" :style="{ height }">
    <div class="mb-4">
      <component 
        v-if="iconComponent" 
        :is="iconComponent" 
        class="w-12 h-12 text-gray-300" 
        aria-hidden="true" 
      />
      <div v-else class="w-12 h-12 bg-gray-200 rounded-lg flex items-center justify-center">
        <ChartBarIcon class="w-6 h-6 text-gray-400" aria-hidden="true" />
      </div>
    </div>
    
    <h3 class="text-lg font-medium text-gray-900 mb-2">
      {{ title || 'No Data Available' }}
    </h3>
    
    <p class="text-sm text-gray-500 mb-4 max-w-sm">
      {{ description || defaultDescription }}
    </p>
    
    <div v-if="showActions" class="space-y-2">
      <Button 
        v-if="showRefresh"
        size="sm" 
        variant="outline" 
        @click="$emit('refresh')"
      >
        <ArrowPathIcon class="w-4 h-4 mr-1" aria-hidden="true" />
        Refresh Data
      </Button>
      
      <Button 
        v-if="showFilters"
        size="sm" 
        variant="ghost" 
        @click="$emit('show-filters')"
      >
        <AdjustmentsHorizontalIcon class="w-4 h-4 mr-1" aria-hidden="true" />
        Adjust Filters
      </Button>
    </div>
    
    <div v-if="suggestions && suggestions.length > 0" class="mt-4 text-left">
      <p class="text-xs font-medium text-gray-700 mb-2">Suggestions:</p>
      <ul class="text-xs text-gray-600 space-y-1">
        <li v-for="suggestion in suggestions" :key="suggestion" class="flex items-start">
          <span class="w-1 h-1 bg-gray-400 rounded-full mt-1.5 mr-2 shrink-0"></span>
          {{ suggestion }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { 
  ChartBarIcon, 
  ArrowPathIcon, 
  AdjustmentsHorizontalIcon,
  DocumentIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'
import * as HeroIcons from '@heroicons/vue/24/outline'
import Button from '@/components/common/Button.vue'

const props = defineProps({
  type: {
    type: String,
    default: 'general',
    validator: (value) => [
      'general', 'line-chart', 'bar-chart', 'pie-chart', 
      'area-chart', 'no-data', 'empty-filter', 'loading-error'
    ].includes(value)
  },
  title: {
    type: String,
    default: null
  },
  description: {
    type: String,
    default: null
  },
  iconName: {
    type: String,
    default: null
  },
  height: {
    type: String,
    default: '250px'
  },
  showActions: {
    type: Boolean,
    default: true
  },
  showRefresh: {
    type: Boolean,
    default: true
  },
  showFilters: {
    type: Boolean,
    default: true
  },
  suggestions: {
    type: Array,
    default: () => []
  }
})

defineEmits(['refresh', 'show-filters'])

const iconComponent = computed(() => {
  if (props.iconName) {
    return HeroIcons[props.iconName] || null
  }
  
  // Default icons based on type - using only available icons
  const typeIcons = {
    'line-chart': 'ChartBarIcon',  // Use ChartBarIcon instead of ChartLineIcon
    'bar-chart': 'ChartBarIcon', 
    'pie-chart': 'ChartBarIcon',   // Use ChartBarIcon instead of ChartPieIcon
    'area-chart': 'ChartBarIcon',  // Use ChartBarIcon instead of ChartAreaIcon
    'no-data': 'DocumentIcon',     // This should exist
    'empty-filter': 'AdjustmentsHorizontalIcon', // Use existing icon
    'loading-error': 'ExclamationTriangleIcon'
  }
  
  const iconName = typeIcons[props.type]
  return iconName ? HeroIcons[iconName] : null
})

const defaultDescription = computed(() => {
  const descriptions = {
    'line-chart': 'No time series data available to display trends.',
    'bar-chart': 'No data available for distribution analysis.',
    'pie-chart': 'No data available to show proportional breakdown.',
    'area-chart': 'No data available to display area trends.',
    'no-data': 'Data has not been collected yet for the selected time period.',
    'empty-filter': 'No results match your current filter criteria.',
    'loading-error': 'Unable to load data. Please try again.',
    'general': 'No data available to display.'
  }
  
  return descriptions[props.type] || descriptions.general
})
</script>

<style scoped>
/* Animation for empty state */
.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>