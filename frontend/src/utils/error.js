/**
 * 공통 에러 메시지 처리 유틸리티
 *
 * 위치: frontend/src/utils/error.js
 * API 에러 응답에서 사용자 친화적 메시지를 추출한다.
 * - 서버 메시지 우선 사용
 * - 에러 코드별 기본 메시지 매핑
 * - fallback 메시지 지원
 */

/** 에러 코드 → 기본 한글 메시지 매핑 */
const CODE_MESSAGES = {
  FORBIDDEN: '권한이 없어 작업을 수행할 수 없습니다',
  UNAUTHORIZED: '인증이 필요합니다. 다시 로그인해주세요',
  NOT_FOUND: '요청한 데이터를 찾을 수 없습니다',
  DUPLICATE_ERROR: '이미 존재하는 데이터입니다',
  VALIDATION_ERROR: '입력값이 올바르지 않습니다',
  BAD_REQUEST: '잘못된 요청입니다',
  INTERNAL_ERROR: '서버 내부 오류가 발생했습니다',
}

/**
 * API 에러에서 사용자용 메시지를 추출한다.
 *
 * @param {Error|string} error - catch 블록의 에러 객체 또는 'cancel' 문자열
 * @param {string} [defaultMsg='작업에 실패하였습니다'] - 모든 매핑 실패 시 fallback
 * @returns {string|null} 사용자에게 표시할 메시지. dialog cancel이면 null 반환
 */
export function getErrorMessage(error, defaultMsg = '작업에 실패하였습니다') {
  // ElMessageBox cancel 처리
  if (error === 'cancel' || error === 'close') return null

  // 서버에서 내려온 메시지가 있으면 우선 사용
  if (error?.message) return error.message

  // 에러 코드별 기본 메시지
  if (error?.code && CODE_MESSAGES[error.code]) {
    return CODE_MESSAGES[error.code]
  }

  return defaultMsg
}

/**
 * 권한 오류인지 확인한다.
 *
 * @param {Error} error - catch 블록의 에러 객체
 * @returns {boolean} FORBIDDEN 에러 여부
 */
export function isForbiddenError(error) {
  return error?.code === 'FORBIDDEN'
}
