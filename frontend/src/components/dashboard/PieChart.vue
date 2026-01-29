<template>
  <div class="chart-container" :style="{ height: height }">
    <div v-if="loading" class="flex items-center justify-center h-full">
      <LoadingSpinner size="md" />
    </div>
    <div v-else-if="!chartData || chartData.datasets.length === 0" class="flex items-center justify-center h-full">
      <EmptyState
        title="No data"
        description="No data available for this chart"
      />
    </div>
    <Pie
      v-else
      :data="chartData"
      :options="mergedOptions"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Pie } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend
} from 'chart.js'
import { defaultChartOptions, getResponsiveChartOptions } from '@/utils/chartConfig'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'

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
    default: '300px'
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const mergedOptions = computed(() => {
  return getResponsiveChartOptions({
    ...defaultChartOptions,
    ...props.options
  })
})
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  max-width: 100%;
  padding: 0.5rem;
}

@media (min-width: 640px) {
  .chart-container {
    padding: 1rem;
  }
}
</style>
