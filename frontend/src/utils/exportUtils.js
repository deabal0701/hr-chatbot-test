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
 * 원본 DOM을 직접 캡처 (cloneNode는 Canvas 픽셀 데이터를 복사하지 못함)
 * 헤더(제목+시각)는 jsPDF 텍스트로 직접 추가
 * @param {HTMLElement} element - 캡처 대상 DOM
 * @param {string} title - PDF 제목
 * @param {string} filename - 저장 파일명
 */
export async function exportElementPdf(element, title, filename) {
  const { toPng } = await import('html-to-image')
  const { default: jsPDF } = await import('jspdf')

  // 원본 DOM 직접 캡처 (Canvas 요소 포함)
  const dataUrl = await toPng(element, { pixelRatio: 2, backgroundColor: '#ffffff' })

  const img = new Image()
  img.src = dataUrl
  await new Promise((resolve) => { img.onload = resolve })

  // PDF 방향 자동 판단 (가로/세로)
  const orientation = img.width > img.height ? 'landscape' : 'portrait'
  const pdf = new jsPDF({ orientation, unit: 'mm', format: 'a4' })
  const pageW = pdf.internal.pageSize.getWidth()
  const pageH = pdf.internal.pageSize.getHeight()
  const margin = 10
  const headerH = 12

  // 헤더: 제목 + 시각
  pdf.setFontSize(14)
  pdf.setTextColor(51, 51, 51)
  pdf.text(title, margin, margin + 6)
  pdf.setFontSize(9)
  pdf.setTextColor(136, 136, 136)
  pdf.text(new Date().toLocaleString('ko-KR'), pageW - margin, margin + 6, { align: 'right' })
  pdf.setDrawColor(224, 224, 224)
  pdf.line(margin, margin + headerH - 2, pageW - margin, margin + headerH - 2)

  // 이미지 배치 (헤더 아래)
  const availW = pageW - margin * 2
  const availH = pageH - margin - (margin + headerH)
  const ratio = Math.min(availW / img.width, availH / img.height)
  const imgW = img.width * ratio
  const imgH = img.height * ratio

  pdf.addImage(dataUrl, 'PNG', margin, margin + headerH, imgW, imgH)
  pdf.save(filename)
}
