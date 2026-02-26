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
 * DOM 요소를 PNG로 캡처하여 다운로드 (html-to-image)
 */
export async function captureElementPng(element, filename) {
  const { toPng } = await import('html-to-image')
  const dataUrl = await toPng(element, { pixelRatio: 2, backgroundColor: '#ffffff' })
  downloadDataUrl(dataUrl, filename)
}

/**
 * DOM 요소를 캡처하여 PDF로 저장 (html-to-image + jsPDF)
 * 헤더(제목+시각)를 임시 DOM으로 생성하여 함께 캡처 → 한글 깨짐 방지
 * @param {HTMLElement} element - 캡처 대상 DOM
 * @param {string} title - PDF 제목
 * @param {string} filename - 저장 파일명
 */
export async function exportElementPdf(element, title, filename) {
  const { toPng } = await import('html-to-image')
  const { default: jsPDF } = await import('jspdf')

  // 임시 래퍼: 헤더(제목+시각) + 원본 콘텐츠를 하나의 DOM으로 묶어 캡처
  const wrapper = document.createElement('div')
  wrapper.style.cssText = 'position:absolute;left:-9999px;top:0;background:#fff;padding:20px;'
  wrapper.style.width = `${element.scrollWidth}px`

  const header = document.createElement('div')
  header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #e0e0e0;'
  header.innerHTML = `<span style="font-size:18px;font-weight:700;color:#333;">${title}</span><span style="font-size:12px;color:#888;">${new Date().toLocaleString('ko-KR')}</span>`

  const clone = element.cloneNode(true)
  wrapper.appendChild(header)
  wrapper.appendChild(clone)
  document.body.appendChild(wrapper)

  try {
    const dataUrl = await toPng(wrapper, { pixelRatio: 2, backgroundColor: '#ffffff' })

    const img = new Image()
    img.src = dataUrl
    await new Promise((resolve) => { img.onload = resolve })

    const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
    const pageW = pdf.internal.pageSize.getWidth()
    const pageH = pdf.internal.pageSize.getHeight()
    const margin = 10
    const availW = pageW - margin * 2
    const availH = pageH - margin * 2
    const ratio = Math.min(availW / img.width, availH / img.height)
    const imgW = img.width * ratio
    const imgH = img.height * ratio

    pdf.addImage(dataUrl, 'PNG', margin, margin, imgW, imgH)
    pdf.save(filename)
  } finally {
    document.body.removeChild(wrapper)
  }
}
