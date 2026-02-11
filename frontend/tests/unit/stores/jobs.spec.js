import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useJobsStore } from '@/stores/jobs'
import { jobsApi } from '@/api/jobs'

// Mock API
vi.mock('@/api/jobs', () => ({
  jobsApi: {
    getAll: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn()
  }
}))

describe('Jobs Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('initializes with empty state', () => {
    const store = useJobsStore()
    expect(store.jobs).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBe(null)
  })

  it('fetches jobs successfully', async () => {
    const mockJobs = [
      { job_id: '1', account_id: 'account_01', status: 'pending' },
      { job_id: '2', account_id: 'account_01', status: 'completed' }
    ]

    jobsApi.getAll.mockResolvedValue({
      success: true,
      data: mockJobs
    })

    const store = useJobsStore()
    await store.fetchJobs()

    expect(store.jobs).toEqual(mockJobs)
    expect(store.loading).toBe(false)
    expect(store.error).toBe(null)
  })

  it('handles fetch error', async () => {
    jobsApi.getAll.mockRejectedValue(new Error('Network error'))

    const store = useJobsStore()
    await store.fetchJobs()

    expect(store.error).toBeTruthy()
    expect(store.loading).toBe(false)
  })

  it('filters jobs by account', () => {
    const store = useJobsStore()
    store.jobs = [
      { job_id: '1', account_id: 'account_01' },
      { job_id: '2', account_id: 'account_02' },
      { job_id: '3', account_id: 'account_01' }
    ]

    store.setFilters({ accountId: 'account_01' })

    expect(store.filteredJobs).toHaveLength(2)
    expect(store.filteredJobs.every(j => j.account_id === 'account_01')).toBe(true)
  })

  it('creates job successfully', async () => {
    const newJob = {
      content: 'Test content',
      account_id: 'account_01',
      platform: 'threads'
    }

    jobsApi.create.mockResolvedValue({
      success: true,
      data: { job_id: 'new_job_1' }
    })

    jobsApi.getAll.mockResolvedValue({
      success: true,
      data: []
    })

    const store = useJobsStore()
    const result = await store.createJob(newJob)

    expect(result).toBeTruthy()
    expect(jobsApi.create).toHaveBeenCalledWith(newJob)
  })

  it('deletes job successfully', async () => {
    const store = useJobsStore()
    store.jobs = [
      { job_id: '1', account_id: 'account_01' },
      { job_id: '2', account_id: 'account_01' }
    ]

    jobsApi.delete.mockResolvedValue({
      success: true
    })

    await store.deleteJob('1')

    expect(store.jobs).toHaveLength(1)
    expect(store.jobs[0].job_id).toBe('2')
  })
})
