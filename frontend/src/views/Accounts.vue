<template>
  <div>
    <div class="mb-4 md:mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-3 md:gap-0">
      <div>
        <h1 class="text-xl md:text-2xl font-semibold text-gray-900 mb-1">👤 Accounts</h1>
        <p class="text-xs md:text-sm text-gray-600">Manage your accounts</p>
      </div>
      <Button @click="showAddModal = true" class="w-full md:w-auto">+ Add Account</Button>
    </div>

    <Alert
      v-if="error"
      type="error"
      :message="error"
      dismissible
      @dismiss="clearError"
    />

    <Alert
      v-if="successMessage"
      type="success"
      :message="successMessage"
      dismissible
      @dismiss="successMessage = null"
    />

    <div v-if="loading" class="flex justify-center py-12">
      <LoadingSpinner size="lg" />
    </div>

    <div v-else-if="accounts.length === 0" class="py-8">
      <EmptyState
        title="No accounts"
        description="Add your first account to get started"
      />
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <Card
        v-for="account in accounts"
        :key="account.account_id"
      >
        <div class="space-y-4">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-1">{{ account.account_id }}</h3>
            <p class="text-xs text-gray-500 mb-2">Account ID</p>
            <div v-if="account.metadata && account.metadata.username" class="mb-3">
              <p class="text-sm text-gray-600">
                <span class="font-medium">Username:</span> {{ account.metadata.username }}
              </p>
            </div>
          </div>
          <div class="mt-4 p-3 bg-gray-50 rounded-md">
            <p class="text-2xl font-semibold text-primary-600">
              {{ account.jobs_count !== undefined ? account.jobs_count : 0 }}
            </p>
            <p class="text-sm text-gray-600">Total Jobs</p>
          </div>
          <div class="flex flex-col md:flex-row gap-2 md:space-x-2 pt-4 border-t border-gray-200">
            <Button
              size="sm"
              variant="outline"
              @click="viewAccountStats(account.account_id)"
              class="flex-1 w-full md:w-auto"
            >
              Stats
            </Button>
            <Button
              size="sm"
              variant="danger"
              @click="handleDeleteAccount(account.account_id)"
              class="flex-1 w-full md:w-auto"
            >
              Delete
            </Button>
          </div>
        </div>
      </Card>
    </div>

    <!-- Add Account Modal -->
    <Modal v-model="showAddModal" title="Add New Account" size="md">
      <form @submit.prevent="handleAddAccount">
        <div class="space-y-4">
          <FormInput
            v-model="newAccount.account_id"
            label="Account ID"
            placeholder="Enter account ID"
            required
          />
        </div>
      </form>
      <template #footer>
        <div class="flex flex-col md:flex-row gap-2 md:gap-3 w-full md:w-auto md:ml-auto">
          <Button variant="outline" @click="showAddModal = false" class="w-full md:w-auto">Cancel</Button>
          <Button @click="handleAddAccount" :loading="loading" class="w-full md:w-auto">Add Account</Button>
        </div>
      </template>
    </Modal>

    <!-- Account Stats Modal -->
    <Modal v-model="showStatsModal" title="Account Statistics" size="lg">
      <div v-if="loading" class="flex justify-center py-12">
        <LoadingSpinner size="lg" />
      </div>
      <div v-else-if="accountStatsData" class="space-y-6">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 mb-4">
            Account: <span class="text-primary-600">{{ selectedAccountForStats }}</span>
          </h3>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3 sm:gap-4">
          <Card padding="md">
            <div class="text-center">
              <p class="text-sm text-gray-600 mb-2">Total Jobs</p>
              <p class="text-2xl font-semibold text-primary-600">
                {{ accountStatsData.jobs_count || 0 }}
              </p>
            </div>
          </Card>
          
          <Card padding="md">
            <div class="text-center">
              <p class="text-sm text-gray-600 mb-2">Profile Path</p>
              <p class="text-xs text-gray-500 break-all">
                {{ accountStatsData.profile_path || 'N/A' }}
              </p>
            </div>
          </Card>
        </div>

        <div v-if="accountStatsData.metadata" class="mt-4">
          <h4 class="text-sm font-semibold text-gray-700 mb-2">Metadata</h4>
          <pre class="bg-gray-50 p-4 rounded-lg text-xs overflow-auto border border-gray-200">{{ JSON.stringify(accountStatsData.metadata, null, 2) }}</pre>
        </div>
      </div>
      <div v-else class="py-8 text-center">
        <p class="text-gray-500">No statistics available</p>
      </div>
      <template #footer>
        <div class="flex justify-end w-full">
          <Button variant="outline" @click="showStatsModal = false" class="w-full sm:w-auto">Close</Button>
        </div>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
// Use composable instead of direct store access (Phase 3)
import { useAccounts } from '@/features/accounts/composables/useAccounts'
import Card from '@/components/common/Card.vue'
import Button from '@/components/common/Button.vue'
import Alert from '@/components/common/Alert.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import Modal from '@/components/common/Modal.vue'
import FormInput from '@/components/common/FormInput.vue'

// Use composable instead of direct store access
const {
  accounts,
  accountStats,
  loading,
  error,
  fetchAccounts,
  fetchAccountStats,
  createAccount,
  deleteAccount,
  clearError
} = useAccounts()

const showAddModal = ref(false)
const successMessage = ref(null)
const newAccount = ref({
  account_id: ''
})

const handleAddAccount = async () => {
  // Business logic (validation) is now in composable
  const result = await createAccount(newAccount.value)
  if (result) {
    successMessage.value = `Account "${newAccount.value.account_id}" created successfully`
    showAddModal.value = false
    newAccount.value = { account_id: '' }
    // Clear success message after 3 seconds
    setTimeout(() => {
      successMessage.value = null
    }, 3000)
  }
}

const showStatsModal = ref(false)
const selectedAccountForStats = ref(null)
const accountStatsData = ref(null)

const viewAccountStats = async (accountId) => {
  selectedAccountForStats.value = accountId
  accountStatsData.value = null
  showStatsModal.value = true
  
  const stats = await fetchAccountStats(accountId)
  if (stats) {
    accountStatsData.value = stats
  }
}

const handleDeleteAccount = async (accountId) => {
  if (confirm(`Are you sure you want to delete account ${accountId}?`)) {
    const result = await deleteAccount(accountId)
    if (result) {
      successMessage.value = `Account "${accountId}" deleted successfully`
      // Clear success message after 3 seconds
      setTimeout(() => {
        successMessage.value = null
      }, 3000)
    }
  }
}

onMounted(async () => {
  await fetchAccounts()
  // Debug: Log accounts to console
  console.log('Accounts in view:', accounts)
})
</script>
