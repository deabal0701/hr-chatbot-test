/**
 * 개인 대시보드 Vuex 모듈
 * 프로토타입: localStorage 기반 (Backend 연동 전)
 */

const STORAGE_KEY = 'mureum_dashboard_widgets'
const THEME_STORAGE_KEY = 'mureum_dashboard_theme'

// localStorage에서 위젯 로드
function loadFromStorage() {
  try {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  } catch {
    return []
  }
}

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

// localStorage에 위젯 저장
function saveToStorage(widgets) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(widgets))
  } catch {
    // ignore
  }
}

// 목업 데이터 (초기 데모용)
function getMockWidgets() {
  return [
    {
      widget_id: 1,
      title: '부서별 직원 수',
      widget_type: 'bar',
      query: '부서별 직원 수를 알려줘',
      sql: 'SELECT department_name, COUNT(*) as employee_count FROM employee GROUP BY department_name ORDER BY employee_count DESC',
      chart_config: {
        x_column: 'department_name',
        y_columns: ['employee_count'],
        pie_top_n: null,
        kpi_column: null,
        kpi_suffix: null
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
        row_count: 7,
        cached_at: new Date().toISOString()
      },
      grid_position: { x: 0, y: 0, w: 6, h: 10 },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_refreshed_at: new Date().toISOString()
    },
    {
      widget_id: 2,
      title: '월별 입사자 추이 (2024)',
      widget_type: 'line',
      query: '2024년 월별 입사자 수 추이를 알려줘',
      sql: "SELECT TO_CHAR(hire_date, 'YYYY-MM') as month, COUNT(*) as hire_count FROM employee WHERE hire_date >= '2024-01-01' GROUP BY month ORDER BY month",
      chart_config: {
        x_column: 'month',
        y_columns: ['hire_count'],
        pie_top_n: null,
        kpi_column: null,
        kpi_suffix: null
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
        row_count: 12,
        cached_at: new Date().toISOString()
      },
      grid_position: { x: 6, y: 0, w: 6, h: 10 },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_refreshed_at: new Date().toISOString()
    },
    {
      widget_id: 3,
      title: '직급별 인원 분포',
      widget_type: 'pie',
      query: '직급별 인원 분포를 알려줘',
      sql: 'SELECT position_name, COUNT(*) as cnt FROM employee GROUP BY position_name ORDER BY cnt DESC',
      chart_config: {
        x_column: 'position_name',
        y_columns: ['cnt'],
        pie_top_n: 10,
        kpi_column: null,
        kpi_suffix: null
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
        row_count: 6,
        cached_at: new Date().toISOString()
      },
      grid_position: { x: 0, y: 10, w: 5, h: 10 },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_refreshed_at: new Date().toISOString()
    },
    {
      widget_id: 4,
      title: '전체 직원 수',
      widget_type: 'kpi',
      query: '전체 직원 수는?',
      sql: 'SELECT COUNT(*) as total_count FROM employee',
      chart_config: {
        x_column: null,
        y_columns: null,
        pie_top_n: null,
        kpi_column: 'total_count',
        kpi_suffix: '명'
      },
      cached_data: {
        columns: ['total_count'],
        rows: [{ total_count: 342 }],
        row_count: 1,
        cached_at: new Date().toISOString()
      },
      grid_position: { x: 5, y: 10, w: 3, h: 5 },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_refreshed_at: new Date().toISOString()
    },
    {
      widget_id: 5,
      title: '평균 연봉',
      widget_type: 'kpi',
      query: '전체 직원 평균 연봉은?',
      sql: 'SELECT ROUND(AVG(salary)) as avg_salary FROM employee',
      chart_config: {
        x_column: null,
        y_columns: null,
        pie_top_n: null,
        kpi_column: 'avg_salary',
        kpi_suffix: '만원'
      },
      cached_data: {
        columns: ['avg_salary'],
        rows: [{ avg_salary: 5280 }],
        row_count: 1,
        cached_at: new Date().toISOString()
      },
      grid_position: { x: 8, y: 10, w: 3, h: 5 },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_refreshed_at: new Date().toISOString()
    },
    {
      widget_id: 6,
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
        row_count: 7,
        cached_at: new Date().toISOString()
      },
      grid_position: { x: 5, y: 15, w: 6, h: 8 },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      last_refreshed_at: new Date().toISOString()
    }
  ]
}

