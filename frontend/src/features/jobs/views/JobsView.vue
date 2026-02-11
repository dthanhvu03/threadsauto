<template>
  <div>
    <div class="mb-6 flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900 mb-1">📅 Jobs</h1>
        <p class="text-sm text-gray-600">Manage and monitor your scheduled jobs</p>
      </div>
      <Button @click="showCreateModal = true">+ Create Job</Button>
    </div>

    <Alert
      v-if="error"
      type="error"
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <!-- Filters -->
    <Card class="mb-6" padding="md">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <FormInput
          v-model="localFilters.accountId"
          label="Account ID"
          placeholder="Filter by account"
        />
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            v-model="localFilters.status"
            class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Status</option>
            <option value="pending">Pending</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Platform</label>
          <select
            v-model="localFilters.platform"
            class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
          >
            <option value="">All Platforms</option>
            <option value="threads">Threads</option>
            <option value="facebook">Facebook</option>
          </select>
        </div>
        <div class="flex space-x-2 items-end">
          <Button variant="outline" @click="applyFilters">Apply Filters</Button>
          <Button variant="outline" @click="handleClearFilters">Clear</Button>
        </div>
      </div>
    </Card>

    <!-- Jobs List -->
    <Card>
      <template #header>
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Jobs List</h3>
          <Button size="sm" variant="outline" @click="handleRefreshJobs">🔄 Refresh</Button>
        </div>
      </template>
      <div v-if="loading" class="flex justify-center py-12">
        <LoadingSpinner size="lg" />
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
        <template #actions="{ row }">
          <div class="flex space-x-2">
            <Button size="sm" variant="outline" @click="editJob(row)">Edit</Button>
            <Button size="sm" variant="danger" @click="handleDeleteJob(row.job_id)">Delete</Button>
          </div>
        </template>
      </Table>
    </Card>

    <!-- Create Job Modal -->
    <Modal v-model="showCreateModal" title="Create New Job" size="lg">
      <form @submit.prevent="handleCreateJob">
        <div class="space-y-4">
          <FormInput
            v-model="newJob.content"
            label="Content"
            placeholder="Enter job content"
            required
          />
          <FormInput
            v-model="newJob.account_id"
            label="Account ID"
            placeholder="Enter account ID"
            required
          />
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Platform</label>
            <select
              v-model="newJob.platform"
              class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="THREADS">Threads</option>
              <option value="FACEBOOK">Facebook</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <select
              v-model="newJob.priority"
              class="block w-full rounded-lg border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 sm:text-sm"
            >
              <option value="NORMAL">Normal</option>
              <option value="HIGH">High</option>
              <option value="URGENT">Urgent</option>
            </select>
          </div>
          <FormInput
            v-model="newJob.scheduled_time"
            label="Scheduled Time"
            type="datetime-local"
            required
          />
        </div>
      </form>
      <template #footer>
        <Button variant="outline" @click="showCreateModal = false">Cancel</Button>
        <Button @click="handleCreateJob" :loading="loading">Create</Button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useJobs } from '../composables/useJobs'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Table from '@/components/common/Table.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import Modal from '@/components/common/Modal.vue'
import FormInput from '@/components/common/FormInput.vue'

// Use composable
const {
  jobs,
  filteredJobs,
  loading,
  error,
  fetchJobs,
  createJob,
  deleteJob,
  setFilters,
  clearFilters,
  clearError
} = useJobs()

const showCreateModal = ref(false)
const localFilters = ref({
  accountId: '',
  status: '',
  platform: ''
})

const newJob = ref({
  content: '',
  account_id: '',
  platform: 'THREADS',
  priority: 'NORMAL',
  scheduled_time: ''
})

const jobColumns = [
  { key: 'job_id', label: 'Job ID' },
  { key: 'account_id', label: 'Account' },
  { key: 'platform', label: 'Platform' },
  { key: 'content', label: 'Content' },
  { key: 'status', label: 'Status' },
  { key: 'created_at', label: 'Created' }
]

const applyFilters = () => {
  setFilters({
    accountId: localFilters.value.accountId || null,
    status: localFilters.value.status || null,
    platform: localFilters.value.platform || null
  })
}

const handleClearFilters = () => {
  localFilters.value = { accountId: '', status: '', platform: '' }
  clearFilters()
}

const handleRefreshJobs = async () => {
  await fetchJobs({ 
    accountId: localFilters.value.accountId || null,
    reload: true 
  })
}

const handleCreateJob = async () => {
  // Format scheduled_time to ISO format
  const scheduledTime = new Date(newJob.value.scheduled_time).toISOString()
  
  const jobData = {
    account_id: newJob.value.account_id,
    content: newJob.value.content,
    platform: newJob.value.platform,
    priority: newJob.value.priority,
    scheduled_time: scheduledTime
  }
  
  const result = await createJob(jobData)
  if (result) {
    showCreateModal.value = false
    newJob.value = {
      content: '',
      account_id: '',
      platform: 'THREADS',
      priority: 'NORMAL',
      scheduled_time: ''
    }
  }
}

const editJob = (job) => {
  // TODO: Implement edit functionality
  console.log('Edit job:', job)
}

const handleDeleteJob = async (jobId) => {
  if (confirm('Are you sure you want to delete this job?')) {
    await deleteJob(jobId)
  }
}

onMounted(async () => {
  await fetchJobs()
})
</script>
