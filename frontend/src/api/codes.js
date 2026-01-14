/**
 * 코드 관리 API 클라이언트 (Phase B)
 *
 * LLM 제공자, 모델, 임베딩 모델 등 코드성 데이터 관리
 */
import apiClient from './index'

const BASE_URL = '/api/admin/v1/codes'

const codesApi = {
  /**
   * 모든 코드 그룹 목록 조회
   * @returns {Promise<string[]>} 코드 그룹 목록
   */
  async getGroups() {
    try {
      return await apiClient.get(`${BASE_URL}/groups`)
    } catch (error) {
      console.error('코드 그룹 조회 실패:', error)
      throw error
    }
  },

  /**
   * 특정 그룹의 코드 목록 조회
   * @param {string} codeGroup - 코드 그룹명
   * @param {boolean} includeInactive - 비활성 코드 포함 여부
   * @returns {Promise<Object>} 코드 그룹 응답 (code_group, codes, total_count)
   */
  async getByGroup(codeGroup, includeInactive = false) {
    try {
      return await apiClient.get(`${BASE_URL}/${codeGroup}`, {
        params: { include_inactive: includeInactive }
      })
    } catch (error) {
      console.error(`코드 조회 실패 (${codeGroup}):`, error)
      throw error
    }
  },

  /**
   * 코드 단건 조회
   * @param {number} codeId - 코드 ID
   * @returns {Promise<Object>} 코드 정보
   */
  async getById(codeId) {
    try {
      return await apiClient.get(`${BASE_URL}/item/${codeId}`)
    } catch (error) {
      console.error(`코드 조회 실패 (ID: ${codeId}):`, error)
      throw error
    }
  },

  /**
   * 코드 생성
   * @param {Object} codeData - 코드 생성 데이터
   * @param {string} codeData.code_group - 코드 그룹명
   * @param {string} codeData.code_value - 코드 값
   * @param {string} codeData.code_name - 표시명
   * @param {string} [codeData.description] - 설명
   * @param {Object} [codeData.metadata] - 메타데이터
   * @param {number} [codeData.sort_order] - 정렬 순서
   * @param {boolean} [codeData.is_active] - 활성화 여부
   * @returns {Promise<Object>} 생성된 코드 정보
   */
  async create(codeData) {
    try {
      return await apiClient.post(BASE_URL, codeData)
    } catch (error) {
      console.error('코드 생성 실패:', error)
      throw error
    }
  },

  /**
   * 코드 수정
   * @param {number} codeId - 코드 ID
   * @param {Object} codeData - 수정할 데이터
   * @param {string} [codeData.code_name] - 표시명
   * @param {string} [codeData.description] - 설명
   * @param {Object} [codeData.metadata] - 메타데이터
   * @param {number} [codeData.sort_order] - 정렬 순서
   * @param {boolean} [codeData.is_active] - 활성화 여부
   * @returns {Promise<Object>} 수정된 코드 정보
   */
  async update(codeId, codeData) {
    try {
      return await apiClient.put(`${BASE_URL}/${codeId}`, codeData)
    } catch (error) {
      console.error(`코드 수정 실패 (ID: ${codeId}):`, error)
      throw error
    }
  },

  /**
   * 코드 삭제 (시스템 코드는 삭제 불가)
   * @param {number} codeId - 코드 ID
   * @returns {Promise<void>}
   */
  async delete(codeId) {
    try {
      await apiClient.delete(`${BASE_URL}/${codeId}`)
    } catch (error) {
      console.error(`코드 삭제 실패 (ID: ${codeId}):`, error)
      throw error
    }
  },

  /**
   * 코드 순서 변경
   * @param {string} codeGroup - 코드 그룹명
   * @param {number[]} codeIds - 코드 ID 목록 (순서대로)
   * @returns {Promise<Object>} 성공 메시지
   */
  async reorder(codeGroup, codeIds) {
    try {
      return await apiClient.post(`${BASE_URL}/${codeGroup}/reorder`, { code_ids: codeIds })
    } catch (error) {
      console.error(`코드 순서 변경 실패 (${codeGroup}):`, error)
      throw error
    }
  }
}

export default codesApi
