<template>
  <nav class="bg-white border-b border-gray-200 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center space-x-8">
          <div class="flex-shrink-0 flex items-center space-x-2">
            <span class="text-2xl">🧵</span>
            <h1 class="text-xl font-semibold text-gray-900">
              Threads Automation
            </h1>
          </div>
          <div class="hidden md:flex space-x-1">
            <router-link
              v-for="item in navigation"
              :key="item.name"
              :to="item.path"
              :class="[
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                $route.name === item.name
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              ]"
            >
              {{ item.label }}
            </router-link>
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <select
            v-if="accounts.length > 0"
            :value="selectedAccount"
            @change="handleAccountChange($event.target.value)"
            class="block rounded-md border-gray-300 focus:border-primary-500 focus:ring-1 focus:ring-primary-500 sm:text-sm bg-white px-3 py-2"
          >
            <option value="">All Accounts</option>
            <option
              v-for="account in accounts"
              :key="account.account_id"
              :value="account.account_id"
            >
              {{ account.account_id }}
            </option>
          </select>
        </div>
      </div>
    </div>
    <!-- Mobile menu -->
    <div class="md:hidden border-t border-gray-200">
      <div class="px-2 pt-2 pb-3 space-y-1">
        <router-link
          v-for="item in navigation"
          :key="item.name"
          :to="item.path"
          :class="[
            'block px-3 py-2 rounded-md text-base font-medium',
            $route.name === item.name
              ? 'bg-primary-600 text-white'
              : 'text-gray-700 hover:bg-gray-100'
          ]"
        >
          {{ item.label }}
        </router-link>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useAccountsStore } from '@/stores/accounts'

const props = defineProps({
  selectedAccount: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['account-change'])

const accountsStore = useAccountsStore()

const accounts = computed(() => accountsStore.accounts)

const navigation = [
  { name: 'dashboard', path: '/', label: '📊 Dashboard' },
  { name: 'jobs', path: '/jobs', label: '📅 Jobs' },
  { name: 'excel', path: '/excel', label: '📤 Excel Upload' },
  { name: 'scheduler', path: '/scheduler', label: '⏰ Lịch trình' },
  { name: 'accounts', path: '/accounts', label: '👤 Tài khoản' },
  { name: 'config', path: '/config', label: '⚙️ Cấu hình' },
  { name: 'selectors', path: '/selectors', label: '🎯 Selectors' }
]

const handleAccountChange = (accountId) => {
  emit('account-change', accountId || null)
}
</script>
