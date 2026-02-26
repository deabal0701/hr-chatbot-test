/**
 * 차트 옵션 생성 Composable
 * ChartBuilder.vue와 Dashboard WidgetChart.vue에서 공유
 */

/**
 * 테마 색상 가져오기
 */
export function getThemeColor(varName) {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || '#333'
}

/**
 * 컬럼 타입 감지 (숫자 vs 텍스트)
 */
export function detectColumnTypes(columns, rows) {
  if (!rows || rows.length === 0) return { numeric: [], text: [] }

  const sampleSize = Math.min(rows.length, 10)
  const numeric = []
  const text = []

  for (const col of columns) {
    let numCount = 0
    for (let i = 0; i < sampleSize; i++) {
      const val = rows[i][col]
      if (val !== null && val !== undefined && val !== '' && !isNaN(Number(val))) {
        numCount++
      }
    }
    if (numCount > sampleSize * 0.5) {
      numeric.push(col)
    } else {
      text.push(col)
    }
  }

  return { numeric, text }
}

// 차트 컬러 팔레트 프리셋
export const CHART_PALETTES = {
  default: {
    label: '기본',
    colors: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4', '#ea7ccc', '#5ab1ef']
  },
  vivid: {
    label: '비비드',
    colors: ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#e84393', '#00b894', '#6c5ce7']
  },
  pastel: {
    label: '파스텔',
    colors: ['#a1c4fd', '#c2e9fb', '#fbc2eb', '#f6d365', '#a8edea', '#fed6e3', '#d4fc79', '#fda085', '#c3cfe2', '#e0c3fc']
  },
  warm: {
    label: '따뜻한',
    colors: ['#ff6b6b', '#ffa502', '#ff7f50', '#ff6348', '#eccc68', '#ff9ff3', '#f368e0', '#ff9f43', '#ee5a24', '#e55039']
  },
  cool: {
    label: '시원한',
    colors: ['#0984e3', '#00cec9', '#6c5ce7', '#74b9ff', '#55efc4', '#81ecec', '#a29bfe', '#00b894', '#0abde3', '#48dbfb']
  },
  earth: {
    label: '어스톤',
    colors: ['#8b6914', '#6b8e23', '#cd853f', '#8fbc8f', '#daa520', '#bc8f8f', '#a0522d', '#708238', '#c19a6b', '#967969']
  }
}

const DEFAULT_COLORS = CHART_PALETTES.default.colors

/**
 * 차트 옵션 생성
 */
export function buildChartOption({ chartType, xColumn, yColumns, rows, pieTopN = 10, whiteBg = false, darkMode = null, colorPalette = null }) {
  let textColor, subTextColor, borderColor
  if (darkMode === true) {
    textColor = '#e5e5e5'; subTextColor = '#8c8c8c'; borderColor = '#303030'
  } else if (darkMode === false || whiteBg) {
    textColor = '#333333'; subTextColor = '#666666'; borderColor = '#dcdcdc'
  } else {
    textColor = getThemeColor('--text-color-primary')
    subTextColor = getThemeColor('--text-color-secondary')
    borderColor = getThemeColor('--border-color-lighter')
  }

  const paletteColors = (colorPalette && CHART_PALETTES[colorPalette]?.colors) || DEFAULT_COLORS
  const baseStyle = {
    color: paletteColors,
    textStyle: { color: textColor },
    backgroundColor: whiteBg ? '#ffffff' : 'transparent'
  }

  // hbar → bar (가로) 변환
  const isHorizontal = chartType === 'hbar'
  const resolvedType = isHorizontal ? 'bar' : chartType

  if (resolvedType === 'pie') {
    return buildPieOption({ xColumn, yColumns, rows, pieTopN, baseStyle, textColor, subTextColor })
  } else if (resolvedType === 'scatter') {
    return buildScatterOption({ xColumn, yColumns, rows, baseStyle, subTextColor, borderColor })
  } else {
    return buildAxisOption({ chartType: resolvedType, xColumn, yColumns, rows, baseStyle, subTextColor, borderColor, isHorizontal })
  }
}

