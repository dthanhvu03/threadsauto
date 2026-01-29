<template>
  <div>
    <label v-if="label" :for="id" class="block text-xs md:text-sm font-medium text-gray-700 mb-1.5 md:mb-1">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <textarea
      :id="id"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :required="required"
      :rows="rows"
      :class="textareaClasses"
      @input="handleInput($event)"
      @blur="$emit('blur', $event)"
    ></textarea>
    <p v-if="error" class="mt-1 text-xs md:text-sm text-red-600">{{ error }}</p>
    <p v-if="hint && !error" class="mt-1 text-xs md:text-sm text-gray-500">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  id: {
    type: String,
    default: () => `textarea-${Math.random().toString(36).substr(2, 9)}`
  },
  label: {
    type: String,
    default: null
  },
  placeholder: {
    type: String,
    default: ''
  },
  rows: {
    type: Number,
    default: 4
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
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg'].includes(value)
  }
})

const emit = defineEmits(['update:modelValue', 'blur'])

const handleInput = (event) => {
  emit('update:modelValue', event.target.value)
}

const textareaClasses = computed(() => {
  // Size variants với responsive values
  const sizes = {
    // Small: Mobile 88px (2x touch target), Tablet 80px, Desktop 72px
    sm: 'px-3 py-2.5 md:py-2 lg:py-1.5 text-xs md:text-sm lg:text-sm min-h-[88px] md:min-h-[80px] lg:min-h-[72px]',
    // Medium: Mobile 88px, Tablet 80px, Desktop 72px
    md: 'px-3 md:px-3 lg:px-3 py-2.5 md:py-2 lg:py-2 text-sm md:text-sm lg:text-base min-h-[88px] md:min-h-[80px] lg:min-h-[72px]',
    // Large: Mobile 96px, Tablet 88px, Desktop 80px
    lg: 'px-4 md:px-4 lg:px-4 py-3 md:py-2.5 lg:py-2.5 text-base md:text-base lg:text-lg min-h-[96px] md:min-h-[88px] lg:min-h-[80px]'
  }
  
  const base = 'block w-full rounded-md border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 transition-colors resize-y'
  const sizeClass = sizes[props.size] || sizes.md
  const errorClass = props.error ? 'border-red-300 text-red-900 placeholder-red-300 focus:border-red-500 focus:ring-red-500' : ''
  const disabledClass = props.disabled ? 'bg-gray-50 cursor-not-allowed' : 'bg-white'
  
  return `${base} ${sizeClass} ${errorClass} ${disabledClass}`.trim()
})
</script>
