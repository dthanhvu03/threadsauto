<template>
  <div>
    <div class="flex items-start">
      <div class="flex items-center min-w-[44px] md:min-w-0 min-h-[44px] md:min-h-0">
        <input
          :id="id"
          type="checkbox"
          :checked="modelValue"
          :disabled="disabled"
          :required="required"
          :class="checkboxClasses"
          @change="handleChange($event)"
        />
      </div>
      <label v-if="label" :for="id" class="ml-2 md:ml-3 block text-xs md:text-sm text-gray-700 cursor-pointer flex-1">
        {{ label }}
        <span v-if="required" class="text-red-500">*</span>
      </label>
    </div>
    <p v-if="error" class="mt-1 text-xs md:text-sm text-red-600 ml-[44px] md:ml-[20px]">{{ error }}</p>
    <p v-if="hint && !error" class="mt-1 text-xs md:text-sm text-gray-500 ml-[44px] md:ml-[20px]">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  id: {
    type: String,
    default: () => `checkbox-${Math.random().toString(36).substr(2, 9)}`
  },
  label: {
    type: String,
    default: null
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
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const handleChange = (event) => {
  emit('update:modelValue', event.target.checked)
  emit('change', event.target.checked)
}

const checkboxClasses = computed(() => {
  // Checkbox size: Mobile 20px (touch area 44px), Tablet 18px, Desktop 16px
  const base = 'h-5 w-5 md:h-[18px] md:w-[18px] lg:h-4 lg:w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded transition-colors cursor-pointer'
  const disabledClass = props.disabled ? 'cursor-not-allowed opacity-50' : ''
  const errorClass = props.error ? 'border-red-300 focus:ring-red-500' : ''
  
  return `${base} ${errorClass} ${disabledClass}`.trim()
})
</script>
