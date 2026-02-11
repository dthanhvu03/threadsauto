<template>
  <div 
    class="chart-container" 
    :style="{ height: chartHeight }"
    role="img"
    :aria-label="ariaLabel || 'Pie chart showing part-to-whole relationships'"
  >
    <ChartSkeleton v-if="loading" :height="chartHeight" />
    <!-- ChartEmptyState temporarily disabled for debugging -->
    <div v-else-if="!chartData || !chartData.datasets || chartData.datasets.length === 0 || isDataEmpty" class="flex items-center justify-center h-full">
      <div class="text-center">
        <h3 class="text-lg font-medium text-gray-900 mb-2">No Proportion Data</h3>
        <p class="text-sm text-gray-500">No data available to show proportional breakdown.</p>
      </div>
    </div>
    <Pie
      v-else
      :data="chartData"
      :options="mergedOptions"
      aria-hidden="true"
    />
    <!-- Data table alternative for accessibility (charts.csv: Pie charts hard for accessibility) -->
    <div v-if="showDataTable && chartData && chartData.datasets.length > 0" class="mt-4" role="region" aria-label="Chart data table">
      <details class="data-table-container">
        <summary 
          class="data-table-summary"
          :aria-label="`View ${ariaLabel || 'pie chart'} data as table (recommended for accessibility)`"
          tabindex="0"
          role="button"
        >
          <span class="flex items-center gap-2">
            <svg class="w-4 h-4 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
            <span>View data as table (recommended for accessibility)</span>
          </span>
        </summary>
        <div class="data-table-wrapper">
          <table 
            class="data-table"
            role="table"
            :aria-label="`Data table for ${ariaLabel || 'pie chart'}`"
          >
            <thead>
              <tr>
                <th scope="col" class="data-table-header">Label</th>
                <th scope="col" class="data-table-header">Value</th>
                <th scope="col" class="data-table-header">Percentage</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="(label, index) in chartData.labels" 
                :key="index"
                class="data-table-row"
              >
                <td class="data-table-row-header">{{ label || '-' }}</td>
                <td class="data-table-cell">{{ formatTableValue(chartData.datasets[0]?.data[index]) }}</td>
                <td class="data-table-cell">
                  {{ totalValue > 0 ? ((chartData.datasets[0]?.data[index] / totalValue) * 100).toFixed(1) : 0 }}%
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
import { Pie } from 'vue-chartjs'
import { getResponsiveChartHeight } from '@/utils/chartConfig'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import { defaultChartOptions, getResponsiveChartOptions } from '@/utils/chartConfig'
import ChartSkeleton from '@/components/dashboard/ChartSkeleton.vue'
// import ChartEmptyState from '@/components/dashboard/ChartEmptyState.vue' // Temporarily disabled

ChartJS.register(
  ArcElement,
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
    default: true // Default true for pie charts (charts.csv: hard for accessibility)
  }
})

defineEmits(['refresh', 'show-filters'])

// Check if data is effectively empty
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

const mergedOptions = computed(() => {
  return getResponsiveChartOptions({
    ...defaultChartOptions,
    ...props.options,
    elements: {
      arc: {
        borderWidth: 2,
        borderColor: '#ffffff',
        borderRadius: 4,
        hoverBorderWidth: 3,
        hoverOffset: 4
      }
    },
    plugins: {
      ...defaultChartOptions.plugins,
      ...props.options.plugins,
      tooltip: {
        ...defaultChartOptions.plugins.tooltip,
        ...props.options.plugins?.tooltip,
        callbacks: {
          ...defaultChartOptions.plugins.tooltip.callbacks,
          ...props.options.plugins?.tooltip?.callbacks,
          label: (context) => {
            const label = context.label || ''
            const value = context.parsed || 0
            const total = context.dataset.data.reduce((a, b) => a + b, 0)
            const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0
            const formattedValue = typeof value === 'number' 
              ? new Intl.NumberFormat('vi-VN').format(value)
              : value
            return `${label}: ${formattedValue} (${percentage}%)`
          }
        }
      }
    }
  })
})

// Calculate total for percentage display
const totalValue = computed(() => {
  if (!props.chartData?.datasets?.[0]?.data) return 0
  return props.chartData.datasets[0].data.reduce((sum, val) => sum + (val || 0), 0)
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
