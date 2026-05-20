/**
 * API Service Unit Tests
 * 测试 api.js 中的方法
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock fetch globally
global.fetch = vi.fn()

// Import after mocking - api is a singleton
import { api } from '../../src/services/api.js'

describe('ApiService - createSpace', () => {
  const mockToken = 'test-token-123'

  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.setItem('hfm_token', mockToken)
  })

  it('should call POST /spaces with correct payload including storage_pool_id', async () => {
    const mockResponse = {
      ok: true,
      json: () => Promise.resolve({
        space_id: 'space-001',
        name: 'Test Space',
        storage_pool_id: 'pool-001'
      })
    }
    fetch.mockResolvedValue(mockResponse)

    const result = await api.createSpace('Test Space', 'pool-001', 'Test description')

    expect(fetch).toHaveBeenCalledWith(
      expect.stringMatching(/\/api\/v1\/spaces$/),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Authorization': `Bearer ${mockToken}`,
          'Content-Type': 'application/json'
        }),
        body: JSON.stringify({
          name: 'Test Space',
          storage_pool_id: 'pool-001',
          description: 'Test description'
        })
      })
    )
    expect(result.space_id).toBe('space-001')
  })

  it('should include max_bytes when provided', async () => {
    const mockResponse = {
      ok: true,
      json: () => Promise.resolve({
        space_id: 'space-002',
        name: 'Test Space 2'
      })
    }
    fetch.mockResolvedValue(mockResponse)

    await api.createSpace('Test Space 2', 'pool-002', 'Description', 1024 * 1024 * 100)

    expect(fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        body: JSON.stringify({
          name: 'Test Space 2',
          storage_pool_id: 'pool-002',
          description: 'Description',
          max_bytes: 104857600
        })
      })
    )
  })

  it('should not include max_bytes when null', async () => {
    const mockResponse = {
      ok: true,
      json: () => Promise.resolve({ space_id: 'space-003' })
    }
    fetch.mockResolvedValue(mockResponse)

    await api.createSpace('Test Space 3', 'pool-003', 'Description', null)

    const callBody = JSON.parse(fetch.mock.calls[0][1].body)
    expect(callBody).not.toHaveProperty('max_bytes')
  })

  it('should throw error when request fails', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Storage pool not found' })
    })

    await expect(api.createSpace('Test', 'invalid-pool', ''))
      .rejects.toThrow('Storage pool not found')
  })
})
