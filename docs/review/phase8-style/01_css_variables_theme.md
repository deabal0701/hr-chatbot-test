# Phase 8-1: CSS 변수 & 테마 시스템

## 이 문서의 목적

MUREUM이 **라이트/다크 모드**를 어떻게 구현하는지,
CSS 변수(`--xxx`) 기반 테마 시스템의 구조를 설명합니다.

---

## 비유: 방의 조명 모드

```
라이트 모드 = 낮 모드 (밝은 벽지, 진한 글자)
다크 모드   = 밤 모드 (어두운 벽지, 밝은 글자)

조명 스위치를 누르면:
  → 벽지 색상이 바뀌고 (배경)
  → 글자 색상이 바뀌고 (텍스트)
  → 가구 색상이 바뀜  (컴포넌트)
  → 하지만 가구의 위치는 변하지 않음 (레이아웃 동일)
```

---

## 1. CSS 변수란?

CSS 변수(Custom Properties)는 **값에 이름을 붙여** 재사용하는 기능입니다:

```css
/* 변수 선언 */
:root {
  --color-primary: #409eff;
}

/* 변수 사용 */
.button {
  background-color: var(--color-primary);
}
```

**장점**: 한 곳에서 값을 바꾸면 **모든 곳**이 동시에 변합니다.

---

## 2. _variables.scss 전체 구조

`_variables.scss`(302줄)는 4개 영역으로 나뉩니다:

```
┌─────────────────────────────────────────────┐
│  _variables.scss (302줄)                     │
│                                             │
│  ① :root { ... }              (1~86줄)      │
│     라이트 테마 CSS 변수 55개                 │
│                                             │
│  ② [data-theme="dark"] { ... } (89~166줄)   │
│     다크 테마 CSS 변수 55개 (같은 이름, 다른 값)│
│                                             │
│  ③ User Chat Sidebar 변수     (168~186줄)   │
│     :root + [data-theme="dark"] 쌍           │
│                                             │
│  ④ Dashboard 테마 변수        (188~296줄)   │
│     .dashboard-light / .dashboard-dark       │
│     + Element Plus --el-* 오버라이드         │
│                                             │
│  ⑤ SCSS 변수 ($xxx)           (298~302줄)   │
│     $sidebar-width, $header-height 등        │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 3. 라이트/다크 테마 전환 원리

### 핵심 개념

```
HTML 태그의 속성이 바뀌면 → CSS 변수의 값이 바뀜 → 화면 전체가 변함

<html>                          ← 속성 없음 → :root 변수 적용 (라이트)
<html data-theme="dark">        ← 속성 있음 → [data-theme="dark"] 변수 적용 (다크)
```

### 전환 흐름

```
사용자가 테마 토글 클릭
     │
     ▼
JavaScript:
  document.documentElement.setAttribute('data-theme', 'dark')
     │
     ▼
CSS 변수가 자동 전환:
  --bg-color: #f5f7fa  →  --bg-color: #1a1a1a
  --text-color-primary: #303133  →  --text-color-primary: #e5e5e5
     │
     ▼
var(--bg-color)를 사용하는 모든 요소가 자동으로 색상 변경
```

### 라이트 → 다크 비교표

| 변수 | 라이트 | 다크 | 용도 |
|------|--------|------|------|
| `--bg-color` | `#f5f7fa` (연한 회색) | `#1a1a1a` (거의 검정) | 페이지 배경 |
| `--bg-color-card` | `#ffffff` (흰색) | `#1f1f1f` (어두운 회색) | 카드 배경 |
| `--bg-color-input` | `#ffffff` | `#2c2c2c` | 입력창 배경 |
| `--text-color-primary` | `#303133` (진한 회색) | `#e5e5e5` (밝은 회색) | 주 텍스트 |
| `--text-color-secondary` | `#909399` | `#8c8c8c` | 보조 텍스트 |
| `--border-color` | `#dcdfe6` | `#4a4a4a` | 테두리 |
| `--box-shadow` | `rgba(0,0,0,0.1)` | `rgba(0,0,0,0.3)` | 그림자 |

