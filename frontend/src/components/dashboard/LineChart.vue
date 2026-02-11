<template>
  <div 
    class="chart-container" 
    :style="{ height: chartHeight }"
    role="img"
    :aria-label="ariaLabel || 'Line chart showing data trends over time'"
  >
    <ChartSkeleton v-if="loading" :height="chartHeight" />
    <!-- ChartEmptyState temporarily disabled for debugging -->
    <div v-else-if="!chartData || !chartData.datasets || chartData.datasets.length === 0 || isDataEmpty" class="flex items-center justify-center h-full">
      <div class="text-center">
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Timeline Data</h3>
        <p class="text-sm text-gray-500">No data available to display trends.</p>
      </div>
    </div>
    <Line
      v-else
      :data="processedChartData"
      :options="mergedOptions"
      aria-hidden="true"
    />
    <!-- Data table alternative for accessibility (charts.csv recommendation) -->
    <div v-if="showDataTable && processedChartData && processedChartData.datasets && processedChartData.datasets.length > 0 && processedChartData.labels && processedChartData.labels.length > 0" class="mt-4" role="region" aria-label="Chart data table">
      <details class="data-table-container">
        <summary 
          class="data-table-summary"
          :aria-label="`View ${ariaLabel || 'chart'} data as table`"
          tabindex="0"
          role="button"
        >
          <span class="flex items-center gap-2">
            <svg class="w-4 h-4 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            <span>View data as table</span>
          </span>
        </summary>
        <div class="data-table-wrapper">
          <table 
            class="data-table"
            role="table"
            :aria-label="`Data table for ${ariaLabel || 'chart'}`"
          >
            <thead>
              <tr>
                <th scope="col" class="data-table-header">
                  Date/Time
                </th>
                <th 
                  v-for="dataset in processedChartData.datasets" 
                  :key="dataset.label"
                  scope="col"
                  class="data-table-header"
                >
                  {{ dataset.label }}
                </th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(label, index) in processedChartData.labels" 
                :key="index"
                class="data-table-row"
              >
                <th scope="row" class="data-table-row-header">
                  {{ label || '-' }}
                </th>
                <td 
                  v-for="dataset in processedChartData.datasets" 
                  :key="dataset.label"
                  class="data-table-cell"
                >
                  {{ formatTableValue(dataset.data[index]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </details>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { defaultChartOptions, getResponsiveChartOptions, getResponsiveChartHeight, getColorblindPattern } from '@/utils/chartConfig'
import ChartSkeleton from '@/components/dashboard/ChartSkeleton.vue'
// import ChartEmptyState from '@/components/dashboard/ChartEmptyState.vue' // Temporarily disabled

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

const props = defineProps({
  chartData: {
    type: Object,
    default: () => ({ labels: [], datasets: [] })
  },
  options: {
    type: Object,
    default: () => ({})
  },
  height: {
    type: String,
    default: null // Will use responsive height if not provided
  },
  loading: {
    type: Boolean,
    default: false
  },
  ariaLabel: {
    type: String,
    default: null
  },
  showDataTable: {
    type: Boolean,
    default: false // Optional: show data table for accessibility
  }
})

defineEmits(['refresh', 'show-filters'])

// Check if data is effectively empty (all datasets have no meaningful data)
const isDataEmpty = computed(() => {
  if (!props.chartData?.datasets?.length) return true
  
  return props.chartData.datasets.every(dataset => {
    const data = dataset.data || []
    return data.length === 0 || data.every(value => value === null || value === undefined || value === 0)
  })
})

// Use responsive height if not provided
const chartHeight = computed(() => {
  return props.height || getResponsiveChartHeight('300px')
})

// Apply UI/UX Pro Max guidelines for line charts (charts.csv line 1)
// Primary: #0080FF for trend/time-series, Clear line patterns for colorblind users
const processedChartData = computed(() => {
  if (!props.chartData || !props.chartData.datasets) {
    return props.chartData
  }

  return {
    ...props.chartData,
    datasets: props.chartData.datasets.map((dataset, index) => {
      // Use primary trend color if not specified
      const borderColor = dataset.borderColor || '#0080FF'
      const backgroundColor = dataset.backgroundColor || borderColor
      
      // Determine color key for colorblind patterns
      // Try to match color to palette
      let colorKey = 'primary'
      if (borderColor.includes('16a34a') || borderColor.includes('success')) colorKey = 'success'
      else if (borderColor.includes('dc2626') || borderColor.includes('error')) colorKey = 'error'
      else if (borderColor.includes('d97706') || borderColor.includes('warning')) colorKey = 'warning'
      else if (borderColor.includes('4b5563') || borderColor.includes('info')) colorKey = 'info'
      
      // Get colorblind-friendly pattern
      const pattern = getColorblindPattern(colorKey)
      
      return {
        ...dataset,
        borderColor: borderColor,
        backgroundColor: backgroundColor,
        fill: false, // Line chart doesn't fill
        tension: 0.4, // Smooth curve
        ...pattern // Add colorblind pattern (dashed/dotted lines)
      }
    })
  }
})

const mergedOptions = computed(() => {
  return getResponsiveChartOptions({
    ...defaultChartOptions,
    ...props.options,
    elements: {
      line: {
        tension: 0.4, // Smooth curve (charts.csv recommendation)
        borderWidth: 2, // Clear line patterns
        borderCapStyle: 'round',
        borderJoinStyle: 'round'
      },
      point: {
        radius: 4, // Visible points
        hoverRadius: 6,
        hoverBorderWidth: 2,
        pointStyle: 'circle',
        backgroundColor: '#ffffff',
        borderWidth: 2
      }
    },
    scales: {
      ...defaultChartOptions.scales,
      ...props.options.scales
    },
    // Accessibility: make chart keyboard navigable
    onHover: (event, activeElements) => {
      // Chart.js handles hover automatically
    },
    onClick: (event, activeElements) => {
      // Chart.js handles click automatically
    }
  })
})

// Format table values with thousands separators
const formatTableValue = (value) => {
  if (value === null || value === undefined) return '-'
  if (typeof value === 'number') {
    return new Intl.NumberFormat('vi-VN').format(value)
  }
  return value
}
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  max-width: 100%;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s ease-in-out;
}

.chart-container:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

@media (min-width: 640px) {
  .chart-container {
    padding: 1rem;
  }
}

@media (min-width: 1024px) {
  .chart-container {
    padding: 1.25rem;
  }
}

/* Data Table Styles */
.data-table-container {
  margin-top: 1rem;
}

.data-table-summary {
  display: flex;
  align-items: center;
  padding: 0.625rem 0.875rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #4b5563;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  user-select: none;
  list-style: none;
}

.data-table-summary::-webkit-details-marker {
  display: none;
}

.data-table-summary:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
  color: #111827;
}

.data-table-summary:focus {
  outline: none;
  ring: 2px;
  ring-color: #2563eb;
  ring-offset: 2px;
}

.data-table-container[open] .data-table-summary svg {
  transform: rotate(180deg);
}

.data-table-wrapper {
  margin-top: 0.75rem;
  max-height: 400px;
  overflow-y: auto;
  overflow-x: auto;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  background: #ffffff;
  box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.data-table-header {
  padding: 0.75rem 1rem;
  font-weight: 600;
  font-size: 0.8125rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #374151;
  background: #f9fafb;
  border-bottom: 2px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table-header:first-child {
  min-width: 140px;
}

.data-table-row {
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.15s ease-in-out;
}

.data-table-row:hover {
  background-color: #f9fafb;
}

.data-table-row:last-child {
  border-bottom: none;
}

.data-table-row-header {
  padding: 0.75rem 1rem;
  font-weight: 500;
  color: #111827;
  background: #ffffff;
  white-space: nowrap;
  text-align: left;
}

.data-table-cell {
  padding: 0.75rem 1rem;
  color: #4b5563;
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
}

/* Scrollbar styling */
.data-table-wrapper::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.data-table-wrapper::-webkit-scrollbar-track {
  background: #f9fafb;
  border-radius: 4px;
}

.data-table-wrapper::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 4px;
}

.data-table-wrapper::-webkit-scrollbar-thumb:hover {
  background: #9ca3af;
}

@media (max-width: 640px) {
  .data-table-header,
  .data-table-row-header,
  .data-table-cell {
    padding: 0.5rem 0.75rem;
    font-size: 0.8125rem;
  }
  
  .data-table-wrapper {
    max-height: 300px;
  }
}
</style>
