<template>
  <!-- Mobile backdrop overlay -->
  <div
    v-if="isMobileMenuOpen"
    class="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity"
    @click="closeMobileMenu"
  ></div>

  <!-- Sidebar -->
  <aside
    :class="[
      'md:static flex-shrink-0',
      'w-64 bg-white border-r border-gray-200',
      'flex flex-col',
      'h-screen',
      'transform transition-transform duration-300 ease-in-out',
      'fixed md:relative inset-y-0 left-0 z-50',
      isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
    ]"
  >
    <!-- Logo and Title -->
    <div class="flex items-center justify-between h-14 px-3 md:px-4 border-b border-gray-200">
      <div class="flex items-center space-x-2">
        <span class="text-xl md:text-2xl">🧵</span>
        <h1 class="text-base md:text-xl font-semibold text-gray-900">
          Threads Automation
        </h1>
      </div>
      <div class="flex items-center space-x-2">
        <!-- Theme Toggle -->
        <ThemeToggle />
        <!-- Mobile close button -->
        <button
          @click="closeMobileMenu"
          class="md:hidden p-2.5 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 min-w-[44px] min-h-[44px] flex items-center justify-center transition-colors"
          aria-label="Close menu"
        >
          <XMarkIcon class="h-6 w-6" />
        </button>
      </div>
    </div>

    <!-- Search Bar -->
    <div class="px-3 py-2 border-b border-gray-200">
      <div class="relative">
        <MagnifyingGlassIcon class="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Tìm kiếm..."
          class="w-full pl-10 pr-4 py-2.5 md:py-2 rounded-lg bg-gray-50 border border-gray-200 text-sm min-h-[44px] md:min-h-[38px] focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-colors"
        />
      </div>
    </div>

    <!-- Navigation Links -->
    <nav class="flex-1 overflow-y-auto py-3 md:py-4">
      <div class="px-2 space-y-0.5">
        <template v-for="section in navigationSections" :key="section.key">
          <!-- Section Header -->
          <div v-if="section.items.length > 0" class="px-3 py-2 mt-4 first:mt-0">
            <h3 class="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              {{ section.label }}
            </h3>
          </div>
          
          <!-- Navigation Items -->
          <router-link
            v-for="item in section.items"
            :key="item.name"
            :to="getRoutePath(item)"
            @click="handleNavClick"
            :class="[
              'group flex items-center justify-between px-3 py-2.5 md:py-2.5 rounded-lg text-xs md:text-sm font-medium transition-all duration-200 ease-in-out min-h-[44px] md:min-h-[40px]',
              'hover:scale-[1.02] active:scale-[0.98]',
              $route.name === item.name
                ? 'bg-indigo-50 border-l-[3px] border-primary-600 text-primary-700 font-semibold shadow-sm'
                : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
            ]"
          >
            <span class="flex items-center gap-2">
              <component 
                :is="getIconComponent(item.icon)" 
                class="h-5 w-5 flex-shrink-0"
              />
              {{ item.label }}
            </span>
            <StatusBadge
              v-if="getBadgeForItem(item)"
              :variant="getBadgeForItem(item).variant"
              :size="'sm'"
              :label="getBadgeForItem(item).label"
              :count="getBadgeForItem(item).count"
              class="transition-transform duration-200 group-hover:scale-110"
            />
          </router-link>
        </template>
      </div>
    </nav>

    <!-- User Profile Section -->
    <div class="border-t border-gray-200 p-3 bg-gray-50/30">
      <div class="flex items-center space-x-3">
        <!-- Avatar -->
        <div class="relative flex-shrink-0">
          <div class="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center">
            <span class="text-indigo-600 font-semibold text-sm">
              {{ userInitials }}
            </span>
          </div>
          <span 
            v-if="isConnected"
            class="absolute bottom-0 right-0 w-3 h-3 bg-green-500 rounded-full border-2 border-white"
            title="Online"
          ></span>
        </div>
        
        <!-- Name & Email -->
        <div class="flex-1 min-w-0">
          <p class="text-sm font-semibold text-gray-900 truncate">
            {{ userName || selectedAccount || 'User' }}
          </p>
          <p class="text-xs text-gray-500 truncate">
            {{ userEmail || (selectedAccount ? `${selectedAccount}@threads.com` : 'No account selected') }}
          </p>
        </div>
        
        <!-- Logout/Account button -->
        <button 
          @click="handleAccountMenu"
          class="p-2.5 md:p-2 text-gray-400 hover:text-gray-600 transition-colors min-w-[44px] md:min-w-0 min-h-[44px] md:min-h-0 flex items-center justify-center"
          :title="'Account menu'"
        >
          <ArrowRightOnRectangleIcon class="h-5 w-5" />
        </button>
      </div>
      
      <!-- Account Selector (Collapsible) -->
      <div v-if="showAccountSelector && accounts.length > 0" class="mt-3 pt-3 border-t border-gray-200">
        <FormSelect
          :model-value="selectedAccount"
          @update:model-value="handleAccountChange"
          label="Switch Account"
          :options="[
            { value: '', label: 'All Accounts' },
            ...accounts.map(acc => ({ value: acc.account_id, label: acc.account_id }))
          ]"
        />
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { 
  XMarkIcon, 
  MagnifyingGlassIcon, 
  ArrowRightOnRectangleIcon,
  HomeIcon,
  BriefcaseIcon,
  ArrowUpTrayIcon,
  ClockIcon,
  UserIcon,
  Cog6ToothIcon,
  AdjustmentsHorizontalIcon,
  HeartIcon,
  RssIcon
} from '@heroicons/vue/24/outline'
import { useAccountsStore } from '@/stores/accounts'
import { useDashboardStore } from '@/features/dashboard/store/dashboardStore'
import { useJobsStore } from '@/features/jobs/store/jobsStore'
import { useWebSocketStore } from '@/stores/websocket'
import StatusBadge from '@/components/common/StatusBadge.vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import FormSelect from '@/components/common/FormSelect.vue'

