/**
 * 마크다운 파싱 유틸리티
 * 테이블, 헤더, 리스트 등의 마크다운을 HTML로 변환
 */

/**
 * 마크다운 테이블을 HTML 테이블로 변환
 * @param {string} text - 마크다운 텍스트
 * @returns {string} - 변환된 텍스트
 */
function parseMarkdownTable(text) {
  const lines = text.split('\n')
  let result = []
  let inTable = false
  let tableRows = []
  let tableId = 0

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()

    if (line.startsWith('|') && line.endsWith('|')) {
      // 구분선 스킵
      if (/^\|[\s\-:|]+\|$/.test(line)) {
        continue
      }

      if (!inTable) {
        inTable = true
        tableRows = []
        tableId++
      }

      const cells = line.slice(1, -1).split('|').map(cell => cell.trim())
      tableRows.push(cells)
    } else {
      if (inTable && tableRows.length > 0) {
        result.push(buildHtmlTable(tableRows, tableId))
        tableRows = []
        inTable = false
      }
      result.push(line)
    }
  }

  if (inTable && tableRows.length > 0) {
    result.push(buildHtmlTable(tableRows, tableId))
  }

  return result.join('\n')
}

/**
 * HTML 테이블 생성 (복사 버튼 포함)
 * @param {Array} rows - 테이블 행 데이터
 * @param {number} tableId - 테이블 고유 ID
 * @returns {string} - HTML 테이블 문자열
 */
function buildHtmlTable(rows, tableId) {
  if (rows.length === 0) return ''

  let html = `<div class="md-table-wrapper">`
  html += `<button class="copy-table-btn" onclick="window.copyTable(this)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></button>`
  html += '<div class="md-table-scroll">'
  html += '<table class="md-table">'

  // 헤더
  html += '<thead><tr>'
  rows[0].forEach(cell => {
    html += `<th>${cell}</th>`
  })
  html += '</tr></thead>'

  // 바디
  if (rows.length > 1) {
    html += '<tbody>'
    for (let i = 1; i < rows.length; i++) {
      html += '<tr>'
      rows[i].forEach(cell => {
        html += `<td>${cell}</td>`
      })
      html += '</tr>'
    }
    html += '</tbody>'
  }

  html += '</table></div></div>'
  return html
}

/**
 * 마크다운 텍스트를 HTML로 변환
 * 테이블만 HTML로 변환하고, 나머지는 일반 텍스트로 유지
 * @param {string} content - 마크다운 텍스트
 * @returns {string} - HTML 문자열
 */
export function formatMarkdownToHtml(content) {
  if (!content) {
    return '<span style="color: #999;">내용이 없습니다.</span>'
  }

  if (content.trim() === '') {
    return '<span style="color: #999;">답변이 비어있습니다.</span>'
  }

  let text = content

  // 1. 테이블만 파싱 (표 형식만 HTML로 변환)
  text = parseMarkdownTable(text)

  // 2. 줄바꿈 (테이블 내부 제외)
  text = text.replace(/\n(?![^<]*<\/table>)/g, '<br>')

  return text
}

/**
 * 전역 테이블 복사 함수 등록
 * 컴포넌트에서 한 번만 호출해야 함
 */
export function registerTableCopyFunction() {
  if (typeof window !== 'undefined') {
    window.copyTable = (btn) => {
      const wrapper = btn.closest('.md-table-wrapper')
      if (!wrapper) return

      const table = wrapper.querySelector('table')
      if (!table) return

      // 테이블 데이터를 탭 구분 텍스트로 변환
      let text = ''
      const rows = table.querySelectorAll('tr')
      rows.forEach(row => {
        const cells = row.querySelectorAll('th, td')
        const rowData = Array.from(cells).map(cell => cell.textContent.trim())
        text += rowData.join('\t') + '\n'
      })

      // 복사 성공 피드백 함수
      const showSuccess = () => {
        btn.style.borderColor = 'var(--color-success)'
        btn.style.color = 'var(--color-success)'
        showToast('표가 클립보드에 복사되었습니다.')
        setTimeout(() => {
          btn.style.borderColor = ''
          btn.style.color = ''
        }, 1500)
      }

      // 복사 실패 피드백 함수
      const showError = () => {
        showToast('복사 기능은 HTTPS 환경에서만 지원됩니다.', 'warning')
      }

      // HTTPS 또는 localhost 환경 체크
      if (window.isSecureContext && navigator.clipboard) {
        navigator.clipboard.writeText(text).then(showSuccess).catch(() => {
          // Clipboard API 실패 시 fallback
          if (fallbackCopy(text)) {
            showSuccess()
          } else {
            showError()
          }
        })
      } else {
        // HTTP 환경: fallback 사용
        if (fallbackCopy(text)) {
          showSuccess()
        } else {
          showError()
        }
      }
    }

    // Fallback 복사 (execCommand 사용)
    function fallbackCopy(text) {
      try {
        const textarea = document.createElement('textarea')
        textarea.value = text
        textarea.style.position = 'fixed'
        textarea.style.left = '-9999px'
        document.body.appendChild(textarea)
        textarea.select()
        const result = document.execCommand('copy')
        document.body.removeChild(textarea)
        return result
      } catch {
        return false
      }
    }

    // 토스트 메시지 표시
    function showToast(message, type = 'success') {
      // Element Plus ElMessage 사용 시도
      if (window.ElMessage) {
        window.ElMessage({ message, type, duration: 2000 })
        return
      }

      // 기본 토스트 생성 (다크모드 호환)
      const toast = document.createElement('div')
      toast.textContent = message
      toast.className = `md-toast md-toast-${type}`
      toast.style.cssText = `
        position: fixed;
        bottom: 80px;
        left: 50%;
        transform: translateX(-50%);
        padding: 12px 24px;
        background: var(--bg-color-card);
        color: var(--text-color-primary);
        border: 1px solid ${type === 'success' ? 'var(--color-success)' : 'var(--color-warning)'};
        border-radius: 8px;
        font-size: 14px;
        z-index: 9999;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      `
      document.body.appendChild(toast)
      setTimeout(() => {
        toast.style.opacity = '0'
        toast.style.transition = 'opacity 0.3s'
        setTimeout(() => document.body.removeChild(toast), 300)
      }, 2000)
    }
  }
}
