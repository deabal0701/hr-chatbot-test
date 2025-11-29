import searchApi from '@/api/search'

// 채팅 상태 모듈
export default {
  namespaced: true,

  state: () => ({
    messages: [],
    isLoading: false,
    searchMode: 'auto', // 'auto' | 'rag' | 'nl2sql'
    error: null
  }),

  mutations: {
    ADD_MESSAGE(state, message) {
      state.messages.push({
        id: Date.now().toString(),
        timestamp: new Date(),
        ...message
      })
    },
    UPDATE_LAST_MESSAGE(state, updates) {
      if (state.messages.length > 0) {
        const lastIndex = state.messages.length - 1
        state.messages[lastIndex] = {
          ...state.messages[lastIndex],
          ...updates
        }
      }
    },
    SET_LOADING(state, loading) {
      state.isLoading = loading
    },
    SET_MODE(state, mode) {
      state.searchMode = mode
    },
    SET_ERROR(state, error) {
      state.error = error
    },
    CLEAR_MESSAGES(state) {
      state.messages = []
    },
    CLEAR_ERROR(state) {
      state.error = null
    }
  },

  getters: {
    messageCount: (state) => state.messages.length,
    hasError: (state) => state.error !== null,
    lastMessage: (state) => state.messages.length > 0 ? state.messages[state.messages.length - 1] : null
  },

  actions: {
    async sendMessage({ commit, state }, query) {
      commit('SET_LOADING', true)
      commit('CLEAR_ERROR')

      // 사용자 메시지 추가
      commit('ADD_MESSAGE', {
        role: 'user',
        content: query
      })

      try {
        const response = await searchApi.search({
          query,
          mode: state.searchMode
        })

        // AI 응답 메시지 추가
        commit('ADD_MESSAGE', {
          role: 'assistant',
          content: response.answer,
          queryType: response.query_type,
          ragResult: response.rag_result,
          nl2sqlResult: response.nl2sql_result,
          responseTimeMs: response.response_time_ms,
          metadata: response.metadata
        })
      } catch (error) {
        const errorMessage = error.response?.data?.detail || error.message || '검색 중 오류가 발생했습니다.'
        commit('SET_ERROR', errorMessage)

        // 에러 메시지도 대화에 추가
        commit('ADD_MESSAGE', {
          role: 'assistant',
          content: `죄송합니다. 오류가 발생했습니다: ${errorMessage}`,
          isError: true
        })
      } finally {
        commit('SET_LOADING', false)
      }
    },

    setMode({ commit }, mode) {
      commit('SET_MODE', mode)
    },

    clearChat({ commit }) {
      commit('CLEAR_MESSAGES')
      commit('CLEAR_ERROR')
    }
  }
}
