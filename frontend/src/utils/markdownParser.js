/**
 * 마크다운 파싱 유틸리티
 * 테이블, 헤더, 리스트, 코드, 볼드 등의 마크다운을 HTML로 변환
 *
 * 처리 순서 (내부 마크다운 오변환 방지를 위해 순서 엄수):
 *   1. 코드 블록 (```...```) → placeholder 보호
 *   2. 인라인 코드 (`...`)  → placeholder 보호
 *   3. 테이블 (| ... |)     → HTML <table> 변환
 *   4. 헤더 (##, ###)       → <span class="md-h2/h3">
 *   5. 볼드 (**text**)      → <strong>
 *   6. 리스트 (-, *, 1.)    → <span class="md-list-item">
 *   7. 줄바꿈 (\n)          → <br>
 *   8. placeholder 복원
 */

/**
 * HTML 특수문자 이스케이프 (XSS 방지)
 * @param {string} text - 이스케이프할 텍스트
 * @returns {string} - 이스케이프된 텍스트
 */
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

/**
 * 테이블 셀용 HTML 이스케이프 (<br> 태그만 허용)
 * LLM이 테이블 셀 내 줄바꿈으로 <br> 태그를 사용하는 경우 보존
 * @param {string} text - 이스케이프할 텍스트
 * @returns {string} - 이스케이프된 텍스트 (<br>은 유지)
 */
function escapeCellHtml(text) {
  return escapeHtml(text).replace(/&lt;br\s*\/?&gt;/gi, '<br>')
}

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
    html += `<th>${escapeCellHtml(cell)}</th>`
  })
  html += '</tr></thead>'

  // 바디
  if (rows.length > 1) {
    html += '<tbody>'
    for (let i = 1; i < rows.length; i++) {
      html += '<tr>'
      rows[i].forEach(cell => {
        html += `<td>${escapeCellHtml(cell)}</td>`
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
  const placeholders = []

  // placeholder 등록 (코드 블록 등 내부 마크다운 처리 방지)
  const hold = (html) => {
    const idx = placeholders.length
    placeholders.push(html)
    return `\x00${idx}\x00`
  }

  // 1. 코드 블록 (```lang\n...\n```) → placeholder 보호
  text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    const escaped = escapeHtml(code.trimEnd())
    return hold(
      `<pre><code${lang ? ` class="language-${lang}"` : ''}>${escaped}</code></pre>`
    )
  })

  // 2. 인라인 코드 (`...`) → placeholder 보호
  text = text.replace(/`([^`\n]+)`/g, (_, code) => {
    return hold(`<code>${escapeHtml(code)}</code>`)
  })

  // 3. 테이블 파싱 (기존 기능 유지, cell escape 추가)
  text = parseMarkdownTable(text)

  // 4. 헤더 (### → md-h3, ## → md-h2, 순서 중요: ### 먼저)
  text = text.replace(/^### (.+)$/gm, '<span class="md-h3">$1</span>')
  text = text.replace(/^## (.+)$/gm, '<span class="md-h2">$1</span>')

  // 5. 볼드 (**text**)
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')

  // 6. 리스트 (순서없는: - , * / 순서있는: 1~99.)
  text = text.replace(/^[\-\*] (.+)$/gm, '<span class="md-list-item">• $1</span>')
  text = text.replace(/^(\d{1,2})\. (.+)$/gm, '<span class="md-list-item">$1. $2</span>')

  // 7. 줄바꿈 (연속 개행 축소 후 <br> 변환)
  text = text.replace(/\n{2,}/g, '\n')
  text = text.replace(/\n/g, '<br>')

  // 8. 블록 요소 사이 <br> 제거 (display:block + <br> 이중 줄바꿈 방지)
  //    </span><br><span class="md-..."> 패턴에서 <br> 제거
  text = text.replace(/(<\/span>)(<br>)+(<span class="md-)/g, '$1$3')

  // 9. placeholder 복원
  placeholders.forEach((html, i) => {
    text = text.replace(`\x00${i}\x00`, html)
  })

  return text
}

/**
 * 전역 테이블 복사 함수 등록
 * 중복 등록 방지 포함
 */
export function registerTableCopyFunction() {
  if (typeof window === 'undefined' || window._copyTableRegistered) return
  window._copyTableRegistered = true

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
