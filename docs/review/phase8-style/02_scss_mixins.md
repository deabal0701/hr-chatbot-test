# Phase 8-2: SCSS Mixins — 재사용 스타일 블록

## 이 문서의 목적

SCSS Mixin은 **반복되는 스타일을 함수처럼** 정의하고 재사용하는 기능입니다.
MUREUM에서 8개 mixin 파일에 **31개 mixin**이 정의되어 있으며,
컴포넌트들이 이를 `@include`로 가져다 씁니다.

---

## 비유: 가구 조립 설명서

```
Mixin = 가구 조립 설명서 (IKEA 매뉴얼)

  설명서 자체는 가구가 아닙니다.
  "이 설명서대로 조립하면 책상이 됩니다"라고 적혀 있을 뿐.

  @mixin stat-card { ... }     ← 설명서 (정의)
  @include mixins.stat-card;   ← 조립 시작 (사용)

  같은 설명서로 여러 방에 같은 가구를 둘 수 있고,
  파라미터를 바꾸면 크기나 색상을 조절할 수 있습니다.
```

---

## 1. Mixin 사용 패턴

### 기본 사용법

```scss
// ① 컴포넌트의 <style> 블록에서 mixin 가져오기
<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mixins;

.my-card {
  @include mixins.stat-card;    // ② mixin 포함
}
</style>
```

### 파라미터 있는 mixin

```scss
// 정의: 기본값이 있는 파라미터
@mixin md-table-styles($font-size: 13px, $cell-padding: 10px 14px) {
  :deep(.md-table) {
    font-size: $font-size;
    th, td { padding: $cell-padding; }
  }
}

// 사용: 기본값 사용
@include mixins.md-table-styles;

// 사용: 파라미터 커스텀
@include mixins.md-table-styles(12px, 8px 10px);
```

---

## 2. @forward 허브 (mixins/_index.scss)

```scss
// mixins/_index.scss (12줄)
@forward 'layout';       // stats-row
@forward 'cards';        // stat-card
@forward 'markdown';     // md-table-styles, copy-table-btn, ... (9개)
@forward 'chat';         // toggle-section-container, ... (6개)
@forward 'forms';        // settings-section, settings-actions
@forward 'animations';   // rotating-animation, ... (6개)
@forward 'chart';        // chart-builder-container, ... (5개)
@forward 'dashboard';    // chart-card, activity-list
```

```
@forward의 역할:

  컴포넌트 입장에서는 @use 'mixins' 한 줄로 31개 mixin을 모두 사용 가능.
  _index.scss가 8개 파일을 묶어서 하나의 "패키지"로 제공합니다.

  택배 = 8개 상자를 하나의 큰 박스로 합포장
```

---

## 3. :deep() 선택자

Vue의 `scoped` CSS에서 자식 컴포넌트의 스타일을 변경할 때 사용합니다:

```
문제:
  <style scoped>에서 작성한 CSS는 현재 컴포넌트에만 적용됩니다.
  v-html로 렌더링된 HTML이나 자식 컴포넌트의 내부 요소는 영향을 받지 않습니다.

해결:
  :deep(.클래스명)으로 "벽을 뚫고" 자식에게 스타일을 전달합니다.
```

```scss
// 마크다운 mixin에서 :deep() 사용 예
@mixin md-table-styles {
  :deep(.md-table) {          // ← v-html로 생성된 .md-table에 적용
    width: 100%;
    border-collapse: collapse;
  }
}
```

```
:deep()이 필요한 상황 (MUREUM):

  ChatMessage.vue
    └─ <div v-html="formattedContent">    ← 마크다운 파서가 생성한 HTML
         └─ <table class="md-table">       ← scoped CSS가 닿지 못함!
              └─ :deep(.md-table) 으로 해결
```

---

## 4. Mixin 파일별 상세

### 4-1. _markdown.scss (170줄, 9개 mixin)

마크다운 → HTML 렌더링 결과물의 스타일을 담당합니다.

