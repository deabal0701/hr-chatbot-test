/**
 * 사용자 관리 API 클라이언트 (v2.0 메뉴 기반)
 *
 * 사용자 CRUD + 메뉴 권한 할당
 * 백엔드: app/api/routes/users.py (prefix: /api/admin/v1/users)
 *
 * 에러 처리: axios 인터셉터(index.js)에서 일괄 처리
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/users'

const usersApi = {
  /** 사용자 목록 조회 */
  list: (params = {}) => apiClient.get(BASE_URL, { params }),

  /** 사용자 상세 조회 */
  get: (userId) => apiClient.get(`${BASE_URL}/${userId}`),

  /** 사용자 생성 */
  create: (data) => apiClient.post(BASE_URL, data),

  /** 사용자 수정 */
  update: (userId, data) => apiClient.put(`${BASE_URL}/${userId}`, data),

  /** 사용자 삭제 */
  delete: (userId) => apiClient.delete(`${BASE_URL}/${userId}`),

  /** 사용자 메뉴 권한 조회 */
  getUserMenus: (userId) => apiClient.get(`${BASE_URL}/${userId}/menus`),

  /** 사용자 메뉴 권한 할당 (replace 방식) */
  assignMenus: (userId, menus) => apiClient.put(`${BASE_URL}/${userId}/menus`, { menus }),

  /** 역할 목록 조회 (사용자 생성/수정 시 역할 선택용) */
  listRoles: () => apiClient.get('/api/admin/v1/roles'),

  /** 역할 선택 옵션 (USER_MGMT 권한으로 접근 가능) */
  getRoleOptions: () => apiClient.get(`${BASE_URL}/options/roles`),

  /** 테넌트 선택 옵션 (USER_MGMT 권한으로 접근 가능) */
  getTenantOptions: () => apiClient.get(`${BASE_URL}/options/tenants`),

  /** 메뉴 선택 옵션 (사용자 메뉴 권한 할당용, USER_MGMT 권한으로 접근) */
  getMenuOptions: () => apiClient.get(`${BASE_URL}/options/menus`),

  /** 부서 선택 옵션 (사용자 생성/수정 시 부서 선택용, tenant_id 기반) */
  getDeptOptions: (tenantId) => apiClient.get(`${BASE_URL}/options/departments`, {
    params: tenantId ? { tenant_id: tenantId } : {}
  }),
}

export default usersApi