function buildPieOption({ xColumn, yColumns, rows, pieTopN, baseStyle, textColor, subTextColor }) {
  const yCol = Array.isArray(yColumns) ? yColumns[0] : yColumns

  let pieData = rows
    .map(r => ({
      name: String(r[xColumn] ?? ''),
      value: Number(r[yCol]) || 0
    }))
    .sort((a, b) => b.value - a.value)

  if (pieTopN > 0 && pieData.length > pieTopN) {
    const topItems = pieData.slice(0, pieTopN)
    const otherSum = pieData.slice(pieTopN).reduce((sum, d) => sum + d.value, 0)
    const otherCount = pieData.length - pieTopN
    topItems.push({ name: `기타 (${otherCount}건)`, value: otherSum })
    pieData = topItems
  }

  const totalValue = pieData.reduce((sum, d) => sum + d.value, 0)

  return {
    ...baseStyle,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      bottom: 0,
      pageIconColor: subTextColor,
      pageTextStyle: { color: subTextColor },
      textStyle: { color: subTextColor, fontSize: 11 }
    },
    series: [{
      type: 'pie',
      radius: ['35%', '65%'],
      center: ['50%', '42%'],
      label: {
        color: textColor,
        fontSize: 11,
        formatter: (params) => {
          const pct = totalValue > 0 ? ((params.value / totalValue) * 100) : 0
          return pct >= 3 ? `${params.name}` : ''
        }
      },
      labelLine: { show: true, length: 10, length2: 8 },
      emphasis: {
        label: { show: true, fontSize: 13, fontWeight: 'bold' },
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.3)' }
      },
      data: pieData
    }]
  }
}

function buildScatterOption({ xColumn, yColumns, rows, baseStyle, subTextColor, borderColor }) {
  const yCols = Array.isArray(yColumns) ? yColumns : [yColumns]
  return {
    ...baseStyle,
    tooltip: { trigger: 'item', formatter: (p) => `${p.seriesName}<br/>${xColumn}: ${p.value[0]}<br/>${p.seriesName}: ${p.value[1]}` },
    legend: { data: yCols, bottom: 0, textStyle: { color: subTextColor, fontSize: 12 } },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
    xAxis: {
      type: 'value',
      name: xColumn,
      nameTextStyle: { color: subTextColor, fontSize: 11 },
      axisLabel: { color: subTextColor, fontSize: 11 },
      axisLine: { lineStyle: { color: borderColor } },
      splitLine: { lineStyle: { color: borderColor, type: 'dashed', opacity: 0.5 } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: subTextColor, fontSize: 11 },
      axisLine: { lineStyle: { color: borderColor } },
      splitLine: { lineStyle: { color: borderColor, type: 'dashed', opacity: 0.5 } }
    },
    series: yCols.map(col => ({
      name: col,
      type: 'scatter',
      data: rows.map(r => [Number(r[xColumn]) || 0, Number(r[col]) || 0]),
      symbolSize: 10
    }))
  }
}

function buildAxisOption({ chartType, xColumn, yColumns, rows, baseStyle, subTextColor, borderColor, isHorizontal = false }) {
  const yCols = Array.isArray(yColumns) ? yColumns : [yColumns]
  const xData = rows.map(r => String(r[xColumn] ?? ''))
  const needZoom = xData.length > 30

  return {
    ...baseStyle,
    tooltip: { trigger: 'axis' },
    legend: {
      data: yCols,
      bottom: needZoom ? 30 : 0,
      textStyle: { color: subTextColor, fontSize: 12 }
    },
    grid: { left: '3%', right: '4%', bottom: needZoom ? '20%' : '15%', top: '10%', containLabel: true },
    ...(needZoom ? {
      dataZoom: [{
        type: 'slider',
        bottom: 5,
        height: 20,
        start: 0,
        end: Math.min(100, (30 / xData.length) * 100),
        textStyle: { color: subTextColor }
      }]
    } : {}),
    xAxis: isHorizontal ? {
      type: 'value',
      axisLabel: { color: subTextColor, fontSize: 11 },
      axisLine: { lineStyle: { color: borderColor } },
      splitLine: { lineStyle: { color: borderColor, type: 'dashed', opacity: 0.5 } }
    } : {
      type: 'category',
      data: xData,
      axisLabel: {
        color: subTextColor,
        fontSize: 11,
        rotate: xData.length > 15 ? 90 : xData.length > 8 ? 45 : 0,
        interval: 0
      },
      axisLine: { lineStyle: { color: borderColor } },
      axisTick: { lineStyle: { color: borderColor } }
    },
    yAxis: isHorizontal ? {
      type: 'category',
      data: xData,
      axisLabel: { color: subTextColor, fontSize: 11 },
      axisLine: { lineStyle: { color: borderColor } },
      axisTick: { lineStyle: { color: borderColor } }
    } : {
      type: 'value',
      axisLabel: { color: subTextColor, fontSize: 11 },
      axisLine: { lineStyle: { color: borderColor } },
      splitLine: { lineStyle: { color: borderColor, type: 'dashed', opacity: 0.5 } }
    },
    series: yCols.map((col, idx) => {
      const base = { name: col, type: chartType, data: rows.map(r => Number(r[col]) || 0) }
      if (chartType === 'bar') {
        base.barMaxWidth = 40
        base.itemStyle = isHorizontal ? { borderRadius: [0, 3, 3, 0] } : { borderRadius: [3, 3, 0, 0] }
      } else if (chartType === 'line') {
        base.smooth = true
        base.lineStyle = { width: 2.5 }
        base.areaStyle = { opacity: 0.08 }
        base.symbol = 'circle'
        base.symbolSize = 6
      }
      return base
    })
  }
}
