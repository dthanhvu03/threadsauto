<template>
  <div class="chart-controls" role="toolbar" aria-label="Chart controls">
    <button
      v-if="showExport"
      @click="handleExport"
      class="control-button"
      :disabled="isExporting || !chartInstance"
      :aria-label="`Export ${chartTitle || 'chart'} as PNG`"
      title="Export as PNG"
    >
      <ArrowDownTrayIcon class="w-4 h-4" aria-hidden="true" />
      <span class="sr-only">Export chart</span>
    </button>
    
    <button
      v-if="showFullscreen"
      @click="handleFullscreen"
      class="control-button"
      :aria-label="`View ${chartTitle || 'chart'} in fullscreen`"
      title="View in fullscreen"
    >
      <ArrowsPointingOutIcon v-if="!isFullscreen" class="w-4 h-4" aria-hidden="true" />
      <ArrowsPointingInIcon v-else class="w-4 h-4" aria-hidden="true" />
      <span class="sr-only">{{ isFullscreen ? 'Exit fullscreen' : 'View fullscreen' }}</span>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ArrowDownTrayIcon, ArrowsPointingOutIcon, ArrowsPointingInIcon } from '@heroicons/vue/24/outline'
import { useChartInteractions } from '@/composables/useChartInteractions'

const props = defineProps({
  chartInstance: {
    type: Object,
    default: null
  },
  chartTitle: {
    type: String,
    default: ''
  },
  showExport: {
    type: Boolean,
    default: true
  },
  showFullscreen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['export', 'fullscreen'])

const { isExporting, exportAsPNG } = useChartInteractions()
const isFullscreen = ref(false)

const handleExport = () => {
  if (props.chartInstance) {
    const filename = props.chartTitle 
      ? props.chartTitle.toLowerCase().replace(/\s+/g, '-')
      : 'chart'
    exportAsPNG(props.chartInstance, filename)
    emit('export', { format: 'png', filename })
  }
}

const handleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  emit('fullscreen', isFullscreen.value)
}
</script>

<style scoped>
.chart-controls {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  justify-content: flex-end;
  padding: 0.5rem;
}

.control-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem;
  border: 1px solid #e5e7eb;
  border-radius: 0.375rem;
  background: #ffffff;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
  min-width: 2rem;
  min-height: 2rem;
}

.control-button:hover:not(:disabled) {
  background: #f9fafb;
  border-color: #d1d5db;
  color: #111827;
}

.control-button:focus {
  outline: none;
  ring: 2px;
  ring-color: #2563eb;
  ring-offset: 2px;
}

.control-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
</style>
