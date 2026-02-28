/**
 * 개인 대시보드 Vuex 모듈
 * Backend API 연동 (personalDashboard API)
 * - 멀티 대시보드 관리 (CRUD + 기본/공유 설정)
 * - 위젯 CRUD + 레이아웃
 */
import personalDashboardApi from '@/api/personalDashboard'

const THEME_STORAGE_KEY = 'mureum_dashboard_theme'

// 대시보드 테마 로드 ('auto' | 'light' | 'dark')
function loadTheme() {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY) || 'auto'
  } catch {
    return 'auto'
  }
}

// 대시보드 테마 저장
function saveTheme(theme) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  } catch {
    // ignore
  }
}

export default {
  namespaced: true,

  state: () => ({
    // 대시보드 관리
    dashboards: [],
    sharedDashboards: [],
    currentDashboardId: null,
    isLoadingDashboards: false,
    isReadOnly: false,

    // 위젯 관리
    widgets: [],
    isLoading: false,
    editMode: false,
    pendingLayout: null,
    refreshingWidgets: {},
    dashboardTheme: loadTheme()
  }),

  mutations: {
    // 대시보드
    SET_DASHBOARDS(state, { myDashboards, sharedDashboards }) {
      state.dashboards = myDashboards
      state.sharedDashboards = sharedDashboards
    },
    SET_LOADING_DASHBOARDS(state, loading) {
      state.isLoadingDashboards = loading
    },
    SET_CURRENT_DASHBOARD_ID(state, id) {
      state.currentDashboardId = id
    },
    SET_READ_ONLY(state, readOnly) {
      state.isReadOnly = readOnly
    },
    UPDATE_DASHBOARD(state, dashboard) {
      const idx = state.dashboards.findIndex(d => d.dashboard_id === dashboard.dashboard_id)
      if (idx !== -1) {
        state.dashboards[idx] = { ...state.dashboards[idx], ...dashboard }
      }
    },
    REMOVE_DASHBOARD(state, dashboardId) {
      state.dashboards = state.dashboards.filter(d => d.dashboard_id !== dashboardId)
    },
    ADD_DASHBOARD(state, dashboard) {
      state.dashboards.push(dashboard)
    },

    // 위젯
    SET_WIDGETS(state, widgets) {
      state.widgets = widgets
    },
    SET_LOADING(state, loading) {
      state.isLoading = loading
    },
    SET_EDIT_MODE(state, mode) {
      state.editMode = mode
    },
    SET_PENDING_LAYOUT(state, layout) {
      state.pendingLayout = layout
    },
    ADD_WIDGET(state, widget) {
      state.widgets.push(widget)
    },
    UPDATE_WIDGET(state, { widgetId, updates }) {
      const idx = state.widgets.findIndex(w => w.widget_id === widgetId)
      if (idx !== -1) {
        state.widgets[idx] = { ...state.widgets[idx], ...updates }
      }
    },
    REMOVE_WIDGET(state, widgetId) {
      state.widgets = state.widgets.filter(w => w.widget_id !== widgetId)
    },
    UPDATE_LAYOUT(state, layoutItems) {
      for (const item of layoutItems) {
        const widget = state.widgets.find(w => w.widget_id === item.widget_id)
        if (widget) {
          widget.grid_position = { x: item.x, y: item.y, w: item.w, h: item.h }
        }
      }
    },
    SET_WIDGET_REFRESHING(state, { widgetId, refreshing }) {
      state.refreshingWidgets = { ...state.refreshingWidgets, [widgetId]: refreshing }
    },
    SET_DASHBOARD_THEME(state, theme) {
      state.dashboardTheme = theme
      saveTheme(theme)
    },
    CLEAR_STATE(state) {
      state.dashboards = []
      state.sharedDashboards = []
      state.currentDashboardId = null
      state.isReadOnly = false
      state.widgets = []
      state.isLoading = false
      state.editMode = false
      state.pendingLayout = null
      state.refreshingWidgets = {}
    }
  },

  getters: {
    // 대시보드
    currentDashboard: (state) => {
      if (!state.currentDashboardId) return null
      return state.dashboards.find(d => d.dashboard_id === state.currentDashboardId)
        || state.sharedDashboards.find(d => d.dashboard_id === state.currentDashboardId)
    },
    defaultDashboard: (state) => state.dashboards.find(d => d.is_default),
    myDashboards: (state) => state.dashboards,
    sharedDashboardList: (state) => state.sharedDashboards,
    isReadOnly: (state) => state.isReadOnly,
    canShare: (state, getters, rootState) => {
      const roleCode = rootState.auth?.user?.role_code
      return roleCode === 'GLOBAL' || roleCode === 'TENANT'
    },

    // 위젯
    widgetCount: (state) => state.widgets.length,
    isEditMode: (state) => state.editMode,
    widgetById: (state) => (id) => state.widgets.find(w => w.widget_id === id),
    isWidgetRefreshing: (state) => (id) => !!state.refreshingWidgets[id],
    dashboardTheme: (state) => state.dashboardTheme,
    gridLayout: (state) => state.widgets.map(w => ({
      i: String(w.widget_id),
      x: w.grid_position.x,
      y: w.grid_position.y,
      w: w.grid_position.w,
      h: w.grid_position.h,
      minW: w.widget_type === 'kpi' ? 2 : 4,
      minH: w.widget_type === 'kpi' ? 3 : 6
    }))
  },

  actions: {
    // ============================================
    // 대시보드 Actions
    // ============================================

    async fetchDashboards({ commit, state }) {
      commit('SET_LOADING_DASHBOARDS', true)
      try {
        const res = await personalDashboardApi.getDashboards()
        commit('SET_DASHBOARDS', {
          myDashboards: res.my_dashboards || [],
          sharedDashboards: res.shared_dashboards || []
        })

        // currentDashboardId 유효성 검증 후 기본 대시보드 선택
        const allIds = [
          ...(res.my_dashboards || []).map(d => d.dashboard_id),
          ...(res.shared_dashboards || []).map(d => d.dashboard_id)
        ]
        if (!state.currentDashboardId || !allIds.includes(state.currentDashboardId)) {
          const defaultDb = (res.my_dashboards || []).find(d => d.is_default)
          commit('SET_CURRENT_DASHBOARD_ID', defaultDb ? defaultDb.dashboard_id : null)
        }
      } catch (err) {
        console.error('[Dashboard] 대시보드 목록 조회 실패:', err)
      } finally {
        commit('SET_LOADING_DASHBOARDS', false)
      }
    },

    async selectDashboard({ commit, dispatch }, dashboardId) {
      commit('SET_CURRENT_DASHBOARD_ID', dashboardId)
      commit('SET_EDIT_MODE', false)
      commit('SET_PENDING_LAYOUT', null)
      await dispatch('fetchWidgets')
    },

    async createDashboard({ commit, dispatch }, data) {
      const res = await personalDashboardApi.createDashboard(data)
      commit('ADD_DASHBOARD', res)
      return res
    },

    async updateDashboard({ commit }, { dashboardId, data }) {
      const res = await personalDashboardApi.updateDashboard(dashboardId, data)
      commit('UPDATE_DASHBOARD', res)
      return res
    },

    async deleteDashboard({ commit, state, dispatch }, dashboardId) {
      await personalDashboardApi.deleteDashboard(dashboardId)
      commit('REMOVE_DASHBOARD', dashboardId)

      // 삭제된 대시보드가 현재 선택된 대시보드인 경우
      if (state.currentDashboardId === dashboardId) {
        const defaultDb = state.dashboards.find(d => d.is_default)
        if (defaultDb) {
          await dispatch('selectDashboard', defaultDb.dashboard_id)
        } else {
          // 마지막 대시보드 삭제: 상태 초기화
          commit('SET_CURRENT_DASHBOARD_ID', null)
          commit('SET_WIDGETS', [])
          commit('SET_READ_ONLY', false)
        }
      }
    },

    async setDefaultDashboard({ dispatch }, dashboardId) {
      await personalDashboardApi.setDefaultDashboard(dashboardId)
      await dispatch('fetchDashboards')
    },

    async shareDashboard({ commit }, { dashboardId, data }) {
      const res = await personalDashboardApi.shareDashboard(dashboardId, data)
      commit('UPDATE_DASHBOARD', res)
      return res
    },

    // ============================================
    // 위젯 Actions
    // ============================================

    async fetchWidgets({ commit, state }) {
      // 대시보드 없으면 API 호출 스킵
      if (!state.currentDashboardId) {
        commit('SET_WIDGETS', [])
        commit('SET_READ_ONLY', false)
        return
      }

      commit('SET_LOADING', true)
      try {
        const res = await personalDashboardApi.getWidgets(state.currentDashboardId)
        commit('SET_WIDGETS', res.items || [])
        commit('SET_READ_ONLY', !!res.is_read_only)
      } catch (err) {
        console.error('[Dashboard] 위젯 목록 조회 실패:', err)
        commit('SET_WIDGETS', [])
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async saveWidget({ commit, state }, widgetConfig) {
      const data = { ...widgetConfig }
      // widget config에 dashboard_id가 없으면 현재 대시보드 사용
      if (!data.dashboard_id && state.currentDashboardId) {
        data.dashboard_id = state.currentDashboardId
      }
      const res = await personalDashboardApi.createWidget(data)
      // 현재 대시보드에 추가된 위젯만 로컬 상태에 반영
      if (data.dashboard_id === state.currentDashboardId) {
        commit('ADD_WIDGET', res)
      }
      return res
    },

    async updateWidget({ commit }, { widgetId, updates }) {
      const res = await personalDashboardApi.updateWidget(widgetId, updates)
      commit('UPDATE_WIDGET', { widgetId, updates: res })
      return res
    },

    async deleteWidget({ commit }, widgetId) {
      await personalDashboardApi.deleteWidget(widgetId)
      commit('REMOVE_WIDGET', widgetId)
    },

    async saveLayout({ state }) {
      const layoutItems = state.widgets.map((w, idx) => ({
        widget_id: w.widget_id,
        x: w.grid_position.x,
        y: w.grid_position.y,
        w: w.grid_position.w,
        h: w.grid_position.h
      }))
      await personalDashboardApi.saveLayout(layoutItems, state.currentDashboardId)
    },

    async refreshWidget({ commit, state }, widgetId) {
      commit('SET_WIDGET_REFRESHING', { widgetId, refreshing: true })
      try {
        const res = await personalDashboardApi.refreshWidget(widgetId)
        commit('UPDATE_WIDGET', {
          widgetId,
          updates: {
            cached_data: res.cached_data,
            last_refreshed_at: res.last_refreshed_at
          }
        })
      } catch (err) {
        console.error('[Dashboard] 위젯 새로고침 실패:', err)
        throw err
      } finally {
        commit('SET_WIDGET_REFRESHING', { widgetId, refreshing: false })
      }
    },

    async refreshAllWidgets({ dispatch, state }) {
      const promises = state.widgets
        .filter(w => w.sql)
        .map(w => dispatch('refreshWidget', w.widget_id).catch(() => {}))
      await Promise.allSettled(promises)
    },

    enterEditMode({ commit, state }) {
      const backup = state.widgets.map(w => ({ ...w, grid_position: { ...w.grid_position } }))
      commit('SET_PENDING_LAYOUT', backup)
      commit('SET_EDIT_MODE', true)
    },

    cancelEditMode({ commit, state }) {
      if (state.pendingLayout) {
        commit('SET_WIDGETS', state.pendingLayout)
      }
      commit('SET_PENDING_LAYOUT', null)
      commit('SET_EDIT_MODE', false)
    },

    async saveEditMode({ dispatch, commit }) {
      await dispatch('saveLayout')
      commit('SET_PENDING_LAYOUT', null)
      commit('SET_EDIT_MODE', false)
    },

    clearState({ commit }) {
      commit('CLEAR_STATE')
    },

    setDashboardTheme({ commit }, theme) {
      commit('SET_DASHBOARD_THEME', theme)
    }
  }
}
