<template>
  <div>
    <label v-if="label" :for="id" class="block text-xs md:text-sm font-medium text-gray-700 mb-1.5 md:mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <input
      :id="id"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :step="step"
      :min="min"
      :max="max"
      :class="inputClasses"
      @input="handleInput($event)"
      @blur="$emit('blur', $event)"
    />
    <p v-if="error" class="mt-1 text-xs md:text-sm text-red-600">{{ error }}</p>
    <p v-if="hint && !error" class="mt-1 text-xs md:text-sm text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  id: {
    type: String,
    default: () => `input-${Math.random().toString(36).substr(2, 9)}`
  },
  type: {
    type: String,
    default: 'text'
  },
  label: {
    type: String,
    default: null
  },
  placeholder: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: null
  },
  hint: {
    type: String,
    default: null
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  step: {
    type: [String, Number],
    default: null
  },
  min: {
    type: [String, Number],
    default: null
  },
  max: {
    type: [String, Number],
    default: null
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue', 'blur'])

const handleInput = (event) => {
  let value = event.target.value
  // Convert to number if type is number
  if (props.type === 'number' && value !== '') {
    value = parseFloat(value) || 0
  }
  emit('update:modelValue', value)
}

const inputClasses = computed(() => {
  // Size variants với responsive values
  const sizes = {
    // Small: Mobile 44px, Tablet 36px, Desktop 32px
    sm: 'px-3 py-2.5 md:py-2 lg:py-1.5 text-xs md:text-sm lg:text-sm min-h-[44px] md:min-h-[36px] lg:min-h-[32px]',
    // Medium: Mobile 44px, Tablet 38px, Desktop 36px
    md: 'px-3 md:px-3 lg:px-3 py-2.5 md:py-2 lg:py-2 text-sm md:text-sm lg:text-base min-h-[44px] md:min-h-[38px] lg:min-h-[36px]',
    // Large: Mobile 48px, Tablet 44px, Desktop 40px
    lg: 'px-4 md:px-4 lg:px-4 py-3 md:py-2.5 lg:py-2.5 text-base md:text-base lg:text-lg min-h-[48px] md:min-h-[44px] lg:min-h-[40px]'
  }
  
  const base = 'block w-full rounded-md border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors'
  const sizeClass = sizes[props.size] || sizes.md
  const errorClass = props.error ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500' : ''
  const disabledClass = props.disabled ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'
  
  return `${base} ${sizeClass} ${errorClass} ${disabledClass}`.trim()
})
</script>
