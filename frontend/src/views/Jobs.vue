<template>
  <div>
    <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 md:gap-0">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-gray-900 mb-1 flex items-center gap-2">
          <CalendarIcon class="w-6 h-6 md:w-7 md:h-7" aria-hidden="true" />
          Jobs
        </h1>
        <p class="text-xs md:text-sm text-gray-600">Manage and monitor your scheduled jobs</p>
      </div>
      <Button 
        @click="showCreateModal = true" 
        class="w-full md:w-auto"
        aria-label="Create new job"
      >
        <PlusIcon class="w-4 h-4 mr-1.5" aria-hidden="true" />
        Create Job
      </Button>
    </div>

    <Alert
      v-if="error"
      type="error"
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <!-- Filters -->
    <Card class="mb-4 md:mb-6" padding="sm">
      <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-3 md:gap-4">
        <FormInput
          v-model="filters.accountId"
          label="Account ID"
          placeholder="Filter by account"
        />
        <FormSelect
          v-model="filters.status"
          label="Status"
          :options="[
            { value: '', label: 'All Status' },
            { value: 'scheduled', label: 'Scheduled' },
            { value: 'pending', label: 'Pending' },
            { value: 'completed', label: 'Completed' },
            { value: 'failed', label: 'Failed' }
          ]"
        />
        <FormSelect
          v-model="filters.platform"
          label="Platform"
          :options="[
            { value: '', label: 'All Platforms' },
            { value: 'threads', label: 'Threads' },
            { value: 'facebook', label: 'Facebook' }
          ]"
        />
        <FormInput
          v-model="filters.scheduled_from"
          label="Scheduled From"
          type="date"
        />
        <FormInput
          v-model="filters.scheduled_to"
          label="Scheduled To"
          type="date"
        />
        <div class="flex flex-col md:flex-row gap-2 md:space-x-2 md:items-end">
          <Button 
            variant="outline" 
            @click="handleClearFilters" 
            class="w-full md:w-auto"
            aria-label="Clear all filters"
          >
            <XMarkIcon class="w-4 h-4 mr-1.5" aria-hidden="true" />
            Clear
          </Button>
        </div>
      </div>
    </Card>

    <!-- Jobs List -->
    <Card>
      <template #header>
        <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-2 md:gap-0">
          <h2 class="text-base md:text-lg font-semibold">Jobs List</h2>
          <Button 
            size="sm" 
            variant="outline" 
            @click="refreshJobs" 
            class="w-full md:w-auto"
            :disabled="loading"
            aria-label="Refresh jobs list"
          >
            <ArrowPathIcon 
              class="w-4 h-4 mr-1.5 motion-reduce:animate-none" 
              :class="{ 'animate-spin': loading }" 
              aria-hidden="true" 
            />
            Refresh
          </Button>
        </div>
      </template>
      <div v-if="loading" class="flex justify-center py-12" role="status" aria-live="polite">
        <LoadingSpinner size="lg" />
        <span class="sr-only">Loading jobs...</span>
      </div>
      <div v-else-if="filteredJobs.length === 0" class="py-8">
        <EmptyState
          title="No jobs found"
          description="Create your first job to get started"
        />
      </div>
      <Table
        v-else
        :columns="jobColumns"
        :data="filteredJobs"
        :actions="true"
      >
        <template #cell-status="{ value }">
          <span
            :class="{
              'px-2 py-1 rounded-full text-xs font-medium': true,
              'bg-yellow-100 text-yellow-800': value === 'pending',
              'bg-green-100 text-green-800': value === 'completed',
              'bg-red-100 text-red-800': value === 'failed'
            }"
          >
            {{ value }}
          </span>
        </template>
        <template #cell-created_at="{ value, row }">
          {{ value ? formatDateTimeVN(value) : '-' }}
        </template>
        <template #cell-scheduled_time="{ value }">
          {{ value ? formatDateTimeVN(value) : '-' }}
        </template>
        <template #cell-completed_at="{ value }">
          {{ value ? formatDateTimeVN(value) : '-' }}
        </template>
        <template #actions="{ row }">
          <div class="flex flex-col md:flex-row gap-2 md:space-x-2">
            <Button 
              size="sm" 
              variant="outline" 
              @click="editJob(row)" 
              :disabled="row.status === 'completed' || row.status === 'running'"
              class="w-full md:w-auto"
              :aria-label="`Edit job ${row.job_id}`"
            >
              <PencilIcon class="w-4 h-4 mr-1" aria-hidden="true" />
              Edit
            </Button>
            <Button 
              size="sm" 
              variant="danger" 
              @click="handleDeleteJob(row.job_id)" 
              class="w-full md:w-auto"
              :aria-label="`Delete job ${row.job_id}`"
            >
              <TrashIcon class="w-4 h-4 mr-1" aria-hidden="true" />
              Delete
            </Button>
          </div>
        </template>
      </Table>
      
      <!-- Pagination -->
      <Pagination
        v-if="totalPages > 1 || total > 0"
        :current-page="currentPage"
        :page-size="pageSize"
        :total="total"
        @page-change="handlePageChange"
        @page-size-change="handlePageSizeChange"
      />
    </Card>

    <!-- Edit Job Modal -->
    <Modal 
      v-model="showEditModal" 
      title="Edit Job" 
      size="lg"
      aria-labelledby="edit-job-title"
      aria-describedby="edit-job-description"
    >
      <p id="edit-job-description" class="sr-only">Edit job details and scheduling information</p>
      <form v-if="editingJob" @submit.prevent="handleUpdateJob" aria-label="Edit job form">
        <div class="space-y-4">
          <FormInput
            v-model="editingJob.content"
            label="Content"
            placeholder="Enter job content"
            required
            autocomplete="off"
            spellcheck="true"
            aria-required="true"
          />
          <FormSelect
            v-model="editingJob.account_id"
            label="Account ID"
            :options="[
              { value: '', label: 'None (Optional)' },
              ...accounts.map(acc => ({ value: acc.account_id, label: acc.account_id }))
            ]"
          />
          <FormSelect
            v-model="editingJob.platform"
            label="Platform"
            required
            :options="[
              { value: 'threads', label: 'Threads' },
              { value: 'facebook', label: 'Facebook' }
            ]"
          />
          <FormSelect
            v-model="editingJob.priority"
            label="Priority"
            required
            :options="[
              { value: 'low', label: 'LOW' },
              { value: 'normal', label: 'NORMAL' },
              { value: 'high', label: 'HIGH' },
              { value: 'urgent', label: 'URGENT' }
            ]"
          />
          <FormInput
            v-model="editingJob.scheduled_time"
            label="Scheduled Time"
            type="datetime-local"
            required
          />
          <FormInput
            v-model="editingJob.max_retries"
            label="Max Retries"
            type="number"
            :min="0"
            :max="10"
            required
          />
          <FormInput
            v-model="editingJob.link_aff"
            label="Affiliate Link (Optional)"
            placeholder="Enter affiliate link"
            type="url"
            autocomplete="url"
            spellcheck="false"
          />
        </div>
      </form>
      <template #footer>
        <div class="flex flex-col md:flex-row gap-2 md:gap-3 w-full md:w-auto md:ml-auto">
          <Button variant="outline" @click="showEditModal = false" class="w-full md:w-auto">Cancel</Button>
          <Button @click="handleUpdateJob" :loading="loading" class="w-full md:w-auto">Update</Button>
        </div>
      </template>
    </Modal>

    <!-- Create Job Modal -->
    <Modal 
      v-model="showCreateModal" 
      title="Create New Job" 
      size="lg"
      aria-labelledby="create-job-title"
      aria-describedby="create-job-description"
    >
      <p id="create-job-description" class="sr-only">Create a new scheduled job with content and platform selection</p>
      <form @submit.prevent="handleCreateJob" aria-label="Create job form">
        <div class="space-y-4">
          <FormInput
            v-model="newJob.content"
            label="Content"
            placeholder="Enter job content"
            required
            autocomplete="off"
            spellcheck="true"
            aria-required="true"
          />
          <FormSelect
            v-model="newJob.account_id"
            label="Account ID"
            :options="[
              { value: '', label: 'None (Optional)' },
              ...accounts.map(acc => ({ value: acc.account_id, label: acc.account_id }))
            ]"
          />
          <FormSelect
            v-model="newJob.platform"
            label="Platform"
            required
            :options="[
              { value: 'threads', label: 'Threads' },
              { value: 'facebook', label: 'Facebook' }
            ]"
          />
          <FormSelect
            v-model="newJob.priority"
            label="Priority"
            required
            :options="[
              { value: 'low', label: 'LOW' },
              { value: 'normal', label: 'NORMAL' },
              { value: 'high', label: 'HIGH' },
              { value: 'urgent', label: 'URGENT' }
            ]"
          />
          <FormInput
            v-model="newJob.scheduled_time"
            label="Scheduled Time"
            type="datetime-local"
            required
          />
          <FormInput
            v-model="newJob.max_retries"
            label="Max Retries"
            type="number"
            :min="0"
            :max="10"
            required
          />
          <FormInput
            v-model="newJob.link_aff"
            label="Affiliate Link (Optional)"
            placeholder="Enter affiliate link"
            type="url"
            autocomplete="url"
            spellcheck="false"
          />
        </div>
      </form>
      <template #footer>
        <div class="flex flex-col md:flex-row gap-2 md:gap-3 w-full md:w-auto md:ml-auto">
          <Button variant="outline" @click="showCreateModal = false" class="w-full md:w-auto">Cancel</Button>
          <Button @click="handleCreateJob" :loading="loading" class="w-full md:w-auto">Create</Button>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
