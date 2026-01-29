<template>
  <div :class="cardClasses">
    <div class="flex items-center justify-between">
      <div class="flex-1 min-w-0">
        <p :class="labelClasses">{{ label }}</p>
        <p :class="valueClasses">{{ formattedValue }}</p>
      </div>
      <div v-if="icon" :class="iconClasses">
        {{ icon }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [Number, String],
    required: true
  },
  icon: {
    type: String,
    default: null
  },
  variant: {
    type: String,
    default: 'default',
    validator: (value) => ['default', 'success', 'warning', 'error', 'info'].includes(value)
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const cardClasses = computed(() => {
  const base = 'bg-gray-50 border border-gray-200 rounded-md p-2 sm:p-3'
  return props.compact ? `${base} p-2` : base
})

const labelClasses = computed(() => {
  return 'text-xs text-gray-600 mb-0.5 sm:mb-1 truncate'
})

const valueClasses = computed(() => {
  const base = 'text-base sm:text-lg font-semibold truncate'
  const variants = {
    default: 'text-gray-900',
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
    info: 'text-blue-600'
  }
  return `${base} ${variants[props.variant]}`
})

const iconClasses = computed(() => {
  return 'text-lg sm:text-xl ml-2 flex-shrink-0'
})

const formattedValue = computed(() => {
  if (typeof props.value === 'number') {
    // Format large numbers
    if (props.value >= 1000) {
      return `${(props.value / 1000).toFixed(1)}k`
    }
    return props.value.toString()
  }
  return props.value
})
</script>
