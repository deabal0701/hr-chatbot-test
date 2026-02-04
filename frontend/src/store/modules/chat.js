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
    sessionId: null, // Agent 멀티턴 대화용 세션 ID (서버에서 생성)
    // 채팅 히스토리 (하드코딩 샘플 - 향후 API 연동)
    chatHistory: [],
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
          // 첫 요청: sessionId null → 서버가 생성
          // 멀티턴: 서버 응답에서 받은 sessionId 재사용
          response = await agentApi.agentSearch({
            question: query,
            sessionId: state.sessionId  // 첫 요청 시 null, 이후 서버 응답값 사용
          })

          // 서버가 생성한 session_id 저장 (멀티턴 대화용)
          if (response.session_id && response.session_id !== state.sessionId) {
            commit('SET_SESSION_ID', response.session_id)
          }

          if (import.meta.env.DEV) {
            console.log('[Agent Response]', response)
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
          // nl2sql 모드에서도 멀티턴 대화 지원을 위해 sessionId 전달
          response = await searchApi.search({
            query,
            mode: state.searchMode,
            sessionId: state.sessionId  // 멀티턴 대화용 (첫 요청 시 null)
          })

          // 서버가 생성한 session_id 저장 (멀티턴 대화용)
          if (response.session_id && response.session_id !== state.sessionId) {
            commit('SET_SESSION_ID', response.session_id)
          }

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
            metadata: response.metadata,
            sessionId: response.session_id  // 세션 ID 저장
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
      const previousMode = state.searchMode
      commit('SET_MODE', mode)

      // 모드 변경 시 세션 ID 초기화 (다른 모드로 전환 시)
      if (previousMode !== mode && state.sessionId) {
        commit('SET_SESSION_ID', null)
      }
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