### 패턴: 라이트는 밝은→어두운, 다크는 어두운→밝은

```
라이트 모드:
  배경 ■■■■■□□□□□ 글자     밝은 배경에 진한 글자

다크 모드:
  배경 □□□□□■■■■■ 글자     어두운 배경에 밝은 글자
```

---

## 4. CSS 변수 카테고리 상세

### 4-1. 주요 색상 (Primary Colors)

```scss
:root {
  --color-primary: #409eff;    // 파란색 (액센트)
  --color-success: #67c23a;    // 초록색 (성공)
  --color-warning: #e6a23c;    // 주황색 (경고)
  --color-danger: #f56c6c;     // 빨간색 (위험)
  --color-info: #909399;       // 회색 (정보)
}
```

> 이 5가지 색상은 라이트/다크 모드에서 **동일합니다**.
> Element Plus의 상태 색상과 일치시킨 것입니다.

### 4-2. 아이콘 색상 (Monochrome)

```scss
:root {
  --icon-bg: #f0f0f0;         // 아이콘 배경 (밝은 회색)
  --icon-color: #333333;      // 아이콘 전경 (진한 회색)
}

[data-theme="dark"] {
  --icon-bg: #333333;         // 아이콘 배경 (어두운 회색)
  --icon-color: #ffffff;      // 아이콘 전경 (흰색)
}
```

### 4-3. 채팅 전용 변수

```scss
:root {
  --chat-bubble-user-bg: #f0f0f0;           // 사용자 버블 (연한 회색)
  --chat-bubble-assistant-bg: #ffffff;       // AI 버블 (흰색)
  --chat-input-bg: #ffffff;                  // 입력창 배경
}

[data-theme="dark"] {
  --chat-bubble-user-bg: #3a3a3a;           // 사용자 버블 (어두운 회색)
  --chat-bubble-assistant-bg: #2c2c2c;       // AI 버블 (더 어두운 회색)
  --chat-input-bg: #1f1f1f;                  // 입력창 배경
}
```

### 4-4. 테마 전환 애니메이션

```scss
:root {
  --theme-transition: background-color 0.3s ease,
                      color 0.3s ease,
                      border-color 0.3s ease;
}
```

> 이 변수를 `transition` 속성에 사용하면 테마 전환 시
> 색상이 **0.3초 동안 부드럽게** 변합니다.

---

## 5. User Chat Sidebar 변수

사용자 채팅 화면의 사이드바는 **별도 변수 세트**를 가집니다 (ChatGPT 스타일):

```scss
:root {
  --user-sidebar-width: 260px;
  --user-sidebar-bg: #f7f7f8;
  --user-sidebar-text: #202020;
  --user-sidebar-hover-bg: #ececec;
}

[data-theme="dark"] {
  --user-sidebar-bg: #171717;
  --user-sidebar-text: #ececec;
  --user-sidebar-hover-bg: #212121;
}
```

```
왜 별도 변수를 쓰나?

  Admin 사이드바:   --sidebar-bg: #304156  (남색 계열)
  User Chat 사이드바: --user-sidebar-bg: #f7f7f8  (회색 계열)

  → 디자인 컨셉이 다르므로 변수도 분리
```

---

## 6. 대시보드 테마 격리

대시보드는 **특수한 요구사항**이 있습니다:

```
문제:
  앱 전체는 다크모드인데, 대시보드만 라이트모드로 보여주고 싶다면?
  또는 앱은 라이트인데 대시보드만 다크로 보여주고 싶다면?

해결:
  .dashboard-light / .dashboard-dark 클래스로 격리!
```

### 격리 원리

```
<html>                                       ← 앱 전체 테마
  <body>
    <div class="dashboard-light">            ← 대시보드 자체 테마
      여기 안의 모든 Element Plus 컴포넌트는
      .dashboard-light의 --el-* 변수를 따름
    </div>
```