```
┌─────────────────────────────────────────────────────┐
│  markdownParser.js가 생성하는 HTML                   │
│                                                     │
│  <div class="md-table-wrapper">                     │
│    <button class="copy-table-btn">...</button>      │
│    <div class="md-table-scroll">                    │
│      <table class="md-table">...</table>            │
│    </div>                                           │
│  </div>                                             │
│  <span class="md-h2">제목</span>                    │
│  <span class="md-list-item">• 항목</span>           │
│  <code>인라인코드</code>                             │
│  <pre><code>코드블록</code></pre>                    │
│  <strong>굵은글씨</strong>                           │
│  <hr class="md-hr">                                 │
│  <em>기울임</em>                                     │
│                                                     │
│  ↓ 각각에 대응하는 mixin ↓                           │
└─────────────────────────────────────────────────────┘
```

| Mixin | 대상 | 파라미터 | 설명 |
|-------|------|----------|------|
| `md-table-styles` | `.md-table-wrapper`, `.md-table` | `$font-size`, `$cell-padding`, `$margin`, `$border-radius` | 테이블 전체 |
| `copy-table-btn` | `.copy-table-btn` | `$size`, `$offset`, `$icon-size`, `$border-radius` | 테이블 복사 버튼 |
| `md-header-styles` | `.md-h2`, `.md-h3` | `$margin-top`, `$margin-bottom`, `$font-size` | 제목 |
| `md-list-styles` | `.md-list-item` | `$padding-left`, `$margin` | 리스트 |
| `inline-code-styles` | `code` | `$font-size`, `$padding`, `$border-radius`, `$font-family` | 인라인 코드 |
| `code-block-styles` | `pre` | `$padding`, `$border-radius` | 코드 블록 |
| `strong-styles` | `strong` | (없음) | 굵은 글씨 |
| `md-hr-styles` | `.md-hr` | `$margin` | 수평선 |
| `md-em-styles` | `em` | (없음) | 기울임 |

### 파라미터 패턴 예시

```scss
// 테이블 mixin 정의
@mixin md-table-styles(
  $font-size: 13px,           // 기본값 13px
  $cell-padding: 10px 14px,   // 기본값 10px 14px
  $margin: 16px,              // 기본값 16px
  $border-radius: 8px         // 기본값 8px
) {
  :deep(.md-table-wrapper) {
    margin: $margin 0;
    border-radius: $border-radius;
    border: 1px solid var(--border-color);    // CSS 변수 사용!
  }

  :deep(.md-table) {
    font-size: $font-size;
    th, td { padding: $cell-padding; }
    th { background-color: var(--bg-color-hover); }    // CSS 변수!
    tbody tr:hover { background-color: var(--bg-color-hover); }
  }
}
```

> **핵심**: 크기/간격은 **SCSS 파라미터**로, 색상은 **CSS 변수**로.
> 이 조합이 "파라미터로 크기 커스텀 + 테마로 색상 자동 전환"을 가능하게 합니다.

---

### 4-2. _animations.scss (77줄, 6개 mixin)

| Mixin | 효과 | 사용처 |
|-------|------|--------|
| `rotating-animation` | 무한 회전 (360°) | 로딩 아이콘 |
| `fade-in-animation($duration)` | 아래→위 페이드인 | 메시지 등장 |
| `typing-animation` | 점 3개 깜빡임 | AI 답변 대기 중 |
| `sidebar-slide-transition` | 좌→우 슬라이드 | 사이드바 열기/닫기 |
| `toggle-icon-rotate` | 180° 회전 | 접기/펼치기 화살표 |
| `sidebar-overlay-slide($width, $duration)` | 우→좌 오버레이 슬라이드 | 소스 상세 패널 |

### 애니메이션 동작 시각화

```
rotating-animation:
  ⟳ → ⟳ → ⟳ → ⟳  (1초마다 360° 무한 회전)

fade-in-animation:
  [   ] → [▒▒▒] → [███]  (아래에서 위로 올라오며 나타남)
   0%      50%     100%

typing-animation:
  ●○○ → ○●○ → ○○● → ●○○  (점 3개가 순서대로 깜빡임)

toggle-icon-rotate:
  ▽ → (0.3초) → △  (180° 부드럽게 회전)
```

### sidebar-overlay-slide 상세

