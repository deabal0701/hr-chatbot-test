/**
 * 테넌트 관리 API 클라이언트
 *
 * 테넌트 CRUD
 * 백엔드: app/api/routes/tenants.py (prefix: /api/admin/v1/tenants)
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/tenants'

const tenantsApi = {
  async list() {
    try {
      return await apiClient.get(BASE_URL)
    } catch (error) {
      console.error('테넌트 목록 조회 실패:', error)
      throw error
    }
  },

  async get(tenantId) {
    try {
      return await apiClient.get(`${BASE_URL}/${tenantId}`)
    } catch (error) {
      console.error(`테넌트 조회 실패 (ID: ${tenantId}):`, error)
      throw error
    }
  },

  async create(data) {
    try {
      return await apiClient.post(BASE_URL, data)
    } catch (error) {
      console.error('테넌트 생성 실패:', error)
      throw error
    }
  },

  async update(tenantId, data) {
    try {
      return await apiClient.put(`${BASE_URL}/${tenantId}`, data)
    } catch (error) {
      console.error(`테넌트 수정 실패 (ID: ${tenantId}):`, error)
      throw error
    }
  },

  async delete(tenantId) {
    try {
      await apiClient.delete(`${BASE_URL}/${tenantId}`)
    } catch (error) {
      console.error(`테넌트 삭제 실패 (ID: ${tenantId}):`, error)
      throw error
    }
  }
}

export default tenantsApi
