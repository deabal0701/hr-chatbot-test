/**
 * 메뉴 관리 API 클라이언트
 *
 * 메뉴 트리 CRUD
 * 백엔드: app/api/routes/menus.py (prefix: /api/admin/v1/menus)
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/menus'

const menusApi = {
  /**
   * 메뉴 트리 조회
   * @returns {Promise<{items: Array}>} MenuTreeResponse
   */
  async getTree() {
    try {
      return await apiClient.get(BASE_URL)
    } catch (error) {
      console.error('메뉴 트리 조회 실패:', error)
      throw error
    }
  },

  /**
   * 메뉴 상세 조회
   * @param {number} menuId - 메뉴 ID
   * @returns {Promise<Object>} MenuResponse
   */
  async get(menuId) {
    try {
      return await apiClient.get(`${BASE_URL}/${menuId}`)
    } catch (error) {
      console.error(`메뉴 조회 실패 (ID: ${menuId}):`, error)
      throw error
    }
  },

  /**
   * 메뉴 생성
   * @param {Object} data - MenuCreate
   * @returns {Promise<Object>} 생성된 메뉴 정보
   */
  async create(data) {
    try {
      return await apiClient.post(BASE_URL, data)
    } catch (error) {
      console.error('메뉴 생성 실패:', error)
      throw error
    }
  },

  /**
   * 메뉴 수정
   * @param {number} menuId - 메뉴 ID
   * @param {Object} data - MenuUpdate
   * @returns {Promise<Object>} 수정된 메뉴 정보
   */
  async update(menuId, data) {
    try {
      return await apiClient.put(`${BASE_URL}/${menuId}`, data)
    } catch (error) {
      console.error(`메뉴 수정 실패 (ID: ${menuId}):`, error)
      throw error
    }
  },

  /**
   * 메뉴 삭제
   * @param {number} menuId - 메뉴 ID
   * @returns {Promise<void>}
   */
  async delete(menuId) {
    try {
      await apiClient.delete(`${BASE_URL}/${menuId}`)
    } catch (error) {
      console.error(`메뉴 삭제 실패 (ID: ${menuId}):`, error)
      throw error
    }
  },

  /**
   * 메뉴 순서 일괄 변경 (드래그앤드롭용)
   * @param {Array} items - [{ menu_id, sort_order }]
   * @returns {Promise<Object>}
   */
  async reorder(items) {
    try {
      return await apiClient.put(`${BASE_URL}/reorder`, { items })
    } catch (error) {
      console.error('메뉴 순서 변경 실패:', error)
      throw error
    }
  }
}

export default menusApi
