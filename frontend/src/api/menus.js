/**
 * 메뉴 관리 API 클라이언트
 *
 * 메뉴 트리 CRUD
 * 백엔드: app/api/routes/menus.py (prefix: /api/admin/v1/menus)
 *
 * 에러 처리: axios 인터셉터(index.js)에서 일괄 처리
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/menus'

const menusApi = {
  /** 메뉴 트리 조회 */
  getTree: () => apiClient.get(BASE_URL),

  /** 메뉴 상세 조회 */
  get: (menuId) => apiClient.get(`${BASE_URL}/${menuId}`),

  /** 메뉴 생성 */
  create: (data) => apiClient.post(BASE_URL, data),

  /** 메뉴 수정 */
  update: (menuId, data) => apiClient.put(`${BASE_URL}/${menuId}`, data),

  /** 메뉴 삭제 */
  delete: (menuId) => apiClient.delete(`${BASE_URL}/${menuId}`),

  /** 메뉴 순서 일괄 변경 (드래그앤드롭용) */
  reorder: (items) => apiClient.put(`${BASE_URL}/reorder`, { items }),
}

export default menusApi