### Element Plus 변수 오버라이드

대시보드 라이트 클래스는 Element Plus의 내부 변수까지 **강제 지정**합니다:

```scss
.dashboard-light {
  // 커스텀 변수
  --dashboard-bg: #f0f2f5;
  --dashboard-card: #ffffff;

  // Element Plus 변수 오버라이드!
  --el-bg-color: #ffffff;
  --el-text-color-primary: #303133;
  --el-border-color: #dcdfe6;
  --el-fill-color-blank: #ffffff;
  // ... 15개 이상
}
```

```
왜 --el-* 변수를 오버라이드하나?

  Element Plus는 내부적으로 --el-bg-color 같은 변수를 사용합니다.
  앱이 다크모드일 때 html.dark 클래스가 추가되면
  Element Plus도 자동으로 다크가 됩니다.

  그런데 대시보드만 라이트로 유지하려면?
  → .dashboard-light 안에서 --el-* 변수를 라이트 값으로 덮어씁니다!
```

### 버튼 변수까지 격리

```scss
.dashboard-light .el-button {
  --el-button-text-color: #606266;
  --el-button-bg-color: #ffffff;
  --el-button-hover-text-color: #409eff;
  // ...
}

.dashboard-dark .el-button {
  --el-button-text-color: #cfd3dc;
  --el-button-bg-color: #1f1f1f;
  --el-button-hover-text-color: #409eff;
  // ...
}
```

---

## 7. Element Plus 다크모드 오버라이드

`_element-dark.scss`(376줄)은 `[data-theme="dark"]` 안에서
Element Plus의 **모든 주요 컴포넌트**를 다크 테마에 맞게 스타일링합니다.

### 오버라이드 대상 컴포넌트 (21종)

```
[data-theme="dark"] {
  .el-card         → 카드 배경/테두리
  .el-table        → 테이블 배경/헤더/호버/테두리
  .el-input        → 입력창 배경/테두리/포커스
  .el-textarea     → 텍스트영역
  .el-select       → 셀렉트박스
  .el-button       → 버튼 배경/테두리/호버
  .el-dialog       → 모달 배경/제목
  .el-descriptions → 상세정보 라벨/내용
  .el-collapse     → 접기/펼치기
  .el-form         → 폼 라벨
  .el-divider      → 구분선
  .el-pagination   → 페이지네이션
  .el-message-box  → 확인 대화상자
  .el-radio-button → 라디오 버튼
  .el-radio        → 라디오
  .el-tree         → 트리 메뉴
  .el-select-dropdown → 드롭다운
  .el-input-number → 숫자 입력
  .el-empty        → 빈 상태
  .el-tag          → 태그
  .el-loading      → 로딩 오버레이
  .el-switch       → 토글 스위치
  .el-message      → 알림 메시지
}
```

### 오버라이드 패턴

```scss
// 패턴: 컴포넌트 선택자 + CSS 변수 적용
[data-theme="dark"] {
  .el-card {
    background-color: var(--bg-color-card);    // #1f1f1f
    border-color: var(--border-color);          // #4a4a4a
  }
}
```

> **핵심**: 하드코딩 대신 CSS 변수를 사용하므로,
> `[data-theme="dark"]` 블록에서 선언한 변수 값이 자동 적용됩니다.

---

## 8. 텔레포트 컴포넌트 문제

Element Plus의 일부 컴포넌트(Dialog, Select 드롭다운)는
**`<body>` 하위에 텔레포트**됩니다:

```
문제:

<html data-theme="dark">
  <body>
    <div id="app">
      [data-theme="dark"] 스코프 안 ✅
    </div>

    <div class="el-dialog">          ← body 직속!
      [data-theme="dark"] 스코프 밖 ❌  다크 스타일 미적용!
    </div>
  </body>
</html>
```

### 해결: 직접 클래스 적용