// Use new composable (Phase 3)
import { useJobs } from '@/features/jobs/composables/useJobs'
import { useAccounts } from '@/features/accounts/composables/useAccounts'
import { useWebSocketStore } from '@/stores/websocket'
import { useToast } from '@/core/composables/useToast'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Table from '@/components/common/Table.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import Modal from '@/components/common/Modal.vue'
import FormInput from '@/components/common/FormInput.vue'
import FormSelect from '@/components/common/FormSelect.vue'
import Pagination from '@/components/common/Pagination.vue'
import { formatDateTimeVN, utcToDatetimeLocal, datetimeLocalToUTC } from '@/utils/datetime'
import { 
  CalendarIcon, 
  PlusIcon, 
  ArrowPathIcon, 
  XMarkIcon, 
  PencilIcon, 
  TrashIcon 
} from '@heroicons/vue/24/outline'

// Toast notifications
const toast = useToast()

// Use composable instead of direct store access
const {
  jobs,
  filteredJobs,
  filters: storeFilters, // Get filters from composable (computed ref)
  loading,
  error,
  fetchJobs,
  createJob,
  updateJob,
  deleteJob,
  setFilters,
  clearFilters,
  clearError,
  currentPage,
  pageSize,
  total,
  totalPages,
  goToPage,
  changePageSize
} = useJobs()


