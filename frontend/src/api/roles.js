/**
 * 역할 관리 API 클라이언트
 *
 * 역할 CRUD + 기본 메뉴 조회
 * 백엔드: app/api/routes/roles.py (prefix: /api/admin/v1/roles)
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/roles'

const rolesApi = {
  /**
   * 역할 목록 조회
   * @returns {Promise<{total, items}>} RoleListResponse
   */
  async list() {
    try {
      return await apiClient.get(BASE_URL)
    } catch (error) {
      console.error('역할 목록 조회 실패:', error)
      throw error
    }
  },

  /**
   * 역할 상세 조회
   * @param {number} roleId - 역할 ID
   * @returns {Promise<Object>} RoleResponse
   */
  async get(roleId) {
    try {
      return await apiClient.get(`${BASE_URL}/${roleId}`)
    } catch (error) {
      console.error(`역할 조회 실패 (ID: ${roleId}):`, error)
      throw error
    }
  },

  /**
   * 역할 생성
   * @param {Object} data - RoleCreate
   * @returns {Promise<Object>} 생성된 역할 정보
   */
  async create(data) {
    try {
      return await apiClient.post(BASE_URL, data)
    } catch (error) {
      console.error('역할 생성 실패:', error)
      throw error
    }
  },

  /**
   * 역할 수정
   * @param {number} roleId - 역할 ID
   * @param {Object} data - RoleUpdate
   * @returns {Promise<Object>} 수정된 역할 정보
   */
  async update(roleId, data) {
    try {
      return await apiClient.put(`${BASE_URL}/${roleId}`, data)
    } catch (error) {
      console.error(`역할 수정 실패 (ID: ${roleId}):`, error)
      throw error
    }
  },

  /**
   * 역할 삭제
   * @param {number} roleId - 역할 ID
   * @returns {Promise<void>}
   */
  async delete(roleId) {
    try {
      await apiClient.delete(`${BASE_URL}/${roleId}`)
    } catch (error) {
      console.error(`역할 삭제 실패 (ID: ${roleId}):`, error)
      throw error
    }
  },

  /**
   * 역할별 기본 메뉴 권한 조회
   * @param {string} roleCode - 역할 코드 (GLOBAL, TENANT, USER)
   * @returns {Promise<Array>} 기본 메뉴 권한 목록
   */
  async getDefaultMenus(roleCode) {
    try {
      return await apiClient.get(`${BASE_URL}/default-menus/${roleCode}`)
    } catch (error) {
      console.error(`기본 메뉴 조회 실패 (Role: ${roleCode}):`, error)
      throw error
    }
  }
}

export default rolesApi