```scss
// _element-dark.scss 하단 (303~376줄)
.el-dialog.dashboard-dark {
  // 변수를 직접 재선언
  --bg-color-card: #1f1f1f;
  --text-color-primary: #e5e5e5;
  // ...

  // 내부 컴포넌트 스타일도 직접 지정
  .el-dialog__title { color: var(--text-color-primary); }
  .el-input__wrapper { background-color: var(--bg-color-input); }
  // ...
}
```

```
텔레포트된 Dialog에는 Vue에서 직접 클래스를 부여:

  <el-dialog :class="isDark ? 'dashboard-dark' : ''" ...>
```

---

## 9. 드롭다운 다크 스타일

`_dropdown.scss`(77줄)은 사용자 채팅 화면의 모드 선택 드롭다운용:

```scss
.dark-dropdown-popper {
  background-color: var(--bg-color-card) !important;
  border-radius: 12px !important;

  .el-dropdown-menu__item {
    border-radius: 8px !important;

    &.is-active {
      color: var(--color-primary) !important;
    }
  }
}
```

> `!important`가 많이 사용된 이유:
> 텔레포트된 팝업이므로 Element Plus의 기본 스타일을 확실하게 덮어야 합니다.

---

## 10. SCSS 변수 vs CSS 변수

`_variables.scss` 하단에는 **SCSS 변수**(`$xxx`)도 있습니다:

```scss
$sidebar-width: 220px;
$header-height: 60px;
$user-sidebar-width: 260px;
```

| 구분 | CSS 변수 `var(--xxx)` | SCSS 변수 `$xxx` |
|------|----------------------|-------------------|
| 런타임 변경 | 가능 (JS로 변경) | 불가 (빌드 시 고정) |
| 테마 전환 | ✅ 적합 | ❌ 부적합 |
| 레이아웃 크기 | △ 가능하나 불편 | ✅ 적합 |
| 계산 | `calc()` 필요 | 직접 연산 가능 |

```
색상처럼 동적으로 바뀌는 값 → CSS 변수 (--color-primary)
레이아웃처럼 고정된 크기    → SCSS 변수 ($sidebar-width)
```

---

## 11. 초기화 스타일 (_reset.scss)

`_reset.scss`(38줄)은 브라우저 기본 스타일을 초기화합니다:

```scss
* {
  box-sizing: border-box;    // 패딩/테두리가 크기에 포함
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: fonts.$font-family-sans;
  font-size: 14px;
  background-color: var(--bg-color-page);    // ← CSS 변수!
  color: var(--text-color-primary);           // ← CSS 변수!
  transition: var(--theme-transition);        // ← 부드러운 전환!
}
```

> `body`에 `var(--bg-color-page)`와 `transition`이 있으므로,
> 테마 전환 시 **페이지 전체 배경이 0.3초에 걸쳐 부드럽게** 변합니다.

### 스크롤바 스타일

```scss
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-thumb {
  background-color: var(--scrollbar-thumb);    // 라이트: #c0c4cc, 다크: #4a4a4a
  border-radius: 3px;
}

::-webkit-scrollbar-track {
  background-color: var(--scrollbar-track);    // 라이트: #f5f7fa, 다크: #1a1a1a
}
```

> 스크롤바도 CSS 변수를 사용하므로 다크모드에서 자동 변환됩니다.

---

## 리뷰 체크리스트

- [ ] 모든 CSS 변수가 `:root`(라이트)와 `[data-theme="dark"]`(다크)에 쌍으로 존재하는가?
- [ ] 색상 하드코딩(`#ffffff` 등)이 컴포넌트 코드에 없는가? (변수 사용 확인)
- [ ] `transition: var(--theme-transition)`으로 전환 애니메이션이 적용되는가?
- [ ] 대시보드 테마 격리가 `--el-*` 변수 오버라이드로 완전한가?
- [ ] 텔레포트 컴포넌트(Dialog)에 다크 클래스가 직접 부여되는가?
- [ ] SCSS 변수(`$xxx`)는 레이아웃 크기에만, CSS 변수(`--xxx`)는 색상에 사용되는가?