```scss
@mixin sidebar-overlay-slide($width: 280px, $duration: 0.3s) {
  width: $width;
  transform: translateX(100%);    // 처음: 화면 오른쪽 밖
  opacity: 0;                     // 처음: 투명

  transition: transform $duration cubic-bezier(0.4, 0, 0.2, 1),
              opacity $duration cubic-bezier(0.4, 0, 0.2, 1);

  &.visible {
    transform: translateX(0);     // 활성화: 원래 위치
    opacity: 1;                   // 활성화: 불투명
    box-shadow: -4px 0 16px rgba(0, 0, 0, 0.1);
  }
}
```

```
cubic-bezier(0.4, 0, 0.2, 1) = Material Design 표준 이징

  느리게 시작 → 빠르게 → 느리게 끝
  자연스러운 물리 움직임 효과
```

---

### 4-3. _chat.scss (92줄, 6개 mixin)

| Mixin | 역할 | 파라미터 |
|-------|------|----------|
| `toggle-section-container` | 접기/펼치기 섹션 감싸기 | `$margin-top`, `$border-radius` |
| `toggle-button` | 접기/펼치기 트리거 버튼 | `$padding`, `$font-size` |
| `sql-code-block` | SQL 코드 표시 영역 | (없음) |
| `result-summary` | 결과 요약 텍스트 | (없음) |
| `more-rows` | "N건 더 있음" 텍스트 | (없음) |
| `mode-badge` | 모드 배지 (Agent/NL2SQL/RAG) | (없음) |

### toggle-button 구조

```scss
@mixin toggle-button($padding: 12px 16px, $font-size: 14px) {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;     // 좌: 라벨, 우: 화살표
  // ...

  .toggle-left {                       // 좌측 영역
    display: flex;
    align-items: center;
    gap: 10px;
    .el-icon { font-size: 18px; }
  }

  .toggle-icon {                       // 우측 화살표
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    &.expanded { transform: rotate(180deg); }
  }
}
```

```
토글 버튼 레이아웃:

  ┌──────────────────────────────────────┐
  │  📊 SQL 조회 결과 (5건)           ▽  │
  │  ←── .toggle-left ──→    .toggle-icon│
  └──────────────────────────────────────┘
       클릭하면 ▽ → △ 로 회전 (0.3초)
```

---

### 4-4. _cards.scss (44줄, 1개 mixin)

```scss
@mixin stat-card {
  display: flex;
  align-items: center;
  padding: 12px;
  background-color: var(--bg-color-card);
  box-shadow: var(--box-shadow);

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 8px;
    &.is-primary { background-color: var(--el-color-primary-light-9); }
    &.is-success { background-color: var(--el-color-success-light-9); }
  }

  .stat-content {
    .stat-value { font-size: 28px; font-weight: 600; }
    .stat-label { font-size: 14px; color: var(--text-color-secondary); }
  }
}
```

```
통계 카드 레이아웃:

  ┌─────────────────────────────┐
  │  ┌────┐                     │
  │  │ 📊 │  1,234             │
  │  │    │  총 요청 수          │
  │  └────┘                     │
  │  icon    value + label      │
  └─────────────────────────────┘
```

---

### 4-5. _chart.scss (76줄, 5개 mixin)

| Mixin | 역할 |
|-------|------|
| `chart-builder-container` | 차트 영역 전체 컨테이너 |
| `chart-toggle-btn` | "차트 보기" 토글 버튼 |
| `chart-config-panel` | 차트 설정 패널 (타입, X축, Y축 선택) |
| `chart-config-item` | 설정 항목 하나 (라벨 + 컨트롤) |
| `chart-render-area($height)` | 차트 렌더링 영역 (높이 파라미터) |

```
차트 빌더 구조:

  ┌──────────────────────────────────────────┐
  │  [📊 차트 보기]                ← toggle   │
  │                                          │
  │  ┌── config-panel ───────────────────┐   │
  │  │  차트타입: [Bar ▼]  X축: [부서 ▼] │   │
  │  │  Y축: [직원수 ▼]   [차트 생성]    │   │
  │  └──────────────────────────────────-┘   │
  │                                          │
  │  ┌── render-area (400px) ───────────┐   │
  │  │                                   │   │
  │  │         ███                       │   │
  │  │    ███  ███  ███                  │   │
  │  │    ███  ███  ███  ███             │   │
  │  │    A    B    C    D               │   │
  │  └───────────────────────────────────┘   │
  └──────────────────────────────────────────┘
```

