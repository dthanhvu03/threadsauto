<template>
  <div>
    <!-- Mobile: Card view -->
    <div v-if="data.length > 0" class="md:hidden space-y-4">
      <div
        v-for="(row, index) in data"
        :key="index"
        class="bg-white rounded-lg border border-gray-200 shadow-sm p-3 md:p-4 space-y-2 md:space-y-3"
      >
        <div
          v-for="column in visibleColumns"
          :key="column.key"
          class="flex flex-col"
        >
          <span class="text-xs md:text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
            {{ column.label }}
          </span>
          <div class="text-xs md:text-sm text-gray-900 break-words">
            <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
              {{ row[column.key] }}
            </slot>
          </div>
        </div>
        <div v-if="actions" class="pt-3 border-t border-gray-200">
          <slot name="actions" :row="row" :index="index" />
        </div>
      </div>
    </div>

    <!-- Desktop: Table view -->
    <div class="hidden md:block overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              v-for="column in columns"
              :key="column.key"
              :class="thClasses"
              scope="col"
            >
              {{ column.label }}
            </th>
            <th v-if="actions" :class="thClasses" scope="col" class="relative">
              <span class="sr-only">Actions</span>
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="(row, index) in data" :key="index" class="hover:bg-gray-50">
            <td
              v-for="column in columns"
              :key="column.key"
              :class="tdClasses"
            >
              <slot :name="`cell-${column.key}`" :row="row" :value="row[column.key]">
                {{ row[column.key] }}
              </slot>
            </td>
            <td v-if="actions" :class="tdClasses" class="text-right text-sm font-medium">
              <slot name="actions" :row="row" :index="index" />
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty state (both views) -->
    <div v-if="data.length === 0" class="py-8 text-center text-gray-500">
      <slot name="empty">
        No data available
      </slot>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  columns: {
    type: Array,
    required: true
  },
  data: {
    type: Array,
    default: () => []
  },
  actions: {
    type: Boolean,
    default: false
  },
  mobileView: {
    type: Boolean,
    default: true
  },
  // Columns to show on mobile (if not specified, show all)
  mobileColumns: {
    type: Array,
    default: () => []
  }
})

const visibleColumns = computed(() => {
  if (props.mobileColumns.length > 0) {
    return props.columns.filter(col => 
      props.mobileColumns.includes(col.key) || col.mobile !== false
    )
  }
  // Show all columns by default, or columns marked with mobile: true
  return props.columns.filter(col => col.mobile !== false)
})

// Header: Mobile text-xs font-medium, Tablet text-xs font-semibold, Desktop text-sm font-semibold
// Cell Padding: Mobile px-2 py-2.5, Tablet px-4 py-3, Desktop px-6 py-4
// Font Size: Mobile text-xs, Tablet text-sm, Desktop text-sm
const thClasses = 'px-2 md:px-4 lg:px-6 py-2.5 md:py-3 text-left text-xs md:text-xs lg:text-sm font-medium md:font-semibold lg:font-semibold text-gray-500 uppercase tracking-wider'
const tdClasses = 'px-2 md:px-4 lg:px-6 py-2.5 md:py-3 lg:py-4 whitespace-nowrap text-xs md:text-sm lg:text-sm text-gray-900'
</script>
