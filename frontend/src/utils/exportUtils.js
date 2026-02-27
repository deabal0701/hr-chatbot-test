/**
 * 대시보드 위젯 내보내기 유틸리티
 *
 * - sanitizeFilename: 파일명 특수문자 제거
 * - formatTimestamp: yyyyMMdd_HHmmss 형식 타임스탬프
 * - downloadBlob: Blob → 파일 다운로드
 * - downloadCsv: columns + rows → CSV 다운로드
 */

/**
 * 파일명에 사용할 수 없는 특수문자 제거
 */
export function sanitizeFilename(name) {
  return (name || 'export')
    .replace(/[\\/:*?"<>|]/g, '_')
    .replace(/\s+/g, '_')
    .slice(0, 100)
}

/**
 * yyyyMMdd_HHmmss 형식 타임스탬프
 */
export function formatTimestamp(date = new Date()) {
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}_${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`
}

/**
 * Blob을 파일로 다운로드
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * columns + rows → BOM 포함 UTF-8 CSV 파일 다운로드
 */
export function downloadCsv(columns, rows, filename) {
  const escapeCsv = (val) => {
    if (val === null || val === undefined) return ''
    const str = String(val)
    if (str.includes(',') || str.includes('"') || str.includes('\n')) {
      return `"${str.replace(/"/g, '""')}"`
    }
    return str
  }

  const header = columns.map(escapeCsv).join(',')
  const body = rows.map(row => columns.map(col => escapeCsv(row[col])).join(',')).join('\n')
  const csvContent = '\uFEFF' + header + '\n' + body

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  downloadBlob(blob, filename)
}

/**
 * data URL(base64)을 파일로 다운로드
 */
export function downloadDataUrl(dataUrl, filename) {
  const link = document.createElement('a')
  link.href = dataUrl
  link.download = filename
  link.click()
}

/**
 * 캡처 시 export-exclude 클래스 요소를 제외하는 필터
 */
function exportFilter(domNode) {
  return !domNode.classList?.contains('export-exclude')
}

/**
 * 스크롤 영역을 임시 확장하여 전체 콘텐츠를 캡처 가능하게 하고,
 * 캡처 후 원래 스타일을 복원하는 헬퍼
 * @param {HTMLElement} element - 확장 대상
 * @returns {Function} 복원 함수
 */
function expandForCapture(element) {
  const saved = {
    overflow: element.style.overflow,
    height: element.style.height,
    maxHeight: element.style.maxHeight
  }
  element.style.overflow = 'visible'
  element.style.height = 'auto'
  element.style.maxHeight = 'none'
  return () => {
    element.style.overflow = saved.overflow
    element.style.height = saved.height
    element.style.maxHeight = saved.maxHeight
  }
}

/**
 * DOM 요소를 PNG로 캡처하여 다운로드 (html-to-image)
 * - export-exclude 클래스 요소 제외
 * - 스크롤 영역 전체 캡처 (overflow 임시 확장)
 */
export async function captureElementPng(element, filename) {
  const { toPng } = await import('html-to-image')
  const restore = expandForCapture(element)
  try {
    const dataUrl = await toPng(element, { pixelRatio: 2, backgroundColor: '#ffffff', filter: exportFilter })
    downloadDataUrl(dataUrl, filename)
  } finally {
    restore()
  }
}

/**
 * DOM 요소를 캡처하여 PDF로 저장 (html-to-image + jsPDF)
 * - 한글 깨짐 방지: jsPDF text() 대신 임시 DOM 헤더를 삽입하여 브라우저가 렌더링
 * - 스크롤 영역 전체 캡처: overflow 임시 확장
 * - 이미지가 한 페이지를 초과하면 자동 분할 (멀티페이지)
 * @param {HTMLElement} element - 캡처 대상 DOM
 * @param {string} title - PDF 제목
 * @param {string} filename - 저장 파일명
 */
export async function exportElementPdf(element, title, filename) {
  const { toPng } = await import('html-to-image')
  const { default: jsPDF } = await import('jspdf')

  // 1. 임시 헤더 DOM 삽입 (한글 깨짐 방지 — 브라우저가 직접 렌더링)
  const headerDiv = document.createElement('div')
  headerDiv.className = 'export-exclude-restore'
  headerDiv.style.cssText = 'display:flex;justify-content:space-between;align-items:center;padding:12px 4px 10px;margin-bottom:12px;border-bottom:2px solid #e0e0e0;'
  headerDiv.innerHTML = `<span style="font-size:18px;font-weight:700;color:#333;">${title}</span><span style="font-size:12px;color:#999;">${new Date().toLocaleString('ko-KR')}</span>`
  element.insertBefore(headerDiv, element.firstChild)

  // 2. 스크롤 영역 확장 (화면에 보이지 않는 위젯도 캡처)
  const restore = expandForCapture(element)

  try {
    // 3. 원본 DOM 직접 캡처 (Canvas 포함, export-exclude 제외)
    const dataUrl = await toPng(element, { pixelRatio: 2, backgroundColor: '#ffffff', filter: exportFilter })

    const img = new Image()
    img.src = dataUrl
    await new Promise((resolve) => { img.onload = resolve })

    // 4. PDF 생성 (가로 방향, 멀티페이지 지원)
    const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
    const pageW = pdf.internal.pageSize.getWidth()
    const pageH = pdf.internal.pageSize.getHeight()
    const margin = 10
    const availW = pageW - margin * 2
    const availH = pageH - margin * 2

    // 이미지를 페이지 너비에 맞추고, 높이가 초과하면 분할
    const scale = availW / img.width
    const scaledH = img.height * scale
    const totalPages = Math.ceil(scaledH / availH)

    // Canvas 하나를 재사용하여 메모리 누수 방지
    const canvas = document.createElement('canvas')
    canvas.width = img.width
    const ctx = canvas.getContext('2d')

    for (let page = 0; page < totalPages; page++) {
      if (page > 0) pdf.addPage()
      const srcY = (page * availH / scale)
      const srcH = Math.min(availH / scale, img.height - srcY)
      canvas.height = srcH
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.drawImage(img, 0, srcY, img.width, srcH, 0, 0, img.width, srcH)
      const pageDataUrl = canvas.toDataURL('image/png')
      pdf.addImage(pageDataUrl, 'PNG', margin, margin, availW, srcH * scale)
    }

    // Canvas 참조 정리
    canvas.width = 0
    canvas.height = 0

    pdf.save(filename)
  } finally {
    element.removeChild(headerDiv)
    restore()
  }
}