// Load accounts for dropdown
const { accounts, fetchAccounts } = useAccounts()

// Router for URL sync
const route = useRoute()
const router = useRouter()

// WebSocket for real-time updates
const wsStore = useWebSocketStore()
let wsClient = null

// WebSocket setup for real-time job updates
const setupWebSocket = () => {
  wsClient = wsStore.connect('jobs', filters.value.accountId || null)
  
  wsClient.on('connect', () => {
    console.log('WebSocket connected to jobs room')
  })
  
  wsClient.on('disconnect', () => {
    console.log('WebSocket disconnected from jobs room')
  })
  
  // Listen for job.created event (e.g., from Excel upload)
  wsClient.on('job.created', async (data) => {
    try {
      // Refresh jobs list when new jobs are created
      await refreshJobs()
    } catch (error) {
      console.error('Error refreshing jobs on job.created event:', error)
    }
  })
  
  // Listen for job.updated event
  wsClient.on('job.updated', async (data) => {
    try {
      // Refresh jobs list when jobs are updated
      await refreshJobs()
    } catch (error) {
      console.error('Error refreshing jobs on job.updated event:', error)
    }
  })
}

const showCreateModal = ref(false)
const showEditModal = ref(false)
const editingJob = ref(null)
const filters = ref({
  accountId: '',
  status: '',
  platform: '',
  scheduled_from: '',
  scheduled_to: ''
})

