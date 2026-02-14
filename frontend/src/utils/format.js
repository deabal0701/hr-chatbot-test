/**
 * 공통 포맷팅 유틸리티
 *
 * 날짜, 숫자 등 프로젝트 전역에서 사용하는 포맷 함수
 */

/**
 * 날짜/시간 포맷 (2026.02.12 16:38:47)
 * @param {string|Date|null} dateStr - 날짜 문자열 또는 Date 객체
 * @returns {string} 포맷된 문자열 또는 '-'
 */
export function formatDateTime(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '-'
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  const second = String(d.getSeconds()).padStart(2, '0')
  return `${year}.${month}.${day} ${hour}:${minute}:${second}`
}

/**
 * 날짜만 포맷 (2026.02.12)
 * @param {string|Date|null} dateStr - 날짜 문자열 또는 Date 객체
 * @returns {string} 포맷된 문자열 또는 '-'
 */
export function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '-'
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}.${month}.${day}`
}

/**
 * 숫자 포맷 (1,234,567)
 * @param {number|null} num - 숫자
 * @returns {string} 천단위 콤마 포맷 문자열
 */
export function formatNumber(num) {
  return (num || 0).toLocaleString()
}

/**
 * 응답시간 포맷 (123ms / 1.5s)
 * @param {number|null} ms - 밀리초
 * @returns {string} 포맷된 응답시간 문자열
 */
export function formatResponseTime(ms) {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}