const props = defineProps({
  selectedAccount: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['account-change', 'menu-state-change'])

const route = useRoute()
const accountsStore = useAccountsStore()
const dashboardStore = useDashboardStore()
const jobsStore = useJobsStore()
const wsStore = useWebSocketStore()

const isMobileMenuOpen = ref(false)
const searchQuery = ref('')
const showAccountSelector = ref(false)

const accounts = computed(() => accountsStore.accounts)
const stats = computed(() => dashboardStore.stats)
const jobs = computed(() => jobsStore.jobs)

// Calculate pending jobs count
const pendingJobsCount = computed(() => {
  return jobs.value.filter(job => job.status === 'pending').length
})

// Format success rate
const successRateFormatted = computed(() => {
  if (!stats.value || !stats.value.success_rate) return '0%'
  return `${stats.value.success_rate.toFixed(0)}%`
})

// Check WebSocket connection
const isConnected = computed(() => {
  return wsStore.isConnected('dashboard', props.selectedAccount)
})

// Show metrics if stats are available
const showMetrics = computed(() => {
  return stats.value !== null && stats.value.total_jobs !== undefined
})

// Icon mapping
const iconMap = {
  HomeIcon,
  BriefcaseIcon,
  ArrowUpTrayIcon,
  ClockIcon,
  UserIcon,
  Cog6ToothIcon,
  AdjustmentsHorizontalIcon,
  HeartIcon,
  RssIcon
}

// Navigation structure with sections and badges
const navigationItems = [
  { 
    name: 'dashboard', 
    path: '', 
    label: 'Dashboard',
    icon: 'HomeIcon',
    section: 'main',
    badge: null
  },
  { 
    name: 'jobs', 
    path: 'jobs', 
    label: 'Jobs',
    icon: 'BriefcaseIcon',
    section: 'main',
    badge: { type: 'count', variant: 'warning' }
  },
  { 
    name: 'excel', 
    path: 'excel', 
    label: 'Excel Upload',
    icon: 'ArrowUpTrayIcon',
    section: 'main',
    badge: null
  },
  { 
    name: 'scheduler', 
    path: 'scheduler', 
    label: 'Lịch trình',
    icon: 'ClockIcon',
    section: 'main',
    badge: null
  },
  { 
    name: 'feed-explorer', 
    path: 'feed-explorer', 
    label: 'Feed Explorer',
    icon: 'RssIcon',
    section: 'main',
    badge: null
  },
  { 
    name: 'accounts', 
    path: 'accounts', 
    label: 'Tài khoản',
    icon: 'UserIcon',
    section: 'settings',
    badge: null
  },
  { 
    name: 'config', 
    path: 'config', 
    label: 'Cấu hình',
    icon: 'Cog6ToothIcon',
    section: 'settings',
    badge: null
  },
  { 
    name: 'selectors', 
    path: 'selectors', 
    label: 'Selectors',
    icon: 'AdjustmentsHorizontalIcon',
    section: 'settings',
    badge: null
  }
]

// Get icon component
const getIconComponent = (iconName) => {
  return iconMap[iconName] || null
}

// Get route path/object for navigation
const getRoutePath = (item) => {
  // Use route name for all routes to ensure correct navigation with nested routes
  return { name: item.name }
}

// Filter navigation based on search query
const filteredNavigation = computed(() => {
  if (!searchQuery.value.trim()) {
    return navigationItems
  }
  const query = searchQuery.value.toLowerCase()
  return navigationItems.filter(item => 
    item.label.toLowerCase().includes(query) ||
    item.name.toLowerCase().includes(query)
  )
})

// Group navigation by sections
const navigationSections = computed(() => {
  const sections = [
    { key: 'main', label: 'MAIN MENU', items: [] },
    { key: 'settings', label: 'ACCOUNTS & SETTINGS', items: [] }
  ]
  
  filteredNavigation.value.forEach(item => {
    const section = sections.find(s => s.key === item.section)
    if (section) {
      section.items.push(item)
    }
  })
  
  // Only return sections that have items
  return sections.filter(s => s.items.length > 0)
})

// Get badge info for navigation item
const getBadgeForItem = (item) => {
  if (!item.badge) return null
  
  if (item.badge.type === 'count' && item.name === 'jobs') {
    const count = pendingJobsCount.value
    if (count > 0) {
      return {
        variant: item.badge.variant || 'warning',
        count: count
      }
    }
  }
  
  if (item.badge.type === 'new') {
    return {
      variant: 'new',
      label: item.badge.label || 'New'
    }
  }
  
  return null
}

// User profile helpers
const userInitials = computed(() => {
  if (props.selectedAccount) {
    const parts = props.selectedAccount.split('_')
    if (parts.length > 1) {
      return parts[0].charAt(0).toUpperCase() + parts[1].charAt(0).toUpperCase()
    }
    return props.selectedAccount.substring(0, 2).toUpperCase()
  }
  return 'TA'
})

const userName = computed(() => {
  // Could be extended to fetch from user store if available
  return props.selectedAccount || null
})

const userEmail = computed(() => {
  // Could be extended to fetch from user store if available
  return null
})

// Watch for selected account changes to update metrics
watch(() => props.selectedAccount, () => {
  // Metrics will be updated by parent component or via WebSocket
}, { immediate: true })

const handleAccountChange = (accountId) => {
  emit('account-change', accountId || null)
  showAccountSelector.value = false
}

const handleAccountMenu = () => {
  showAccountSelector.value = !showAccountSelector.value
}

const handleNavClick = () => {
  // Close mobile menu when navigation link is clicked
  if (window.innerWidth < 768) {
    closeMobileMenu()
  }
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
  emit('menu-state-change', false)
}

const openMobileMenu = () => {
  isMobileMenuOpen.value = true
  emit('menu-state-change', true)
}

// Expose methods for parent component
defineExpose({
  openMobileMenu,
  closeMobileMenu
})
</script>
