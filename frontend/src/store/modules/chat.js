import searchApi from '@/api/search'
import agentApi from '@/api/agent'

// 채팅 상태 모듈
export default {
  namespaced: true,

  state: () => ({
    messages: [],
    isLoading: false,
    searchMode: 'auto', // 'auto' | 'rag' | 'nl2sql' | 'agent'
    error: null,
    sessionId: null, // Agent 멀티턴 대화용 세션 ID
    agentConfig: {
      maxIterations: 10,
      enableMemory: true,
      timeoutSeconds: 60
    }
  }),

  mutations: {
    ADD_MESSAGE(state, message) {
      const newMessage = {
        id: Date.now().toString(),
        timestamp: new Date(),
        ...message
      }
      console.log('[ADD_MESSAGE]', newMessage)
      console.log('[Message Content]', newMessage.content)
      state.messages.push(newMessage)
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
    },
    SET_SESSION_ID(state, sessionId) {
      state.sessionId = sessionId
    },
    SET_AGENT_CONFIG(state, config) {
      state.agentConfig = { ...state.agentConfig, ...config }
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
        let response

        // Agent 모드인 경우
        if (state.searchMode === 'agent') {
          // 세션 ID 생성 (첫 메시지) 또는 재사용
          if (!state.sessionId) {
            const sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
            commit('SET_SESSION_ID', sessionId)
          }

          response = await agentApi.agentSearch({
            question: query,
            sessionId: state.sessionId,
            config: state.agentConfig
          })

          // 디버깅: Agent 응답 구조 확인
          console.log('[Agent Response]', response)
          console.log('[Agent Answer]', response.answer)
          console.log('[Agent Steps]', response.steps)

          // Agent 응답 메시지 추가
          commit('ADD_MESSAGE', {
            role: 'assistant',
            content: response.answer || '답변을 생성하지 못했습니다.',
            queryType: 'agent',
            agentResult: {
              steps: response.steps || [],
              totalIterations: response.total_iterations || 0,
              toolsUsed: response.tools_used || [],
              success: response.success,
              sessionId: response.session_id
            },
            metadata: response.metadata || {}
          })
        } else {
          // 기존 모드 (auto/rag/nl2sql)
          response = await searchApi.search({
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
        }
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

    setMode({ commit, state }, mode) {
      commit('SET_MODE', mode)

      // 모드 변경 시 세션 ID 초기화 (Agent 모드가 아닌 경우)
      if (mode !== 'agent' && state.sessionId) {
        commit('SET_SESSION_ID', null)
      }
    },

    setAgentConfig({ commit }, config) {
      commit('SET_AGENT_CONFIG', config)
    },

    clearChat({ commit }) {
      commit('CLEAR_MESSAGES')
      commit('CLEAR_ERROR')
      commit('SET_SESSION_ID', null)
    }
  }
}
