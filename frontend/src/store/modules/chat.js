import searchApi from '@/api/search'
import agentApi from '@/api/agent'
import historyApi from '@/api/history'

// 채팅 상태 모듈
export default {
  namespaced: true,

  state: () => ({
    messages: [],
    isLoading: false,
    searchMode: 'nl2sql', // 'auto' | 'rag' | 'nl2sql' | 'agent' (기본값: nl2sql)
    error: null,
    sessionId: null, // Agent 멀티턴 대화용 세션 ID (서버에서 생성)
    // 채팅 히스토리 (API 연동)
    chatHistory: [],
    historyLoading: false,
    activeChatId: null, // 현재 선택된 채팅의 session_key
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
    },
    // 채팅 이력 mutations
    SET_CHAT_HISTORY(state, history) {
      state.chatHistory = history
    },
    SET_HISTORY_LOADING(state, loading) {
      state.historyLoading = loading
    },
    REMOVE_CHAT_HISTORY_ITEM(state, sessionKey) {
      state.chatHistory = state.chatHistory.filter(item => item.session_key !== sessionKey)
    }
  },

  getters: {
    messageCount: (state) => state.messages.length,
    hasError: (state) => state.error !== null,
    lastMessage: (state) => state.messages.length > 0 ? state.messages[state.messages.length - 1] : null,
    getChatHistory: (state) => state.chatHistory,
    getActiveChatId: (state) => state.activeChatId,
    isHistoryLoading: (state) => state.historyLoading
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

        // 이력 갱신
        dispatch('fetchChatHistory')
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

    async sendMessageStream({ commit, state, dispatch }, query) {
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

          // 이력 갱신
          dispatch('fetchChatHistory')
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

    // =========================================================================
    // 채팅 이력 액션
    // =========================================================================

    async fetchChatHistory({ commit }, searchQuery = null) {
      commit('SET_HISTORY_LOADING', true)
      try {
        const params = { limit: 50, offset: 0 }
        if (searchQuery) params.search = searchQuery
        const response = await historyApi.listSessions(params)
        commit('SET_CHAT_HISTORY', response.items || [])
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error('[fetchChatHistory] Failed:', error)
        }
        commit('SET_CHAT_HISTORY', [])
      } finally {
        commit('SET_HISTORY_LOADING', false)
      }
    },

    async loadChatSession({ commit }, sessionKey) {
      commit('SET_LOADING', true)
      commit('SET_ACTIVE_CHAT', sessionKey)
      commit('CLEAR_MESSAGES')
      commit('CLEAR_ERROR')

      try {
        const response = await historyApi.getSessionHistory(sessionKey)
        const records = response.items || []

        // 이력 레코드를 메시지 배열로 변환
        for (const record of records) {
          // 사용자 메시지
          commit('ADD_MESSAGE', {
            role: 'user',
            content: record.question,
            timestamp: new Date(record.requested_at || record.created_at)
          })

          // AI 응답 메시지
          const traceData = record.trace_data || {}
          const assistantMsg = {
            role: 'assistant',
            content: record.answer || '',
            queryType: record.request_type,
            timestamp: new Date(record.completed_at || record.created_at),
            isHistory: true
          }

          // request_type별 추가 데이터 매핑
          if (record.request_type === 'agent') {
            assistantMsg.agentResult = {
              steps: traceData.steps || [],
              totalIterations: traceData.iteration_count || 0,
              toolsUsed: traceData.tools_used || [],
              success: record.success
            }
          } else if (record.request_type === 'nl2sql') {
            assistantMsg.sql = traceData.sql
            assistantMsg.sqlResult = traceData.sql_result
          } else if (record.request_type === 'rag') {
            assistantMsg.sources = traceData.sources
          }

          commit('ADD_MESSAGE', assistantMsg)
        }

        // 세션 ID 설정 (멀티턴 대화 재개용)
        if (records.length > 0 && records[0].session_id) {
          commit('SET_SESSION_ID', records[0].session_id)
          // 세션의 request_type으로 모드 설정
          const mode = records[records.length - 1].request_type
          if (mode) commit('SET_MODE', mode)
        }
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error('[loadChatSession] Failed:', error)
        }
        commit('SET_ERROR', {
          code: error.code || 'LOAD_ERROR',
          message: '대화 이력을 불러오는데 실패했습니다.'
        })
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async deleteChatHistory({ commit, state }, sessionKey) {
      try {
        await historyApi.deleteSession(sessionKey)
        commit('REMOVE_CHAT_HISTORY_ITEM', sessionKey)
        // 현재 보고 있는 채팅이 삭제된 경우 초기화
        if (state.activeChatId === sessionKey) {
          commit('CREATE_NEW_CHAT')
        }
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error('[deleteChatHistory] Failed:', error)
        }
      }
    },

    selectChat({ dispatch }, sessionKey) {
      dispatch('loadChatSession', sessionKey)
    },

    newChat({ commit }) {
      commit('CREATE_NEW_CHAT')
    }
  }
}
