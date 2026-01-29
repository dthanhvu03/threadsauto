<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-50 overflow-y-auto"
        @click.self="$emit('update:modelValue', false)"
      >
      <div class="flex min-h-full items-center justify-center p-2 sm:p-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" />
          <div
            :class="modalClasses"
            class="relative transform overflow-hidden rounded-lg bg-white shadow-lg w-full max-h-[90vh] overflow-y-auto"
          >
            <div v-if="$slots.header || title" class="px-4 sm:px-6 py-3 sm:py-4 border-b border-gray-200 bg-gray-50">
              <slot name="header">
                <h3 v-if="title" class="text-base sm:text-lg font-semibold text-gray-900">{{ title }}</h3>
              </slot>
            </div>
            <div class="px-4 sm:px-6 py-4 sm:py-6">
              <slot />
            </div>
            <div v-if="$slots.footer" class="px-4 sm:px-6 py-3 sm:py-4 border-t border-gray-200 bg-gray-50 flex flex-col sm:flex-row justify-end gap-2 sm:gap-3">
              <slot name="footer" />
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: null
  },
  size: {
    type: String,
    default: 'md',
    validator: (value) => ['sm', 'md', 'lg', 'xl'].includes(value)
  }
})

defineEmits(['update:modelValue'])

const modalClasses = computed(() => {
  const sizes = {
    sm: 'w-full mx-2 sm:max-w-sm md:max-w-md',
    md: 'w-full mx-2 sm:max-w-md md:max-w-lg',
    lg: 'w-full mx-2 sm:max-w-lg md:max-w-2xl',
    xl: 'w-full mx-2 sm:max-w-2xl md:max-w-4xl'
  }
  return sizes[props.size]
})
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
