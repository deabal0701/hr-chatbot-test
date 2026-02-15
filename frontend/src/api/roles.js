/**
 * 역할 관리 API 클라이언트
 *
 * 역할 CRUD + 기본 메뉴 조회
 * 백엔드: app/api/routes/roles.py (prefix: /api/admin/v1/roles)
 *
 * 에러 처리: axios 인터셉터(index.js)에서 일괄 처리
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/roles'

const rolesApi = {
  /** 역할 목록 조회 */
  list: () => apiClient.get(BASE_URL),

  /** 역할 상세 조회 */
  get: (roleId) => apiClient.get(`${BASE_URL}/${roleId}`),

  /** 역할 생성 */
  create: (data) => apiClient.post(BASE_URL, data),

  /** 역할 수정 */
  update: (roleId, data) => apiClient.put(`${BASE_URL}/${roleId}`, data),

  /** 역할 삭제 */
  delete: (roleId) => apiClient.delete(`${BASE_URL}/${roleId}`),

  /** 역할별 기본 메뉴 권한 조회 */
  getDefaultMenus: (roleCode) => apiClient.get(`${BASE_URL}/default-menus/${roleCode}`),
}

export default rolesApi
