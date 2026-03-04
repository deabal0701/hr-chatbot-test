/**
 * 트리 유틸리티 함수
 * flat↔tree 변환, 필터링 등 트리 데이터 처리 공통 로직
 */

/**
 * flat 리스트 → tree 구조 변환
 * @param {Array} items - flat 배열
 * @param {Object} options - { idKey, parentKey }
 */
export function buildTree(items, { idKey = 'dept_id', parentKey = 'parent_dept_id' } = {}) {
  if (!items.length) return []
  const map = {}
  const roots = []
  for (const d of items) {
    map[d[idKey]] = { ...d, children: [] }
  }
  for (const d of items) {
    if (d[parentKey] && map[d[parentKey]]) {
      map[d[parentKey]].children.push(map[d[idKey]])
    } else {
      roots.push(map[d[idKey]])
    }
  }
  return roots
}

/**
 * tree 구조 → flat 배열 변환
 * @param {Array} items - tree 배열
 */
export function flattenTree(items) {
  const result = []
  const walk = (list) => {
    for (const item of list) {
      result.push(item)
      if (item.children?.length) walk(item.children)
    }
  }
  walk(items)
  return result
}

/**
 * 트리에서 특정 노드 제외 (+ 선택적 필터)
 * @param {Array} items - tree 배열
 * @param {*} excludeId - 제외할 노드 ID
 * @param {Object} options - { idKey, filterFn }
 */
export function filterTree(items, excludeId, { idKey = 'dept_id', filterFn = null } = {}) {
  return items
    .filter(item => item[idKey] !== excludeId && (!filterFn || filterFn(item)))
    .map(item => ({
      ...item,
      children: item.children?.length ? filterTree(item.children, excludeId, { idKey, filterFn }) : []
    }))
}