---

### 4-6. _forms.scss (30줄, 2개 mixin)

```scss
@mixin settings-section {
  padding: 12px 0;
  h3 {
    display: flex; align-items: center; gap: 8px;
    margin: 0 0 12px; font-size: 16px;
  }
}

@mixin settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  border-top: 1px solid var(--border-color-light);
}
```

```
설정 섹션 레이아웃:

  ┌──────────────────────────────────────┐
  │  ⚙ LLM 설정                          │  ← settings-section h3
  │  ┌─────────────┐                     │
  │  │ 모델: GPT-4 │                     │
  │  │ 온도: 0.1   │                     │
  │  └─────────────┘                     │
  │  ──────────────────────────────────  │  ← border-top
  │                     [취소] [저장]     │  ← settings-actions
  └──────────────────────────────────────┘
```

---

### 4-7. _layout.scss (13줄, 1개 mixin)

```scss
@mixin stats-row {
  margin-bottom: 12px;
  .el-col { margin-bottom: 16px; }
}
```

> 가장 단순한 mixin. 통계 카드들이 나열되는 행의 간격을 정의합니다.

---

### 4-8. _dashboard.scss (29줄, 2개 mixin)

```scss
@mixin chart-card {
  @include content-card;    // ← modules/_chat-global.scss의 .content-card 재사용!
  min-height: 360px;
}

@mixin activity-list {
  list-style: none;
  padding: 0; margin: 0;
  li {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border-color-lighter);
    &:last-child { border-bottom: none; }
  }
}
```

> `chart-card`는 `content-card`를 **상속**합니다 (mixin 안에서 또 다른 스타일을 포함).

---

## 5. Mixin 사용 현황 요약

```
컴포넌트          →  사용하는 mixin 파일
─────────────────────────────────────────────
ChatMessage.vue   →  _markdown, _chat, _animations
UserChatMessage   →  _markdown, _chat, _animations
ChatInput.vue     →  (직접 스타일)
SourceCard.vue    →  _chat, _animations
ChartBuilder.vue  →  _chart
DashboardView     →  _dashboard, _cards, _layout
HistoryView       →  _cards, _layout
SettingsView      →  _forms
```

---

## 6. Mixin vs 전역 클래스 선택 기준

```
┌──────────────────────────────────────────────────────┐
│  언제 Mixin을 쓰나?                                   │
│                                                      │
│  ✅ 파라미터로 크기/간격을 조절해야 할 때               │
│  ✅ :deep()으로 자식 요소에 스타일을 전달해야 할 때      │
│  ✅ 여러 컴포넌트에서 구조는 같되 세부 값이 다를 때      │
│                                                      │
│  예: md-table-styles(12px) vs md-table-styles(14px)  │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  언제 전역 클래스를 쓰나?                              │
│                                                      │
│  ✅ 어디서든 동일한 스타일을 적용할 때                   │
│  ✅ 단순 유틸리티 (정렬, 여백, 색상)                    │
│  ✅ HTML에 클래스명만 붙여서 빠르게 적용                 │
│                                                      │
│  예: class="flex-center mt-20 text-muted"            │
└──────────────────────────────────────────────────────┘
```

---

## 리뷰 체크리스트

- [ ] 모든 mixin이 `mixins/_index.scss`에 `@forward`로 등록되어 있는가?
- [ ] 파라미터에 합리적인 기본값이 설정되어 있는가?
- [ ] 색상은 CSS 변수(`var(--xxx)`)로, 크기는 SCSS 파라미터로 분리되어 있는가?
- [ ] `:deep()` 선택자가 필요한 곳(v-html, 자식 컴포넌트)에 올바르게 사용되는가?
- [ ] 동일한 스타일이 중복 정의되지 않고 mixin으로 통합되어 있는가?
- [ ] mixin 이름이 역할을 명확하게 표현하는가?
