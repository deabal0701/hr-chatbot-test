/**
 * 부서 관리 API 클라이언트
 *
 * 부서 트리 CRUD + 순서 변경
 * 백엔드: app/api/routes/departments.py (prefix: /api/admin/v1/departments)
 *
 * 에러 처리: axios 인터셉터(index.js)에서 일괄 처리
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/departments'

const departmentsApi = {
  /** 부서 트리 조회 (params: { tenant_id? }) */
  getTree: (params = {}) => apiClient.get(BASE_URL, { params }),

  /** 부서 상세 조회 */
  get: (deptId) => apiClient.get(`${BASE_URL}/${deptId}`),

  /** 부서 생성 */
  create: (data) => apiClient.post(BASE_URL, data),

  /** 부서 수정 */
  update: (deptId, data) => apiClient.put(`${BASE_URL}/${deptId}`, data),

  /** 부서 삭제 */
  delete: (deptId) => apiClient.delete(`${BASE_URL}/${deptId}`),

  /** 부서 순서 일괄 변경 (드래그앤드롭용) */
  reorder: (items) => apiClient.put(`${BASE_URL}/reorder`, { items }),
}

export default departmentsApi
