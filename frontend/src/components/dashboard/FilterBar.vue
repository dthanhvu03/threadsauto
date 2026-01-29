<template>
  <Card padding="sm" class="mb-4 md:mb-6">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4">
      <!-- Account Filter -->
      <div v-if="showAccountFilter">
        <FormSelect
          :model-value="modelValue.accountId"
          @update:model-value="updateFilter('accountId', $event)"
          label="Tài khoản"
          :options="[
            { value: '', label: 'Tất cả' },
            ...accounts.map(acc => ({ value: acc.account_id, label: acc.account_id }))
          ]"
        />
      </div>

      <!-- Platform Filter -->
      <div>
        <FormSelect
          :model-value="modelValue.platform"
          @update:model-value="updateFilter('platform', $event)"
          label="Platform"
          :options="[
            { value: '', label: 'Tất cả' },
            { value: 'threads', label: 'Threads' },
            { value: 'facebook', label: 'Facebook' }
          ]"
        />
      </div>

      <!-- Status Filter -->
      <div>
        <FormSelect
          :model-value="modelValue.status"
          @update:model-value="updateFilter('status', $event)"
          label="Trạng thái"
          :options="[
            { value: '', label: 'Tất cả' },
            { value: 'completed', label: 'Completed' },
            { value: 'pending', label: 'Pending' },
            { value: 'failed', label: 'Failed' },
            { value: 'running', label: 'Running' }
          ]"
        />
      </div>

      <!-- Clear Filters Button -->
      <div class="flex items-end">
        <Button
          variant="outline"
          size="sm"
          @click="clearFilters"
          class="w-full"
        >
          Xóa bộ lọc
        </Button>
      </div>
    </div>

    <!-- Date Range Picker -->
    <div class="mt-3 md:mt-4">
      <DateRangePicker
        :model-value="dateRange"
        @update:model-value="updateDateRange"
      />
    </div>
  </Card>
</template>

<script setup>
import { computed } from 'vue'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import FormSelect from '@/components/common/FormSelect.vue'
import DateRangePicker from '@/components/common/DateRangePicker.vue'
import { useAccountsStore } from '@/stores/accounts'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      accountId: '',
      platform: '',
      status: '',
      dateRange: { start: null, end: null }
    })
  },
  showAccountFilter: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

const accountsStore = useAccountsStore()
const accounts = computed(() => accountsStore.accounts || [])

const dateRange = computed(() => props.modelValue.dateRange || { start: null, end: null })

const updateFilter = (key, value) => {
  // Check if value actually changed
  if (props.modelValue[key] === value) {
    return // No change, skip emission
  }
  
  const newValue = {
    ...props.modelValue,
    [key]: value
  }
  emit('update:modelValue', newValue)
  emit('change', newValue)
}

const updateDateRange = (range) => {
  // Check if dateRange actually changed
  const currentRange = props.modelValue.dateRange || { start: null, end: null }
  if (currentRange.start === range.start && currentRange.end === range.end) {
    return // No change, skip emission
  }
  
  const newValue = {
    ...props.modelValue,
    dateRange: range
  }
  emit('update:modelValue', newValue)
  emit('change', newValue)
}

const clearFilters = () => {
  const cleared = {
    accountId: '',
    platform: '',
    status: '',
    dateRange: { start: null, end: null }
  }
  emit('update:modelValue', cleared)
  emit('change', cleared)
}
</script>
