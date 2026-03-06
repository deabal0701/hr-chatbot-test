# Personal Dashboard 위젯 등록/수정 일관성 개선 계획

## 목표
3개 모달(SaveToDashboardModal, AddWidgetModal, WidgetEditModal)의 위젯 설정 UI와 데이터 구조를 일관성 있게 통일

## 변경 파일 목록

### 1. AddWidgetModal.vue (대폭 수정)
**현재 문제**: column_aliases 누락, pieTopN UI 없음, 차트 미리보기 없음, 에러 핸들링 없음, 기본 타입 bar, rows 제한 없음

**변경 내용**:
- 기본 widgetType: `'bar'` → `'table'`로 변경
- 대시보드 선택 UI 제거 (현재 대시보드에 추가)
- 위젯 설정 영역을 SaveToDashboardModal과 동일하게 통일:
  - 차트 설정: Pie 라벨 `'항목'` → `'항목 (Label)'`, `'값'` → `'값 (Value)'`
  - Pie 표시 개수(pieTopN) UI 추가
  - 컬럼 표시명(column_aliases) Collapse 섹션 추가
  - WidgetChart/WidgetKpi 미리보기 추가
- handleSave에 try-catch 에러 핸들링 추가
- cached_data.rows: `slice(0, 500)` 행 제한 추가
- cached_data.row_count: 원본 전체 건수 사용
- chart_config에 column_aliases 포함

### 2. WidgetEditModal.vue (소폭 수정)
- handleSave에 try-catch 에러 핸들링 추가
- previewData 전송 시 rows `slice(0, 500)` 제한 추가

### 3. SaveToDashboardModal.vue (변경 없음)
- 이미 가장 완전한 구현이므로 기준점으로 사용

## 구현 순서
1. AddWidgetModal.vue 수정
2. WidgetEditModal.vue 수정
3. 프론트엔드 빌드 테스트
