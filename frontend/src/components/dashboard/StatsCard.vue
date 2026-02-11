<template>
  <Card :class="['transition-all duration-200 hover:shadow-md', cardClasses]">
    <div class="flex items-start justify-between">
      <div class="flex-1">
        <div class="flex items-center space-x-2 mb-2">
          <div :class="['p-2 md:p-2.5 rounded-lg', iconBgClasses]">
            <component 
              v-if="iconComponent" 
              :is="iconComponent" 
              class="w-5 h-5 md:w-6 md:h-6"
              aria-hidden="true"
            />
            <span v-else-if="icon" class="text-xl md:text-2xl">{{ icon }}</span>
          </div>
          <div class="flex-1">
            <p class="text-xs md:text-sm font-medium text-gray-600">{{ label }}</p>
            <p v-if="subtitle" class="text-xs text-gray-500 mt-0.5">{{ subtitle }}</p>
          </div>
          <div v-if="statusBadge" class="flex items-center">
            <span 
              :class="[
                'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
                statusBadgeClasses
              ]"
            >
              {{ statusBadge.text }}
            </span>
          </div>
        </div>
        <p :class="['text-2xl md:text-3xl lg:text-4xl font-bold mb-1', valueClasses]">
          {{ formattedValue }}
        </p>
        <div v-if="trend" class="flex items-center space-x-1">
          <span :class="['text-xs md:text-xs font-medium', trendColorClass]">
            <ArrowUpIcon v-if="trend.direction === 'up'" class="w-3 h-3 inline-block" aria-hidden="true" />
            <ArrowDownIcon v-else-if="trend.direction === 'down'" class="w-3 h-3 inline-block" aria-hidden="true" />
            <ArrowRightIcon v-else class="w-3 h-3 inline-block" aria-hidden="true" />
            {{ trend.percentage }}%
          </span>
          <span class="text-xs md:text-xs text-gray-500">{{ trend.label }}</span>
        </div>
      </div>
      <div v-if="loading" class="animate-pulse motion-reduce:animate-none">
        <div class="w-8 h-8 bg-gray-200 rounded"></div>
      </div>
    </div>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import * as HeroIcons from '@heroicons/vue/24/outline'
import {
  ArrowUpIcon,
  ArrowDownIcon,
  ArrowRightIcon
} from '@heroicons/vue/24/outline'
import Card from '@/components/common/Card.vue'

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
  iconName: {
    type: String,
    default: null
  },
  color: {
    type: String,
    default: 'primary',
    validator: (value) => ['primary', 'success', 'warning', 'danger', 'info'].includes(value)
  },
  trend: {
    type: Object,
    default: null,
    validator: (value) => {
      if (!value) return true
      return value.direction && value.percentage !== undefined && value.label
    }
  },
  loading: {
    type: Boolean,
    default: false
  },
  format: {
    type: String,
    default: 'number',
    validator: (value) => ['number', 'percentage', 'currency', 'duration'].includes(value)
  },
  subtitle: {
    type: String,
    default: null
  },
  statusBadge: {
    type: Object,
    default: null,
    validator: (value) => {
      if (!value) return true
      return value.text && value.type
    }
  }
})

const colorClasses = {
  primary: {
    icon: 'bg-blue-100 text-blue-600',
    value: 'text-blue-600',
    card: 'border-blue-200'
  },
  success: {
    icon: 'bg-green-100 text-green-600',
    value: 'text-green-600',
    card: 'border-green-200'
  },
  warning: {
    icon: 'bg-yellow-100 text-yellow-600',
    value: 'text-yellow-600',
    card: 'border-yellow-200'
  },
  danger: {
    icon: 'bg-red-100 text-red-600',
    value: 'text-red-600',
    card: 'border-red-200'
  },
  info: {
    icon: 'bg-purple-100 text-purple-600',
    value: 'text-purple-600',
    card: 'border-purple-200'
  }
}

const iconBgClasses = computed(() => colorClasses[props.color].icon)
const valueClasses = computed(() => colorClasses[props.color].value)
const cardClasses = computed(() => colorClasses[props.color].card)

const trendColorClass = computed(() => {
  if (!props.trend) return ''
  if (props.trend.colorClass) return props.trend.colorClass
  if (props.trend.direction === 'up') return 'text-green-600'
  if (props.trend.direction === 'down') return 'text-red-600'
  return 'text-gray-600'
})

const statusBadgeClasses = computed(() => {
  if (!props.statusBadge) return ''
  const badgeColors = {
    healthy: 'bg-green-100 text-green-800',
    idle: 'bg-yellow-100 text-yellow-800',
    warning: 'bg-orange-100 text-orange-800',
    error: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800'
  }
  return badgeColors[props.statusBadge.type] || badgeColors.info
})

// Resolve icon component from iconName
const iconComponent = computed(() => {
  if (!props.iconName) return null
  const IconComponent = HeroIcons[props.iconName]
  return IconComponent || null
})

const formattedValue = computed(() => {
  if (props.loading) return '...'
  
  const numValue = typeof props.value === 'string' ? parseFloat(props.value) : props.value
  
  switch (props.format) {
    case 'percentage':
      return `${numValue.toFixed(1)}%`
    case 'currency':
      return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(numValue)
    case 'duration':
      if (numValue < 60) return `${numValue}s`
      if (numValue < 3600) return `${Math.floor(numValue / 60)}m ${numValue % 60}s`
      return `${Math.floor(numValue / 3600)}h ${Math.floor((numValue % 3600) / 60)}m`
    default:
      return new Intl.NumberFormat('vi-VN').format(numValue)
  }
})
</script>
