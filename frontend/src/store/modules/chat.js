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
    activeChatId: null, // 현재 선택된 채팅 ID
    // SSE 스트리밍 상태
    isStreaming: false,
    streamProgress: [],
    streamController: null
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
    },
    // SSE 스트리밍 mutations
    SET_STREAMING(state, streaming) {
      state.isStreaming = streaming
    },
    ADD_STREAM_PROGRESS(state, progress) {
      state.streamProgress.push(progress)
    },
    CLEAR_STREAM_PROGRESS(state) {
      state.streamProgress = []
    },
    SET_STREAM_CONTROLLER(state, controller) {
      state.streamController = controller
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
    async sendMessage({ commit, state, dispatch }, query) {
      // Agent와 NL2SQL 모드는 SSE 스트리밍 사용
      if (state.searchMode === 'agent' || state.searchMode === 'nl2sql') {
        return dispatch('sendMessageStream', query)
      }

      // RAG 모드: 기존 방식 유지
      commit('SET_LOADING', true)
      commit('CLEAR_ERROR')

      // 사용자 메시지 추가
      commit('ADD_MESSAGE', {
        role: 'user',
        content: query
      })

      try {
        let response

        // 기존 모드 (auto/rag)
        // apiClient 인터셉터가 success_response에서 data 자동 추출
        response = await searchApi.search({
          query,
          mode: state.searchMode,
          sessionId: state.sessionId
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
          // RAG 전용 필드
          sources: response.sources,
          // 공통 필드
          responseTimeMs: response.response_time_ms,
          metadata: response.metadata,
          sessionId: response.session_id
        })
      } catch (error) {
        // 새 에러 형식: error.code, error.message 사용
        const errorCode = error.code || 'UNKNOWN_ERROR'
        const errorMessage = error.message || '검색 중 오류가 발생했습니다.'

        commit('SET_ERROR', { code: errorCode, message: errorMessage })

        // 에러 메시지도 대화에 추가
        commit('ADD_MESSAGE', {
          role: 'assistant',
          content: `죄송합니다. ${errorMessage}`,
          isError: true,
          errorCode: errorCode
        })
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async sendMessageStream({ commit, state }, query) {
      commit('SET_LOADING', true)
      commit('SET_STREAMING', true)
      commit('CLEAR_STREAM_PROGRESS')
      commit('CLEAR_ERROR')

      // 사용자 메시지 추가
      commit('ADD_MESSAGE', {
        role: 'user',
        content: query
      })

      // 빈 assistant 메시지를 먼저 추가 (스트리밍 진행 표시용)
      commit('ADD_MESSAGE', {
        role: 'assistant',
        content: '',
        isStreaming: true,
        streamProgress: [],
        currentStep: null,
        queryType: state.searchMode
      })

      const callbacks = {
        onNodeStart: (event) => {
          // 현재 진행 중인 노드의 "~중..." 레이블 업데이트
          commit('UPDATE_LAST_MESSAGE', {
            currentStep: event.message
          })
        },
        onNodeComplete: (event) => {
          commit('ADD_STREAM_PROGRESS', event)
          // 마지막 assistant 메시지의 streamProgress 업데이트 + currentStep 초기화
          const lastMsg = state.messages[state.messages.length - 1]
          if (lastMsg && lastMsg.role === 'assistant') {
            commit('UPDATE_LAST_MESSAGE', {
              streamProgress: [...(lastMsg.streamProgress || []), event],
              currentStep: null
            })
          }
        },
        onComplete: (event) => {
          const data = event.data

          if (state.searchMode === 'agent') {
            // 서버 session_id 저장
            if (data.session_id && data.session_id !== state.sessionId) {
              commit('SET_SESSION_ID', data.session_id)
            }

            commit('UPDATE_LAST_MESSAGE', {
              content: data.answer || '답변을 생성하지 못했습니다.',
              isStreaming: false,
              queryType: 'agent',
              agentResult: {
                steps: data.steps || [],
                totalIterations: data.total_iterations || 0,
                toolsUsed: data.tools_used || [],
                success: data.success,
                sessionId: data.session_id
              },
              metadata: data.metadata || {}
            })
          } else {
            // NL2SQL 모드
            if (data.session_id && data.session_id !== state.sessionId) {
              commit('SET_SESSION_ID', data.session_id)
            }

            commit('UPDATE_LAST_MESSAGE', {
              content: data.answer,
              isStreaming: false,
              queryType: data.query_type || 'nl2sql',
              sql: data.sql,
              sqlResult: data.sql_result,
              responseTimeMs: data.response_time_ms,
              metadata: data.metadata,
              sessionId: data.session_id
            })
          }

          commit('SET_STREAMING', false)
          commit('SET_LOADING', false)
          commit('SET_STREAM_CONTROLLER', null)
        },
        onError: (error) => {
          const errorMessage = error.message || '스트리밍 중 오류가 발생했습니다.'
          const errorCode = error.code || 'STREAM_ERROR'

          commit('SET_ERROR', { code: errorCode, message: errorMessage })
          commit('UPDATE_LAST_MESSAGE', {
            content: `죄송합니다. ${errorMessage}`,
            isStreaming: false,
            isError: true,
            errorCode: errorCode
          })
          commit('SET_STREAMING', false)
          commit('SET_LOADING', false)
          commit('SET_STREAM_CONTROLLER', null)
        }
      }

      // 스트리밍 시작
      let controller
      if (state.searchMode === 'agent') {
        controller = agentApi.agentSearchStream(
          { question: query, sessionId: state.sessionId },
          callbacks
        )
      } else {
        controller = searchApi.searchStream(
          { query, mode: state.searchMode, sessionId: state.sessionId },
          callbacks
        )
      }

      commit('SET_STREAM_CONTROLLER', controller)
    },

    cancelStream({ state, commit }) {
      if (state.streamController) {
        state.streamController.abort()
        commit('SET_STREAMING', false)
        commit('SET_LOADING', false)
        commit('SET_STREAM_CONTROLLER', null)
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
