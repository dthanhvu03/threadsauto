<template>
  <div class="date-range-picker">
    <div class="flex flex-col sm:flex-row gap-2">
      <!-- Preset Buttons -->
      <div class="flex flex-wrap gap-2">
        <button
          v-for="preset in presets"
          :key="preset.value"
          @click="selectPreset(preset.value)"
          :class="[
            'px-3 py-2 text-xs sm:text-sm font-medium rounded-md transition-colors',
            selectedPreset === preset.value
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          ]"
        >
          {{ preset.label }}
        </button>
      </div>
      
      <!-- Custom Range Inputs -->
      <div class="flex flex-col sm:flex-row gap-2 flex-1">
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-700 mb-1">Từ ngày</label>
          <input
            v-model="startDate"
            type="date"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm px-3 py-2"
            @change="handleCustomRange"
          />
        </div>
        <div class="flex-1">
          <label class="block text-xs font-medium text-gray-700 mb-1">Đến ngày</label>
          <input
            v-model="endDate"
            type="date"
            class="w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 text-sm px-3 py-2"
            @change="handleCustomRange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { formatDateVN, toVietnamTimezone } from '@/utils/datetime'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ start: null, end: null })
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const presets = [
  { label: 'Hôm nay', value: 'today' },
  { label: '7 ngày qua', value: 'last7days' },
  { label: '30 ngày qua', value: 'last30days' },
  { label: '90 ngày qua', value: 'last90days' },
  { label: 'Tùy chọn', value: 'custom' }
]

const selectedPreset = ref('last30days')
const startDate = ref('')
const endDate = ref('')

// Initialize with default preset only if no value is set
onMounted(() => {
  // Only set default if no value is provided
  if (!props.modelValue || !props.modelValue.start || !props.modelValue.end) {
    selectPreset('last30days')
  } else {
    // Sync internal state with existing value
    const start = new Date(props.modelValue.start)
    const end = new Date(props.modelValue.end)
    startDate.value = formatDateForInput(start)
    endDate.value = formatDateForInput(end)
  }
})

const selectPreset = (preset) => {
  selectedPreset.value = preset
  
  const now = new Date()
  const vnNow = toVietnamTimezone(now)
  if (!vnNow) return
  
  const today = new Date(vnNow.getFullYear(), vnNow.getMonth(), vnNow.getDate())
  let start = new Date(today)
  let end = new Date(today)
  
  switch (preset) {
    case 'today':
      start = new Date(today)
      end = new Date(today)
      break
    case 'last7days':
      start.setDate(start.getDate() - 6) // Include today, so 6 days back
      break
    case 'last30days':
      start.setDate(start.getDate() - 29) // Include today, so 29 days back
      break
    case 'last90days':
      start.setDate(start.getDate() - 89) // Include today, so 89 days back
      break
    case 'custom':
      // Don't change dates, let user pick
      return
  }
  
  // Format dates for input (YYYY-MM-DD)
  startDate.value = formatDateForInput(start)
  endDate.value = formatDateForInput(end)
  
  emitRange(start, end)
}

const formatDateForInput = (date) => {
  if (!date) return ''
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const handleCustomRange = () => {
  if (!startDate.value || !endDate.value) return
  
  selectedPreset.value = 'custom'
  
  const start = new Date(startDate.value + 'T00:00:00')
  const end = new Date(endDate.value + 'T23:59:59')
  
  // Convert to UTC for API
  const startUTC = new Date(start.getTime() - (7 * 60 * 60 * 1000))
  const endUTC = new Date(end.getTime() - (7 * 60 * 60 * 1000))
  
  emitRange(startUTC, endUTC)
}

const emitRange = (start, end) => {
  const range = {
    start: start ? start.toISOString() : null,
    end: end ? end.toISOString() : null
  }
  
  // Compare with current value before emitting
  const currentRange = props.modelValue
  if (currentRange && 
      currentRange.start === range.start && 
      currentRange.end === range.end) {
    return // No change, skip emission
  }
  
  emit('update:modelValue', range)
  emit('change', range)
}

// Watch for external changes - only update internal state if values actually changed
watch(() => props.modelValue, (newValue) => {
  if (newValue && newValue.start && newValue.end) {
    const start = new Date(newValue.start)
    const end = new Date(newValue.end)
    const newStartDate = formatDateForInput(start)
    const newEndDate = formatDateForInput(end)
    
    // Only update if values actually changed (prevent unnecessary updates)
    if (startDate.value !== newStartDate || endDate.value !== newEndDate) {
      startDate.value = newStartDate
      endDate.value = newEndDate
    }
  }
}, { deep: true })
</script>

<style scoped>
.date-range-picker {
  width: 100%;
}
</style>
