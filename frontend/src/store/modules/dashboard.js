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

// 목업 데이터 (초기 데모용 - resetToMock에서 API로 생성)
function getMockWidgets() {
  return [
    {
      title: '부서별 직원 수',
      widget_type: 'bar',
      query: '부서별 직원 수를 알려줘',
      sql: 'SELECT department_name, COUNT(*) as employee_count FROM employee GROUP BY department_name ORDER BY employee_count DESC',
      chart_config: {
        x_column: 'department_name',
        y_columns: ['employee_count']
      },
      cached_data: {
        columns: ['department_name', 'employee_count'],
        rows: [
          { department_name: '개발팀', employee_count: 42 },
          { department_name: '영업팀', employee_count: 35 },
          { department_name: '인사팀', employee_count: 18 },
          { department_name: '마케팅팀', employee_count: 25 },
          { department_name: '재무팀', employee_count: 15 },
          { department_name: '기획팀', employee_count: 20 },
          { department_name: '디자인팀', employee_count: 12 }
        ],
        row_count: 7
      },
      grid_position: { x: 0, y: 0, w: 6, h: 10 }
    },
    {
      title: '월별 입사자 추이 (2024)',
      widget_type: 'line',
      query: '2024년 월별 입사자 수 추이를 알려줘',
      sql: "SELECT TO_CHAR(hire_date, 'YYYY-MM') as month, COUNT(*) as hire_count FROM employee WHERE hire_date >= '2024-01-01' GROUP BY month ORDER BY month",
      chart_config: {
        x_column: 'month',
        y_columns: ['hire_count']
      },
      cached_data: {
        columns: ['month', 'hire_count'],
        rows: [
          { month: '2024-01', hire_count: 5 },
          { month: '2024-02', hire_count: 3 },
          { month: '2024-03', hire_count: 8 },
          { month: '2024-04', hire_count: 6 },
          { month: '2024-05', hire_count: 4 },
          { month: '2024-06', hire_count: 7 },
          { month: '2024-07', hire_count: 9 },
          { month: '2024-08', hire_count: 5 },
          { month: '2024-09', hire_count: 6 },
          { month: '2024-10', hire_count: 8 },
          { month: '2024-11', hire_count: 4 },
          { month: '2024-12', hire_count: 3 }
        ],
        row_count: 12
      },
      grid_position: { x: 6, y: 0, w: 6, h: 10 }
    },
    {
      title: '직급별 인원 분포',
      widget_type: 'pie',
      query: '직급별 인원 분포를 알려줘',
      sql: 'SELECT position_name, COUNT(*) as cnt FROM employee GROUP BY position_name ORDER BY cnt DESC',
      chart_config: {
        x_column: 'position_name',
        y_columns: ['cnt'],
        pie_top_n: 10
      },
      cached_data: {
        columns: ['position_name', 'cnt'],
        rows: [
          { position_name: '사원', cnt: 65 },
          { position_name: '대리', cnt: 45 },
          { position_name: '과장', cnt: 32 },
          { position_name: '차장', cnt: 18 },
          { position_name: '부장', cnt: 12 },
          { position_name: '이사', cnt: 5 }
        ],
        row_count: 6
      },
      grid_position: { x: 0, y: 10, w: 5, h: 10 }
    },
    {
      title: '전체 직원 수',
      widget_type: 'kpi',
      query: '전체 직원 수는?',
      sql: 'SELECT COUNT(*) as total_count FROM employee',
      chart_config: {
        kpi_column: 'total_count',
        kpi_suffix: '명'
      },
      cached_data: {
        columns: ['total_count'],
        rows: [{ total_count: 342 }],
        row_count: 1
      },
      grid_position: { x: 5, y: 10, w: 3, h: 5 }
    },
    {
      title: '평균 연봉',
      widget_type: 'kpi',
      query: '전체 직원 평균 연봉은?',
      sql: 'SELECT ROUND(AVG(salary)) as avg_salary FROM employee',
      chart_config: {
        kpi_column: 'avg_salary',
        kpi_suffix: '만원'
      },
      cached_data: {
        columns: ['avg_salary'],
        rows: [{ avg_salary: 5280 }],
        row_count: 1
      },
      grid_position: { x: 8, y: 10, w: 3, h: 5 }
    },
    {
      title: '부서별 평균 근속년수',
      widget_type: 'table',
      query: '부서별 평균 근속년수를 알려줘',
      sql: 'SELECT department_name, ROUND(AVG(years_of_service), 1) as avg_years, COUNT(*) as emp_count FROM employee GROUP BY department_name ORDER BY avg_years DESC',
      chart_config: {},
      cached_data: {
        columns: ['department_name', 'avg_years', 'emp_count'],
        rows: [
          { department_name: '재무팀', avg_years: 8.5, emp_count: 15 },
          { department_name: '인사팀', avg_years: 7.2, emp_count: 18 },
          { department_name: '기획팀', avg_years: 6.8, emp_count: 20 },
          { department_name: '영업팀', avg_years: 5.3, emp_count: 35 },
          { department_name: '개발팀', avg_years: 4.1, emp_count: 42 },
          { department_name: '마케팅팀', avg_years: 3.9, emp_count: 25 },
          { department_name: '디자인팀', avg_years: 3.2, emp_count: 12 }
        ],
        row_count: 7
      },
      grid_position: { x: 5, y: 15, w: 6, h: 8 }
    }
  ]
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

        // currentDashboardId가 없으면 기본 대시보드 선택
        if (!state.currentDashboardId) {
          const defaultDb = (res.my_dashboards || []).find(d => d.is_default)
          if (defaultDb) {
            commit('SET_CURRENT_DASHBOARD_ID', defaultDb.dashboard_id)
          }
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

      // 삭제된 대시보드가 현재 선택된 대시보드인 경우 기본으로 전환
      if (state.currentDashboardId === dashboardId) {
        const defaultDb = state.dashboards.find(d => d.is_default)
        if (defaultDb) {
          await dispatch('selectDashboard', defaultDb.dashboard_id)
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
      commit('SET_LOADING', true)
      try {
        const res = await personalDashboardApi.getWidgets(state.currentDashboardId)
        commit('SET_WIDGETS', res.items || [])
        commit('SET_READ_ONLY', !!res.is_read_only)

        // 응답에서 dashboard_id가 돌아오면 업데이트 (기본 대시보드 자동 생성 시)
        if (res.dashboard_id && !state.currentDashboardId) {
          commit('SET_CURRENT_DASHBOARD_ID', res.dashboard_id)
        }
      } catch (err) {
        console.error('[Dashboard] 위젯 목록 조회 실패:', err)
        commit('SET_WIDGETS', [])
      } finally {
        commit('SET_LOADING', false)
      }
    },

    async saveWidget({ commit, state }, widgetConfig) {
      const data = { ...widgetConfig }
      if (state.currentDashboardId) {
        data.dashboard_id = state.currentDashboardId
      }
      const res = await personalDashboardApi.createWidget(data)
      commit('ADD_WIDGET', res)
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

    setDashboardTheme({ commit }, theme) {
      commit('SET_DASHBOARD_THEME', theme)
    },

    // 목업 데이터 리셋 (API를 통해 생성)
    async resetToMock({ commit, state, dispatch }) {
      // 기존 위젯 모두 삭제
      for (const w of [...state.widgets]) {
        await personalDashboardApi.deleteWidget(w.widget_id).catch(() => {})
      }
      // 목업 위젯 순차 생성
      const mocks = getMockWidgets()
      for (const mock of mocks) {
        const data = { ...mock }
        if (state.currentDashboardId) {
          data.dashboard_id = state.currentDashboardId
        }
        await personalDashboardApi.createWidget(data).catch(() => {})
      }
      // 재조회
      await dispatch('fetchWidgets')
    }
  }
}
