/**
 * 코드 관리 API 클라이언트 (Phase B)
 *
 * LLM 제공자, 모델, 임베딩 모델 등 코드성 데이터 관리
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const codesApi = {
  /**
   * 모든 코드 그룹 목록 조회
   * @returns {Promise<string[]>} 코드 그룹 목록
   */
  async getGroups() {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/admin/v1/codes/groups`)
      return response.data
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
      const response = await axios.get(`${API_BASE_URL}/api/admin/v1/codes/${codeGroup}`, {
        params: { include_inactive: includeInactive }
      })
      return response.data
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
      const response = await axios.get(`${API_BASE_URL}/api/admin/v1/codes/item/${codeId}`)
      return response.data
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
      const response = await axios.post(`${API_BASE_URL}/api/admin/v1/codes`, codeData)
      return response.data
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
      const response = await axios.put(`${API_BASE_URL}/api/admin/v1/codes/${codeId}`, codeData)
      return response.data
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
      await axios.delete(`${API_BASE_URL}/api/admin/v1/codes/${codeId}`)
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
      const response = await axios.post(
        `${API_BASE_URL}/api/admin/v1/codes/${codeGroup}/reorder`,
        { code_ids: codeIds }
      )
      return response.data
    } catch (error) {
      console.error(`코드 순서 변경 실패 (${codeGroup}):`, error)
      throw error
    }
  }
}

export default codesApi
