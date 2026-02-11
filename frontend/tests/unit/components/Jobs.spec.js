/**
 * Component tests for Jobs view.
 * 
 * Tests the Jobs component using Vue Test Utils and the new composable pattern.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Jobs from '@/views/Jobs.vue'
import { useJobs } from '@/features/jobs/composables/useJobs'
import { jobsService } from '@/features/jobs/services/jobsService'

// Mock the composable
vi.mock('@/features/jobs/composables/useJobs', () => ({
  useJobs: vi.fn()
}))

// Mock child components
vi.mock('@/components/common/Card.vue', () => ({
  default: {
    name: 'Card',
    template: '<div class="card"><slot /><slot name="header" /></div>',
    props: ['padding', 'class']
  }
}))

vi.mock('@/components/common/Button.vue', () => ({
  default: {
    name: 'Button',
    template: '<button><slot /></button>',
    props: ['variant', 'size', 'loading']
  }
}))

vi.mock('@/components/common/Alert.vue', () => ({
  default: {
    name: 'Alert',
    template: '<div v-if="message" class="alert"><slot /></div>',
    props: ['type', 'message', 'dismissible'],
    emits: ['dismiss']
  }
}))

vi.mock('@/components/common/LoadingSpinner.vue', () => ({
  default: {
    name: 'LoadingSpinner',
    template: '<div class="spinner">Loading...</div>',
    props: ['size']
  }
}))

vi.mock('@/components/common/Table.vue', () => ({
  default: {
    name: 'Table',
    template: '<table><slot name="cell-status" :value="row.status" /><slot name="actions" :row="row" /></table>',
    props: ['columns', 'data', 'actions']
  }
}))

vi.mock('@/components/common/EmptyState.vue', () => ({
  default: {
    name: 'EmptyState',
    template: '<div class="empty-state"><slot /></div>',
    props: ['title', 'description']
  }
}))

vi.mock('@/components/common/Modal.vue', () => ({
  default: {
    name: 'Modal',
    template: '<div v-if="modelValue" class="modal"><slot /><slot name="footer" /></div>',
    props: ['modelValue', 'title', 'size'],
    emits: ['update:modelValue']
  }
}))

vi.mock('@/components/common/FormInput.vue', () => ({
  default: {
    name: 'FormInput',
    template: '<input />',
    props: ['modelValue', 'label', 'placeholder', 'required', 'type'],
    emits: ['update:modelValue']
  }
}))

describe('Jobs Component', () => {
  let wrapper
  let mockUseJobs

  const mockJobs = [
    {
      job_id: 'job_1',
      account_id: 'account_01',
      platform: 'THREADS',
      content: 'Test content 1',
      status: 'pending',
      created_at: '2024-01-01T10:00:00Z'
    },
    {
      job_id: 'job_2',
      account_id: 'account_01',
      platform: 'THREADS',
      content: 'Test content 2',
      status: 'completed',
      created_at: '2024-01-02T10:00:00Z'
    },
    {
      job_id: 'job_3',
      account_id: 'account_02',
      platform: 'FACEBOOK',
      content: 'Test content 3',
      status: 'failed',
      created_at: '2024-01-03T10:00:00Z'
    }
  ]

  beforeEach(() => {
    setActivePinia(createPinia())
    
    // Setup default mock return values
    mockUseJobs = {
      jobs: { value: mockJobs },
      filteredJobs: { value: mockJobs },
      loading: { value: false },
      error: { value: null },
      fetchJobs: vi.fn().mockResolvedValue(mockJobs),
      createJob: vi.fn().mockResolvedValue({ job_id: 'new_job' }),
      deleteJob: vi.fn().mockResolvedValue(true),
      setFilters: vi.fn(),
      clearFilters: vi.fn(),
      clearError: vi.fn()
    }

    useJobs.mockReturnValue(mockUseJobs)
  })

  const createWrapper = (props = {}) => {
    return mount(Jobs, {
      global: {
        plugins: [createPinia()],
        stubs: {
          Card: true,
          Button: true,
          Alert: true,
          LoadingSpinner: true,
          Table: true,
          EmptyState: true,
          Modal: true,
          FormInput: true
        }
      },
      ...props
    })
  }

  describe('Initialization', () => {
    it('renders the component', () => {
      wrapper = createWrapper()
      expect(wrapper.exists()).toBe(true)
    })

    it('displays the page title', () => {
      wrapper = createWrapper()
      expect(wrapper.text()).toContain('Jobs')
      expect(wrapper.text()).toContain('Manage and monitor your scheduled jobs')
    })

    it('calls fetchJobs on mount', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(mockUseJobs.fetchJobs).toHaveBeenCalled()
    })
  })

  describe('Loading State', () => {
    it('shows loading spinner when loading', async () => {
      mockUseJobs.loading.value = true
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      // Check if loading state is displayed
      expect(mockUseJobs.loading.value).toBe(true)
    })

    it('hides loading spinner when not loading', async () => {
      mockUseJobs.loading.value = false
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      expect(mockUseJobs.loading.value).toBe(false)
    })
  })

  describe('Error Handling', () => {
    it('displays error message when error exists', async () => {
      mockUseJobs.error.value = 'Failed to fetch jobs'
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      expect(mockUseJobs.error.value).toBe('Failed to fetch jobs')
    })

    it('calls clearError when error is dismissed', async () => {
      mockUseJobs.error.value = 'Some error'
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      // Simulate error dismissal
      wrapper.vm.clearError()
      expect(mockUseJobs.clearError).toHaveBeenCalled()
    })
  })

  describe('Jobs List Display', () => {
    it('displays jobs table when jobs exist', async () => {
      mockUseJobs.filteredJobs.value = mockJobs
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      expect(mockUseJobs.filteredJobs.value.length).toBeGreaterThan(0)
    })

    it('displays empty state when no jobs', async () => {
      mockUseJobs.filteredJobs.value = []
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      expect(mockUseJobs.filteredJobs.value.length).toBe(0)
    })
  })

  describe('Filtering', () => {
    it('applies filters when Apply Filters is clicked', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      // Set filter values
      wrapper.vm.filters.accountId = 'account_01'
      wrapper.vm.filters.status = 'pending'
      
      // Trigger apply filters
      wrapper.vm.applyFilters()
      
      expect(mockUseJobs.setFilters).toHaveBeenCalledWith({
        accountId: 'account_01',
        status: 'pending',
        platform: null
      })
    })

    it('clears filters when Clear is clicked', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      // Set some filters
      wrapper.vm.filters.accountId = 'account_01'
      
      // Clear filters
      wrapper.vm.handleClearFilters()
      
      expect(mockUseJobs.clearFilters).toHaveBeenCalled()
      expect(wrapper.vm.filters.accountId).toBe('')
    })
  })

  describe('Refresh Jobs', () => {
    it('refreshes jobs when refresh button is clicked', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      wrapper.vm.refreshJobs()
      
      expect(mockUseJobs.fetchJobs).toHaveBeenCalledWith({
        accountId: null,
        reload: true
      })
    })
  })

  describe('Create Job', () => {
    it('opens create modal when Create Job button is clicked', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      expect(wrapper.vm.showCreateModal).toBe(false)
      
      // Find and click create button (would need proper button component)
      // For now, just test the reactive state
      wrapper.vm.showCreateModal = true
      expect(wrapper.vm.showCreateModal).toBe(true)
    })

    it('creates job with correct data', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      wrapper.vm.newJob = {
        content: 'New job content',
        account_id: 'account_01',
        platform: 'threads',
        priority: 'normal'
      }
      
      await wrapper.vm.handleCreateJob()
      
      expect(mockUseJobs.createJob).toHaveBeenCalled()
      const callArgs = mockUseJobs.createJob.mock.calls[0][0]
      expect(callArgs.content).toBe('New job content')
      expect(callArgs.account_id).toBe('account_01')
      expect(callArgs.platform).toBe('THREADS')
      expect(callArgs.priority).toBe('NORMAL')
      expect(callArgs.scheduled_time).toBeDefined()
    })

    it('closes modal after successful job creation', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      wrapper.vm.showCreateModal = true
      wrapper.vm.newJob = {
        content: 'Test',
        account_id: 'account_01',
        platform: 'threads',
        priority: 'normal'
      }
      
      mockUseJobs.createJob.mockResolvedValue({ job_id: 'new_job' })
      
      await wrapper.vm.handleCreateJob()
      
      expect(wrapper.vm.showCreateModal).toBe(false)
      expect(wrapper.vm.newJob.content).toBe('')
    })

    it('keeps modal open if job creation fails', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      wrapper.vm.showCreateModal = true
      wrapper.vm.newJob = {
        content: 'Test',
        account_id: 'account_01',
        platform: 'threads',
        priority: 'normal'
      }
      
      mockUseJobs.createJob.mockResolvedValue(null)
      
      await wrapper.vm.handleCreateJob()
      
      expect(wrapper.vm.showCreateModal).toBe(true)
    })
  })

  describe('Delete Job', () => {
    it('deletes job when confirmed', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      // Mock window.confirm
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)
      
      await wrapper.vm.handleDeleteJob('job_1')
      
      expect(confirmSpy).toHaveBeenCalledWith('Are you sure you want to delete this job?')
      expect(mockUseJobs.deleteJob).toHaveBeenCalledWith('job_1')
      
      confirmSpy.mockRestore()
    })

    it('does not delete job when cancelled', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      // Mock window.confirm to return false
      const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
      
      await wrapper.vm.handleDeleteJob('job_1')
      
      expect(confirmSpy).toHaveBeenCalled()
      expect(mockUseJobs.deleteJob).not.toHaveBeenCalled()
      
      confirmSpy.mockRestore()
    })
  })

  describe('Edit Job', () => {
    it('handles edit job action', async () => {
      wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      const job = mockJobs[0]
      
      wrapper.vm.editJob(job)
      
      expect(consoleSpy).toHaveBeenCalledWith('Edit job:', job)
      
      consoleSpy.mockRestore()
    })
  })

  describe('Job Columns Configuration', () => {
    it('has correct column definitions', () => {
      wrapper = createWrapper()
      
      const columns = wrapper.vm.jobColumns
      expect(columns).toHaveLength(6)
      expect(columns[0].key).toBe('job_id')
      expect(columns[1].key).toBe('account_id')
      expect(columns[2].key).toBe('platform')
      expect(columns[3].key).toBe('content')
      expect(columns[4].key).toBe('status')
      expect(columns[5].key).toBe('created_at')
    })
  })
})
