/**
 * 테마(다크모드) Composable
 * Vuex app 모듈의 테마 상태 접근을 캡슐화
 */
import { computed } from 'vue'
import { useStore } from 'vuex'

export function useTheme() {
  const store = useStore()

  const isDarkMode = computed(() => store.getters['app/isDarkMode'])
  const toggleDarkMode = () => store.dispatch('app/toggleDarkMode')

  return { isDarkMode, toggleDarkMode }
}
