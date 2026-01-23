import searchApi from '@/api/search'
import agentApi from '@/api/agent'

// 채팅 상태 모듈
export default {
  namespaced: true,

  state: () => ({
    messages: [],
    isLoading: false,
    searchMode: 'nl2sql', // 'auto' | 'rag' | 'nl2sql' | 'agent' (기본값: nl2sql)
    error: null,
    sessionId: null, // Agent 멀티턴 대화용 세션 ID
    agentConfig: {
      maxIterations: 10,
      enableMemory: true,
      timeoutSeconds: 60
    },
    // 채팅 히스토리 (하드코딩 샘플 - 향후 API 연동)
    chatHistory: [
      // 일단 주석처리함. 추후 API로 불러올 예정
      // { id: 'sample-1', title: '재택근무 정책 문의', createdAt: new Date('2024-01-15') },
      // { id: 'sample-2', title: '2024년 입사자 현황', createdAt: new Date('2024-01-14') },
      // { id: 'sample-3', title: '연차 신청 방법', createdAt: new Date('2024-01-13') },
      // { id: 'sample-4', title: '부서별 직원 통계', createdAt: new Date('2024-01-12') }
    ],
    activeChatId: null // 현재 선택된 채팅 ID
  }),

  mutations: {
    ADD_MESSAGE(state, message) {
      const newMessage = {
        id: Date.now().toString(),
        timestamp: new Date(),
        ...message
      }
      // 디버깅 로그 (개발 환경에서만)
      if (import.meta.env.DEV) {
        console.log('[ADD_MESSAGE]', newMessage)
        console.log('[Message Content]', newMessage.content)
      }
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
    },
    SET_ACTIVE_CHAT(state, chatId) {
      state.activeChatId = chatId
    },
    CREATE_NEW_CHAT(state) {
      state.messages = []
      state.activeChatId = null
      state.sessionId = null
      state.error = null
    }
  },

  getters: {
    messageCount: (state) => state.messages.length,
    hasError: (state) => state.error !== null,
    lastMessage: (state) => state.messages.length > 0 ? state.messages[state.messages.length - 1] : null,
    getChatHistory: (state) => state.chatHistory,
    getActiveChatId: (state) => state.activeChatId
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

          // 디버깅: Agent 응답 구조 확인 (개발 환경에서만)
          if (import.meta.env.DEV) {
            console.log('[Agent Response]', response)
            console.log('[Agent Answer]', response.answer)
            console.log('[Agent Steps]', response.steps)
          }

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

          // AI 응답 메시지 추가 (통합 SearchResponse 구조)
          commit('ADD_MESSAGE', {
            role: 'assistant',
            content: response.answer,
            queryType: response.query_type,
            // NL2SQL 전용 필드
            sql: response.sql,
            sqlResult: response.sql_result,
            // RAG 전용 필드
            sources: response.sources,
            // 공통 필드
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
    },

    selectChat({ commit }, chatId) {
      commit('SET_ACTIVE_CHAT', chatId)
      // 샘플 채팅이므로 메시지는 초기화 (향후 API에서 로드)
      commit('CLEAR_MESSAGES')
    },

    newChat({ commit }) {
      commit('CREATE_NEW_CHAT')
    }
  }
}
