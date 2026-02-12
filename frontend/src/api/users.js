/**
 * 사용자 관리 API 클라이언트
 *
 * 사용자 CRUD + 역할 할당
 * 백엔드: app/api/routes/users.py (prefix: /api/admin/v1/users)
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/users'

const usersApi = {
  /**
   * 사용자 목록 조회
   * @param {Object} params - 쿼리 파라미터
   * @param {number} [params.limit=20] - 최대 결과 수
   * @param {number} [params.offset=0] - 시작 위치
   * @param {number} [params.tenant_id] - 테넌트 필터
   * @param {boolean} [params.is_active] - 활성화 필터
   * @returns {Promise<{total, items, limit, offset}>}
   */
  async list(params = {}) {
    try {
      return await apiClient.get(BASE_URL, { params })
    } catch (error) {
      console.error('사용자 목록 조회 실패:', error)
      throw error
    }
  },

  /**
   * 사용자 상세 조회
   * @param {number} userId - 사용자 ID
   * @returns {Promise<Object>} UserResponse
   */
  async get(userId) {
    try {
      return await apiClient.get(`${BASE_URL}/${userId}`)
    } catch (error) {
      console.error(`사용자 조회 실패 (ID: ${userId}):`, error)
      throw error
    }
  },

  /**
   * 사용자 생성
   * @param {Object} data - UserCreate
   * @returns {Promise<Object>} 생성된 사용자 정보
   */
  async create(data) {
    try {
      return await apiClient.post(BASE_URL, data)
    } catch (error) {
      console.error('사용자 생성 실패:', error)
      throw error
    }
  },

  /**
   * 사용자 수정
   * @param {number} userId - 사용자 ID
   * @param {Object} data - UserUpdate
   * @returns {Promise<Object>} 수정된 사용자 정보
   */
  async update(userId, data) {
    try {
      return await apiClient.put(`${BASE_URL}/${userId}`, data)
    } catch (error) {
      console.error(`사용자 수정 실패 (ID: ${userId}):`, error)
      throw error
    }
  },

  /**
   * 사용자 삭제
   * @param {number} userId - 사용자 ID
   * @returns {Promise<void>}
   */
  async delete(userId) {
    try {
      await apiClient.delete(`${BASE_URL}/${userId}`)
    } catch (error) {
      console.error(`사용자 삭제 실패 (ID: ${userId}):`, error)
      throw error
    }
  },

  /**
   * 사용자 역할 할당
   * @param {number} userId - 사용자 ID
   * @param {number[]} roleIds - 역할 ID 목록
   * @returns {Promise<Object>}
   */
  async assignRoles(userId, roleIds) {
    try {
      return await apiClient.put(`${BASE_URL}/${userId}/roles`, { role_ids: roleIds })
    } catch (error) {
      console.error(`역할 할당 실패 (User: ${userId}):`, error)
      throw error
    }
  },

  /**
   * 역할 목록 조회 (사용자 생성/수정 시 역할 선택용)
   * @returns {Promise<{total, items}>}
   */
  async listRoles() {
    try {
      return await apiClient.get('/api/admin/v1/roles')
    } catch (error) {
      console.error('역할 목록 조회 실패:', error)
      throw error
    }
  }
}

export default usersApi