let nextWidgetId = 100

export default {
  namespaced: true,

  state: () => ({
    widgets: [],
    isLoading: false,
    editMode: false,
    pendingLayout: null,
    refreshingWidgets: {},
    dashboardTheme: loadTheme() // 'auto' | 'light' | 'dark'
  }),

  mutations: {
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
      saveToStorage(state.widgets)
    },
    UPDATE_WIDGET(state, { widgetId, updates }) {
      const idx = state.widgets.findIndex(w => w.widget_id === widgetId)
      if (idx !== -1) {
        state.widgets[idx] = { ...state.widgets[idx], ...updates, updated_at: new Date().toISOString() }
        saveToStorage(state.widgets)
      }
    },
    REMOVE_WIDGET(state, widgetId) {
      state.widgets = state.widgets.filter(w => w.widget_id !== widgetId)
      saveToStorage(state.widgets)
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
    fetchWidgets({ commit }) {
      commit('SET_LOADING', true)
      // 프로토타입: localStorage에서 로드, 없으면 목업
      const stored = loadFromStorage()
      const widgets = stored.length > 0 ? stored : getMockWidgets()
      if (stored.length === 0) saveToStorage(widgets)
      commit('SET_WIDGETS', widgets)
      commit('SET_LOADING', false)
    },

    saveWidget({ commit }, widgetConfig) {
      const widget = {
        widget_id: nextWidgetId++,
        ...widgetConfig,
        grid_position: widgetConfig.grid_position || { x: 0, y: 0, w: 6, h: 10 },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        last_refreshed_at: new Date().toISOString()
      }
      commit('ADD_WIDGET', widget)
      return widget
    },

    updateWidget({ commit }, { widgetId, updates }) {
      commit('UPDATE_WIDGET', { widgetId, updates })
    },

    deleteWidget({ commit }, widgetId) {
      commit('REMOVE_WIDGET', widgetId)
    },

    saveLayout({ commit, state }) {
      const layoutItems = state.widgets.map(w => ({
        widget_id: w.widget_id,
        ...w.grid_position
      }))
      commit('UPDATE_LAYOUT', layoutItems)
    },

    refreshWidget({ commit, state }, widgetId) {
      commit('SET_WIDGET_REFRESHING', { widgetId, refreshing: true })
      // 프로토타입: 1초 딜레이 시뮬레이션
      setTimeout(() => {
        const widget = state.widgets.find(w => w.widget_id === widgetId)
        if (widget) {
          commit('UPDATE_WIDGET', {
            widgetId,
            updates: { last_refreshed_at: new Date().toISOString() }
          })
        }
        commit('SET_WIDGET_REFRESHING', { widgetId, refreshing: false })
      }, 1000)
    },

    refreshAllWidgets({ dispatch, state }) {
      for (const widget of state.widgets) {
        dispatch('refreshWidget', widget.widget_id)
      }
    },

    enterEditMode({ commit, state }) {
      const backup = state.widgets.map(w => ({ ...w, grid_position: { ...w.grid_position } }))
      commit('SET_PENDING_LAYOUT', backup)
      commit('SET_EDIT_MODE', true)
    },

    cancelEditMode({ commit, state }) {
      if (state.pendingLayout) {
        commit('SET_WIDGETS', state.pendingLayout)
        saveToStorage(state.pendingLayout)
      }
      commit('SET_PENDING_LAYOUT', null)
      commit('SET_EDIT_MODE', false)
    },

    saveEditMode({ dispatch, commit, state }) {
      dispatch('saveLayout')
      saveToStorage(state.widgets)
      commit('SET_PENDING_LAYOUT', null)
      commit('SET_EDIT_MODE', false)
    },

    setDashboardTheme({ commit }, theme) {
      commit('SET_DASHBOARD_THEME', theme)
    },

    // 목업 데이터 리셋
    resetToMock({ commit }) {
      const widgets = getMockWidgets()
      saveToStorage(widgets)
      commit('SET_WIDGETS', widgets)
    }
  }
}