// Debounce timer for auto-apply filters
let debounceTimer = null
const DEBOUNCE_DELAY = 500

// Flag to prevent infinite loop when syncing URL
let isSyncingFromURL = false
// Track last synced query to avoid triggering URL watcher for our own syncs
let lastSyncedQuery = null

/**
 * Sync filters to URL query parameters
 */
const syncFiltersToURL = () => {
  if (isSyncingFromURL) return
  
  const query = {}
  
  if (filters.value.accountId) query.account_id = filters.value.accountId
  if (filters.value.status) query.status = filters.value.status
  if (filters.value.platform) query.platform = filters.value.platform
  if (filters.value.scheduled_from) query.scheduled_from = filters.value.scheduled_from
  if (filters.value.scheduled_to) query.scheduled_to = filters.value.scheduled_to
  if (currentPage.value > 1) query.page = currentPage.value.toString()
  
  // Store the query we're about to set to avoid triggering URL watcher
  const queryStr = JSON.stringify(query)
  lastSyncedQuery = queryStr
  
  // Update URL without reload
  router.replace({ query })
  
  // Clear the flag after a delay to allow URL watcher to process browser navigation
  setTimeout(() => {
    if (lastSyncedQuery === queryStr) {
      lastSyncedQuery = null
    }
  }, 300)
}

/**
 * Initialize filters from URL query parameters
 */
const initFiltersFromURL = () => {
  const query = route.query
  
  if (query.account_id) filters.value.accountId = query.account_id
  if (query.status) filters.value.status = query.status
  if (query.platform) filters.value.platform = query.platform
  if (query.scheduled_from) filters.value.scheduled_from = query.scheduled_from
  if (query.scheduled_to) filters.value.scheduled_to = query.scheduled_to
  
  // Sync to store
  setFilters({
    accountId: filters.value.accountId || null,
    status: filters.value.status || null,
    platform: filters.value.platform || null,
    scheduled_from: filters.value.scheduled_from || null,
    scheduled_to: filters.value.scheduled_to || null
  })
  
  // Remove reload from URL after reading (it's only a signal, not a filter)
  if (query.reload === 'true') {
    router.replace({ query: { ...query, reload: undefined } })
  }
}

/**
 * Apply filters with debounce
 */
const applyFiltersDebounced = () => {
  // Clear existing timer
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  
  // Set new timer
  debounceTimer = setTimeout(async () => {
    // Prevent URL watcher from interfering
    isSyncingFromURL = true
    
    // Get current filter values - preserve non-empty values, convert empty to null
    const normalizeFilter = (value) => {
      if (!value || (typeof value === 'string' && value.trim() === '')) {
        return null
      }
      return typeof value === 'string' ? value.trim() : value
    }
    
    const filterValues = {
      accountId: normalizeFilter(filters.value.accountId),
      status: normalizeFilter(filters.value.status),
      platform: normalizeFilter(filters.value.platform),
      scheduled_from: normalizeFilter(filters.value.scheduled_from),
      scheduled_to: normalizeFilter(filters.value.scheduled_to)
    }
    
    // Sync filters to store
    setFilters(filterValues)
    
    // Sync to URL
    syncFiltersToURL()
    
    // Reset to first page when filters change
    await fetchJobs({
      accountId: filterValues.accountId,
      status: filterValues.status,
      platform: filterValues.platform,
      scheduled_from: filterValues.scheduled_from,
      scheduled_to: filterValues.scheduled_to,
      page: 1,
      limit: pageSize.value
    })
    
    // Reset flag after a delay
    setTimeout(() => {
      isSyncingFromURL = false
    }, 200)
  }, DEBOUNCE_DELAY)
}

