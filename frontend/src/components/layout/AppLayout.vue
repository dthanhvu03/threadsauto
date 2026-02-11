<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <Sidebar
      ref="sidebarRef"
      :selected-account="selectedAccount"
      @account-change="handleAccountChange"
      @menu-state-change="handleMenuStateChange"
    />

    <!-- Main Content Area -->
    <div
      :class="[
        'flex-1 flex flex-col min-w-0',
        'transition-transform duration-300 ease-in-out',
        isMobileMenuOpen ? 'md:translate-x-0 translate-x-64' : 'translate-x-0'
      ]"
    >
      <!-- Mobile Header with Hamburger Menu -->
      <div class="md:hidden bg-white border-b border-gray-200 h-14 flex items-center px-3 sticky top-0 z-30">
        <button
          @click="openMobileMenu"
          class="p-2.5 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 min-w-[44px] min-h-[44px] flex items-center justify-center"
          aria-label="Open menu"
        >
          <Bars3Icon class="h-6 w-6" />
        </button>
        <div class="flex items-center space-x-2 ml-2">
          <svg class="w-6 h-6 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
          </svg>
          <h1 class="text-base font-semibold text-gray-900">
            Threads Automation
          </h1>
        </div>
      </div>

      <!-- Main Content -->
      <!-- Container Padding: Mobile px-3 py-4, Tablet px-4 py-6, Desktop px-6 py-8, Large Desktop px-8 py-10 -->
      <main
        :class="[
          'flex-1 overflow-y-auto',
          'px-3 md:px-4 lg:px-6 xl:px-8 py-4 md:py-6 lg:py-8 xl:py-10'
        ]"
      >
        <div class="max-w-7xl mx-auto">
          <RouterView v-slot="{ Component }">
            <Transition name="page" mode="out-in">
              <component :is="Component" :key="$route.path" />
            </Transition>
          </RouterView>
        </div>
      </main>
    </div>

    <!-- Toast Container -->
    <ToastContainer />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { Bars3Icon } from '@heroicons/vue/24/outline'
import Sidebar from './Sidebar.vue'
import ToastContainer from '@/components/common/ToastContainer.vue'
import { useAccountsStore } from '@/stores/accounts'
import { useAccounts } from '@/features/accounts/composables/useAccounts'

const accountsStore = useAccountsStore()
const { fetchAccounts } = useAccounts()
const selectedAccount = ref(null)
const sidebarRef = ref(null)
const isMobileMenuOpen = ref(false)

const handleAccountChange = (accountId) => {
  selectedAccount.value = accountId
  accountsStore.setSelectedAccount(accountId)
}

const handleMenuStateChange = (isOpen) => {
  isMobileMenuOpen.value = isOpen
}

const openMobileMenu = () => {
  if (sidebarRef.value) {
    sidebarRef.value.openMobileMenu()
  }
}

onMounted(async () => {
  await fetchAccounts()
  if (accountsStore.accounts.length > 0) {
    selectedAccount.value = accountsStore.accounts[0].account_id
  }
})
</script>

<style scoped>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.15s ease;
}

.page-enter-from,
.page-leave-to {
  opacity: 0;
}
</style>
