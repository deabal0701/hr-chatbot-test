/**
 * 테넌트 관리 API 클라이언트
 *
 * 테넌트 CRUD
 * 백엔드: app/api/routes/tenants.py (prefix: /api/admin/v1/tenants)
 *
 * 에러 처리: axios 인터셉터(index.js)에서 일괄 처리
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/tenants'

const tenantsApi = {
  /** 테넌트 목록 조회 */
  list: () => apiClient.get(BASE_URL),

  /** 테넌트 상세 조회 */
  get: (tenantId) => apiClient.get(`${BASE_URL}/${tenantId}`),

  /** 테넌트 생성 */
  create: (data) => apiClient.post(BASE_URL, data),

  /** 테넌트 수정 */
  update: (tenantId, data) => apiClient.put(`${BASE_URL}/${tenantId}`, data),

  /** 테넌트 삭제 */
  delete: (tenantId) => apiClient.delete(`${BASE_URL}/${tenantId}`),
}

export default tenantsApi
