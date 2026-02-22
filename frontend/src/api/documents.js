import apiClient from './index'

// 문서 관리 API
const documentsApi = {
  /**
   * 문서 목록 조회
   * @param {Object} params - 조회 파라미터
   */
  list(params = {}) {
    return apiClient.get('/api/admin/v1/documents', { params })
  },

  /**
   * 문서 상세 조회
   * @param {number} docId - 문서 ID
   */
  get(docId) {
    return apiClient.get(`/api/admin/v1/documents/${docId}`)
  },

  /**
   * 문서 저장 (임베딩 없이)
   * @param {Object} data - 문서 데이터
   */
  save(data) {
    const payload = {
      title: data.title,
      doc_type: data.docType,
      content: data.content,
      language: data.language || 'ko',
      metadata: data.metadata || {},
      context_data: data.contextData || null,
      source_type: data.sourceType || 'ui_input',
      source_file: data.sourceFile || null,
      usage_type: data.usageType || 'rag_knowledge'
    }
    if (data.tenantId) payload.tenant_id = data.tenantId
    return apiClient.post('/api/admin/v1/documents', payload)
  },

  /**
   * 문서 수정
   * @param {number} docId - 문서 ID
   * @param {Object} data - 수정할 데이터
   */
  update(docId, data) {
    const updateData = {}
    if (data.title !== undefined) updateData.title = data.title
    if (data.docType !== undefined) updateData.doc_type = data.docType
    if (data.content !== undefined) updateData.content = data.content
    if (data.language !== undefined) updateData.language = data.language
    if (data.metadata !== undefined) updateData.metadata = data.metadata
    if (data.contextData !== undefined) updateData.context_data = data.contextData

    return apiClient.put(`/api/admin/v1/documents/${docId}`, updateData)
  },

  /**
   * 문서 삭제
   * @param {number} docId - 문서 ID
   */
  delete(docId) {
    return apiClient.delete(`/api/admin/v1/documents/${docId}`)
  },

  /**
   * 문서 일괄 삭제
   * @param {number[]} docIds - 문서 ID 목록
   */
  bulkDelete(docIds) {
    return apiClient.post('/api/admin/v1/documents/bulk-delete', {
      doc_ids: docIds
    })
  },

  /**
   * 임베딩 실행
   * @param {Object} params - 임베딩 파라미터
   */
  executeEmbedding(params) {
    const payload = {
      doc_ids: params.doc_ids,
      delete_original: params.delete_original || false
    }
    if (params.chunk_size) payload.chunk_size = params.chunk_size
    if (params.chunk_overlap) payload.chunk_overlap = params.chunk_overlap
    return apiClient.post('/api/admin/v1/documents/embedding/execute', payload)
  },

  /**
   * 파일 업로드 (PDF/DOCX → 텍스트 추출)
   * @param {File} file - 업로드할 파일 객체
   * @param {Function} onProgress - 업로드 진행률 콜백 (optional)
   */
  upload(file, onProgress) {
    const formData = new FormData()
    formData.append('file', file)
    return apiClient.post('/api/admin/v1/documents/upload', formData, {
      headers: { 'Content-Type': undefined },
      ...(onProgress && {
        onUploadProgress: (e) => onProgress(Math.round((e.loaded * 100) / e.total))
      })
    })
  },

  /**
   * 청킹 미리보기
   * @param {Object} params - 미리보기 파라미터
   */
  previewChunks(params) {
    const payload = { content: params.content }
    if (params.chunk_size) payload.chunk_size = params.chunk_size
    if (params.chunk_overlap) payload.chunk_overlap = params.chunk_overlap
    return apiClient.post('/api/admin/v1/documents/embedding/preview', payload)
  }
}

export default documentsApi