// Watch filter changes and auto-apply with debounce
// Only watch if not syncing from URL to avoid conflicts
watch(
  () => [filters.value.accountId, filters.value.status, filters.value.platform, filters.value.scheduled_from, filters.value.scheduled_to],
  (newVal, oldVal) => {
    // Skip if we're syncing from URL to avoid infinite loop
    if (!isSyncingFromURL) {
      applyFiltersDebounced()
    }
  },
  { deep: true }
)

// Helper function to get default scheduled time (1 hour from now)
const getDefaultScheduledTime = () => {
  const oneHourLater = new Date()
  oneHourLater.setHours(oneHourLater.getHours() + 1)
  // Format as datetime-local string (YYYY-MM-DDTHH:mm)
  const year = oneHourLater.getFullYear()
  const month = String(oneHourLater.getMonth() + 1).padStart(2, '0')
  const day = String(oneHourLater.getDate()).padStart(2, '0')
  const hours = String(oneHourLater.getHours()).padStart(2, '0')
  const minutes = String(oneHourLater.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

const newJob = ref({
  content: '',
  account_id: '',
  platform: 'threads',
  priority: 'normal',
  scheduled_time: getDefaultScheduledTime(),
  link_aff: '',
  max_retries: 3
})

const jobColumns = [
  { key: 'job_id', label: 'Job ID' },
  { key: 'account_id', label: 'Account' },
  { key: 'platform', label: 'Platform' },
  { key: 'content', label: 'Content' },
  { key: 'status', label: 'Status' },
  { key: 'created_at', label: 'Created' }
]

/**
 * Manual apply filters (optional, for immediate apply)
 */
const applyFilters = async () => {
  // Clear debounce timer if exists
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  
  setFilters({
    accountId: filters.value.accountId || null,
    status: filters.value.status || null,
    platform: filters.value.platform || null,
    scheduled_from: filters.value.scheduled_from || null,
    scheduled_to: filters.value.scheduled_to || null
  })
  
  // Sync to URL
  syncFiltersToURL()
  
  // Reset to first page when applying filters
  await fetchJobs({
    accountId: filters.value.accountId || null,
    status: filters.value.status || null,
    platform: filters.value.platform || null,
    scheduled_from: filters.value.scheduled_from || null,
    scheduled_to: filters.value.scheduled_to || null,
    page: 1,
    limit: pageSize.value
  })
}

/**
 * Clear filters and reset pagination
 */
const handleClearFilters = async () => {
  // Clear debounce timer if exists
  if (debounceTimer) {
    clearTimeout(debounceTimer)
    debounceTimer = null
  }
  
  // Reset filter values
  filters.value = { 
    accountId: '', 
    status: '', 
    platform: '',
    scheduled_from: '',
    scheduled_to: ''
  }
  
  // Clear in store
  clearFilters()
  
  // Clear URL query params
  router.replace({ query: {} })
  
  // Reset pagination and fetch jobs
  await fetchJobs({
    page: 1,
    limit: pageSize.value
  })
}

const refreshJobs = async () => {
  // NOTE: reload=true để force reload từ server và cập nhật jobs đã xóa
  // Khi user xóa job từ database, frontend cần reload từ server để cập nhật danh sách
  await fetchJobs({ 
    accountId: filters.value.accountId || null,
    status: filters.value.status || null,
    platform: filters.value.platform || null,
    scheduled_from: filters.value.scheduled_from || null,
    scheduled_to: filters.value.scheduled_to || null,
    page: currentPage.value,
    limit: pageSize.value,
    reload: true  // Force reload from server to get latest data (including deleted jobs removal)
  })
  // Sync URL after refresh
  syncFiltersToURL()
}

const handlePageChange = async (page) => {
  await goToPage(page)
  
  // Update URL with new page, preserving all filter params
  const query = {}
  
  // Preserve filters from current state (not from route.query which might be stale)
  if (filters.value.accountId) query.account_id = filters.value.accountId
  if (filters.value.status) query.status = filters.value.status
  if (filters.value.platform) query.platform = filters.value.platform
  if (filters.value.scheduled_from) query.scheduled_from = filters.value.scheduled_from
  if (filters.value.scheduled_to) query.scheduled_to = filters.value.scheduled_to
  
  // Add page if > 1
  if (page > 1) {
    query.page = page.toString()
  }
  
  // Store the query we're about to set to avoid triggering URL watcher
  const queryStr = JSON.stringify(query)
  lastSyncedQuery = queryStr
  
  router.replace({ query })
}

const handlePageSizeChange = async (size) => {
  await changePageSize(size)
  // Reset to page 1 and update URL, preserving all filter params
  const query = {}
  
  // Preserve filters from current state (not from route.query which might be stale)
  if (filters.value.accountId) query.account_id = filters.value.accountId
  if (filters.value.status) query.status = filters.value.status
  if (filters.value.platform) query.platform = filters.value.platform
  if (filters.value.scheduled_from) query.scheduled_from = filters.value.scheduled_from
  if (filters.value.scheduled_to) query.scheduled_to = filters.value.scheduled_to
  
  // Page is reset to 1, so don't include it in URL
  
  // Store the query we're about to set to avoid triggering URL watcher
  const queryStr = JSON.stringify(query)
  lastSyncedQuery = queryStr
  
  router.replace({ query })
}

// Watch for URL changes (browser back/forward)
// Only react to URL changes that come from browser navigation, not from our own syncs
watch(
  () => route.query,
  (newQuery) => {
    // Skip if this is our own sync (compare with last synced query)
    const queryStr = JSON.stringify(newQuery)
    if (lastSyncedQuery === queryStr) {
      // This is our own sync, ignore
      return
    }
    
    // This is a browser navigation (back/forward), process it
    isSyncingFromURL = true
    
    // Only update if filters changed (not pagination)
    const urlFilters = {
      accountId: newQuery.account_id || '',
      status: newQuery.status || '',
      platform: newQuery.platform || '',
      scheduled_from: newQuery.scheduled_from || '',
      scheduled_to: newQuery.scheduled_to || ''
    }
    
    // Check if filters actually changed
    const filtersChanged = 
      urlFilters.accountId !== filters.value.accountId ||
      urlFilters.status !== filters.value.status ||
      urlFilters.platform !== filters.value.platform ||
      urlFilters.scheduled_from !== filters.value.scheduled_from ||
      urlFilters.scheduled_to !== filters.value.scheduled_to
    
    if (filtersChanged) {
      // Update filters from URL
      filters.value = urlFilters
      // Sync to store
      setFilters({
        accountId: urlFilters.accountId || null,
        status: urlFilters.status || null,
        platform: urlFilters.platform || null,
        scheduled_from: urlFilters.scheduled_from || null,
        scheduled_to: urlFilters.scheduled_to || null
      })
      
      // Fetch jobs with new filters
      const page = newQuery.page ? parseInt(newQuery.page, 10) : 1
      fetchJobs({
        accountId: urlFilters.accountId || null,
        status: urlFilters.status || null,
        platform: urlFilters.platform || null,
        scheduled_from: urlFilters.scheduled_from || null,
        scheduled_to: urlFilters.scheduled_to || null,
        page: page,
        limit: pageSize.value
      })
    } else if (newQuery.page) {
      // Only page changed, update pagination
      const page = parseInt(newQuery.page, 10)
      if (page !== currentPage.value && page >= 1 && page <= totalPages.value) {
        goToPage(page)
      }
    }
    
    // Reset flag after a short delay
    setTimeout(() => {
      isSyncingFromURL = false
    }, 200)
  },
  { deep: true }
)

const handleCreateJob = async () => {
  try {
    // Convert datetime-local from Vietnam timezone to UTC ISO string for API
    // Handle empty account_id (convert to null if empty string)
    // Fix: account_id can be number (from FormSelect auto-conversion) or string
    // Preserve original string value from accounts list to maintain leading zeros (e.g., "02")
    let accountIdValue = newJob.value.account_id
    if (accountIdValue != null && accountIdValue !== '') {
      // If account_id is a number (FormSelect converted it), lookup original string from accounts
      if (typeof accountIdValue === 'number') {
        const foundAccount = accounts.value.find(acc => {
          // Try to match by converting both to numbers for comparison
          const accIdNum = Number(acc.account_id)
          return !isNaN(accIdNum) && accIdNum === accountIdValue
        })
        if (foundAccount) {
          // Use original string value from accounts list (preserves leading zeros)
          accountIdValue = foundAccount.account_id
        } else {
          // Fallback: convert to string (but will lose leading zeros)
          accountIdValue = String(accountIdValue)
        }
      } else {
        // Already a string, just trim
        accountIdValue = String(accountIdValue).trim()
      }
      // If empty after processing, set to null
      if (accountIdValue === '') {
        accountIdValue = null
      }
    } else {
      accountIdValue = null
    }
    
    const jobData = {
      ...newJob.value,
      account_id: accountIdValue,
      scheduled_time: datetimeLocalToUTC(newJob.value.scheduled_time)
    }
    
    // Business logic is now in composable (formatting, scheduled_time default)
    const result = await createJob(jobData)
    
    if (result) {
      showCreateModal.value = false
      // Reset form with all fields
      newJob.value = {
        content: '',
        account_id: '',
        platform: 'threads',
        priority: 'normal',
        scheduled_time: getDefaultScheduledTime(),
        link_aff: '',
        max_retries: 3
      }
      // Sync local filters with store filters after job creation
      // This ensures the dropdown shows the correct filter value
      if (storeFilters) {
        filters.value.accountId = storeFilters.value.accountId || ''
        filters.value.status = storeFilters.value.status || ''
        filters.value.platform = storeFilters.value.platform || ''
        filters.value.scheduled_from = storeFilters.value.scheduled_from || ''
        filters.value.scheduled_to = storeFilters.value.scheduled_to || ''
      }
    }
  } catch (error) {
    console.error('Error creating job:', error)
    // Error is already handled in createJob composable, but show toast for user feedback
    toast.error('Failed to create job', error.message || 'Unknown error occurred')
  }
}

const editJob = (job) => {
  try {
    // Don't allow editing completed or running jobs
    if (job.status === 'completed' || job.status === 'running') {
      return
    }
    
    // Populate editing job with current job data
    // Convert UTC datetime to datetime-local format in Vietnam timezone
    const scheduledTimeStr = job.scheduled_time 
      ? utcToDatetimeLocal(job.scheduled_time)
      : getDefaultScheduledTime()
    
    // Handle priority and platform - they might be enum objects or strings
    // JobPriority enum values: LOW=1, NORMAL=2, HIGH=3, URGENT=4
    // Platform enum values: THREADS="threads", FACEBOOK="facebook"
    let priorityValue = 'normal'
    if (job.priority) {
      if (typeof job.priority === 'string') {
        priorityValue = job.priority.toLowerCase()
      } else {
        // Get numeric value from enum
        const priorityNum = job.priority.value || job.priority
        // Map number to string: 1=LOW, 2=NORMAL, 3=HIGH, 4=URGENT
        const priorityMap = { 1: 'low', 2: 'normal', 3: 'high', 4: 'urgent' }
        priorityValue = priorityMap[priorityNum] || 'normal'
      }
    }
    
    let platformValue = 'threads'
    if (job.platform) {
      if (typeof job.platform === 'string') {
        platformValue = job.platform.toLowerCase()
      } else {
        // Platform enum value is already a string ("threads" or "facebook")
        platformValue = (job.platform.value || String(job.platform)).toLowerCase()
      }
    }
    
    editingJob.value = {
      job_id: job.job_id,
      content: job.content || '',
      account_id: job.account_id || '',
      platform: platformValue.toLowerCase(),
      priority: priorityValue.toLowerCase(),
      scheduled_time: scheduledTimeStr,
      link_aff: job.link_aff || '',
      max_retries: job.max_retries || 3
    }
    
    showEditModal.value = true
  } catch (error) {
    console.error('Error in editJob:', error)
    toast.error('Failed to edit job', error.message || 'Unknown error occurred')
  }
}

const handleUpdateJob = async () => {
  if (!editingJob.value) return
  
  // Convert datetime-local from Vietnam timezone to UTC ISO string for API
  const jobData = {
    ...editingJob.value,
    account_id: editingJob.value.account_id?.trim() || null,
    scheduled_time: datetimeLocalToUTC(editingJob.value.scheduled_time)
  }
  
  // Remove job_id from update data (it's in the URL)
  const jobId = jobData.job_id
  delete jobData.job_id
  
  const result = await updateJob(jobId, jobData)
  
  if (result) {
    showEditModal.value = false
    editingJob.value = null
    // Refresh jobs list after successful update
    // Use reload: true to get fresh data from server after update
    await fetchJobs({ 
      accountId: filters.value.accountId || null,
      status: filters.value.status || null,
      platform: filters.value.platform || null,
      scheduled_from: filters.value.scheduled_from || null,
      scheduled_to: filters.value.scheduled_to || null,
      page: currentPage.value,
      limit: pageSize.value,
      reload: true  // Reload from server to get updated job data
    })
  }
}

const handleDeleteJob = async (jobId) => {
  // Use proper confirmation dialog (UX guidelines: Confirmation Dialogs)
  const confirmed = window.confirm(
    `Are you sure you want to delete job ${jobId}? This action cannot be undone.`
  )
  if (confirmed) {
    try {
      const result = await deleteJob(jobId)
      if (result) {
        // Refresh jobs list after successful delete
        await refreshJobs()
      }
    } catch (error) {
      console.error('Failed to delete job:', error)
      toast.error('Failed to delete job', error.message || 'Unknown error occurred')
    }
  }
}

onMounted(async () => {
  // Initialize filters from URL if present
  initFiltersFromURL()
  
  // Load accounts for dropdown
  await fetchAccounts()
  
  // Setup WebSocket for real-time updates
  setupWebSocket()
  
  // Fetch jobs with initial filters (from URL or defaults)
  // Always reload from server when page mounts to ensure fresh data
  const initialPage = route.query.page ? parseInt(route.query.page, 10) : 1
  await fetchJobs({
    accountId: filters.value.accountId || null,
    status: filters.value.status || null,
    platform: filters.value.platform || null,
    scheduled_from: filters.value.scheduled_from || null,
    scheduled_to: filters.value.scheduled_to || null,
    page: initialPage,
    limit: pageSize.value,
    reload: true  // Always reload from server on mount to ensure fresh data
  })
})

onUnmounted(() => {
  // Cleanup WebSocket connection
  if (wsClient) {
    wsStore.disconnect('jobs', filters.value.accountId || null)
  }
})
</script>
