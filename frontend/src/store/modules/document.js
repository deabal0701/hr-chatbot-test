import documentApi from '@/api/documents'

// 문서 관리 상태 모듈
export default {
  namespaced: true,

  state: () => ({
    documents: [],
    currentDocument: null,
    selectedIds: [],
    isLoading: false,
    isSaving: false,
    filters: {
      docType: null,
      sourceType: null,
      indexed: null
    },
    pagination: {
      page: 1,
      limit: 20,
      total: 0
    },
    error: null
  }),

  mutations: {
    SET_DOCUMENTS(state, { documents, total }) {
      state.documents = documents
      state.pagination.total = total
    },
    SET_CURRENT_DOCUMENT(state, document) {
      state.currentDocument = document
    },
    SET_LOADING(state, loading) {
      state.isLoading = loading
    },
    SET_SAVING(state, saving) {
      state.isSaving = saving
    },
    SET_FILTERS(state, filters) {
      state.filters = { ...state.filters, ...filters }
    },
    RESET_FILTERS(state) {
      state.filters = {
        docType: null,
        sourceType: null,
        indexed: null
      }
    },
    SET_SELECTED(state, ids) {
      state.selectedIds = ids
    },
    TOGGLE_SELECTED(state, id) {
      const index = state.selectedIds.indexOf(id)
      if (index === -1) {
        state.selectedIds.push(id)
      } else {
        state.selectedIds.splice(index, 1)
      }
    },
    CLEAR_SELECTED(state) {
      state.selectedIds = []
    },
    SET_PAGE(state, page) {
      state.pagination.page = page
    },
    SET_PAGE_SIZE(state, size) {
      state.pagination.limit = size
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    CLEAR_ERROR(state) {
      state.error = null
    }
  },

  getters: {
    selectedCount: (state) => state.selectedIds.length,
    hasSelected: (state) => state.selectedIds.length > 0,
    totalPages: (state) => Math.ceil(state.pagination.total / state.pagination.limit),
    pendingDocuments: (state) => state.documents.filter(doc => !doc.indexed),
    pendingCount: (state) => state.documents.filter(doc => !doc.indexed).length
  },

  actions: {
    // 문서 목록 조회
    async fetchDocuments({ commit, state }) {
      commit('SET_LOADING', true)
      commit('CLEAR_ERROR')

      try {
        const params = {
          limit: state.pagination.limit,
          offset: (state.pagination.page - 1) * state.pagination.limit
        }

        // 필터 적용
        if (state.filters.docType) {
          params.doc_type = state.filters.docType
        }
        if (state.filters.sourceType) {
          params.source_type = state.filters.sourceType
        }
        if (state.filters.indexed !== null) {
          params.indexed = state.filters.indexed
        }

        const response = await documentApi.list(params)

        commit('SET_DOCUMENTS', {
          documents: response.documents,
          total: response.total
        })
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '문서 목록 조회 실패'
        commit('SET_ERROR', errorMessage)
      } finally {
        commit('SET_LOADING', false)
      }
    },

    // 문서 상세 조회
    async fetchDocument({ commit }, docId) {
      commit('SET_LOADING', true)
      commit('CLEAR_ERROR')

      try {
        const response = await documentApi.get(docId)
        commit('SET_CURRENT_DOCUMENT', response)
        return response
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '문서 조회 실패'
        commit('SET_ERROR', errorMessage)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    // 문서 저장 (생성)
    async saveDocument({ commit, dispatch }, documentData) {
      commit('SET_SAVING', true)
      commit('CLEAR_ERROR')

      try {
        const response = await documentApi.save(documentData)
        await dispatch('fetchDocuments')
        return response
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '문서 저장 실패'
        commit('SET_ERROR', errorMessage)
        throw error
      } finally {
        commit('SET_SAVING', false)
      }
    },

    // 문서 수정
    async updateDocument({ commit, dispatch }, { docId, documentData }) {
      commit('SET_SAVING', true)
      commit('CLEAR_ERROR')

      try {
        const response = await documentApi.update(docId, documentData)
        await dispatch('fetchDocuments')
        return response
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '문서 수정 실패'
        commit('SET_ERROR', errorMessage)
        throw error
      } finally {
        commit('SET_SAVING', false)
      }
    },

    // 문서 삭제
    async deleteDocument({ commit, dispatch }, docId) {
      commit('SET_LOADING', true)
      commit('CLEAR_ERROR')

      try {
        await documentApi.delete(docId)
        await dispatch('fetchDocuments')
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '문서 삭제 실패'
        commit('SET_ERROR', errorMessage)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    // 선택된 문서 일괄 삭제
    async deleteSelected({ commit, state, dispatch }) {
      if (state.selectedIds.length === 0) return

      commit('SET_LOADING', true)
      commit('CLEAR_ERROR')

      try {
        await documentApi.bulkDelete(state.selectedIds)
        commit('CLEAR_SELECTED')
        await dispatch('fetchDocuments')
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '일괄 삭제 실패'
        commit('SET_ERROR', errorMessage)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    // 임베딩 실행
    async executeEmbedding({ commit, dispatch }, { docIds, chunkSize = 1000, chunkOverlap = 100 }) {
      commit('SET_LOADING', true)
      commit('CLEAR_ERROR')

      try {
        const response = await documentApi.executeEmbedding({
          doc_ids: docIds,
          chunk_size: chunkSize,
          chunk_overlap: chunkOverlap
        })
        await dispatch('fetchDocuments')
        return response
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '임베딩 실행 실패'
        commit('SET_ERROR', errorMessage)
        throw error
      } finally {
        commit('SET_LOADING', false)
      }
    },

    // 청킹 미리보기
    async previewChunks({ commit }, { content, chunkSize = 1000, chunkOverlap = 100 }) {
      try {
        const response = await documentApi.previewChunks({
          content,
          chunk_size: chunkSize,
          chunk_overlap: chunkOverlap
        })
        return response
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '청킹 미리보기 실패'
        commit('SET_ERROR', errorMessage)
        throw error
      }
    },

    // 필터 설정
    setFilters({ commit, dispatch }, filters) {
      commit('SET_FILTERS', filters)
      commit('SET_PAGE', 1)
      dispatch('fetchDocuments')
    },

    // 필터 초기화
    resetFilters({ commit, dispatch }) {
      commit('RESET_FILTERS')
      commit('SET_PAGE', 1)
      dispatch('fetchDocuments')
    },

    // 페이지 변경
    setPage({ commit, dispatch }, page) {
      commit('SET_PAGE', page)
      dispatch('fetchDocuments')
    },

    // 페이지 사이즈 변경
    setPageSize({ commit, dispatch }, size) {
      commit('SET_PAGE_SIZE', size)
      commit('SET_PAGE', 1)  // 페이지 사이즈 변경 시 1페이지로 이동
      dispatch('fetchDocuments')
    },

    // 선택 토글
    toggleSelection({ commit }, id) {
      commit('TOGGLE_SELECTED', id)
    },

    // 전체 선택/해제
    selectAll({ commit, state }) {
      if (state.selectedIds.length === state.documents.length) {
        commit('CLEAR_SELECTED')
      } else {
        commit('SET_SELECTED', state.documents.map(doc => doc.id))
      }
    },

    // 선택 초기화
    clearSelection({ commit }) {
      commit('CLEAR_SELECTED')
    }
  }
}
