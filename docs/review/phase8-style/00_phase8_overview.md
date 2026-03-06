# Phase 8: 스타일 시스템 & 유틸리티 — 전체 개요

## 이 문서의 목적

Phase 8은 MUREUM 프론트엔드의 **시각적 기반**을 다루는 마지막 단계입니다.
화면에 보이는 모든 색상, 간격, 애니메이션, 다크모드, 그리고 마크다운 렌더링·파일 내보내기 같은 **JS 유틸리티**까지 포함합니다.

---

## 비유: 건물의 인테리어

```
Phase 1~7 = 건물의 구조 (골조, 배관, 전기)
Phase 8   = 인테리어 (벽지, 조명, 가구 배치, 편의시설)

┌─────────────────────────────────────┐
│  건물(앱)을 짓는 순서                │
│                                     │
│  ① 골조(컴포넌트) → 이미 완성        │
│  ② 배관(API/Store) → 이미 완성       │
│  ③ 벽지·조명(스타일) → Phase 8 ◀    │
│  ④ 편의시설(유틸리티) → Phase 8 ◀   │
└─────────────────────────────────────┘
```

- **벽지** = CSS 변수 (색상 테마)
- **조명 스위치** = 다크모드 토글
- **가구 배치** = SCSS Mixin (재사용 스타일)
- **편의시설** = JS 유틸리티 (마크다운 변환, 파일 내보내기, 포맷팅)

---

## SCSS 아키텍처 전체 구조

```
frontend/src/assets/styles/
│
├── _variables.scss          ← CSS 변수 정의 (테마 색상)
├── main.scss                ← 진입점 (모든 모듈을 조합)
│
├── modules/                 ← 전역 스타일 (모든 페이지에 적용)
│   ├── _reset.scss          ← 브라우저 기본값 초기화
│   ├── _utilities.scss      ← 유틸리티 클래스 (.flex, .mt-10 등)
│   ├── _chat-global.scss    ← 공통 레이아웃 클래스
│   ├── _element-dark.scss   ← Element Plus 다크모드 오버라이드
│   └── _dropdown.scss       ← 드롭다운 팝업 다크 스타일
│
└── mixins/                  ← 재사용 스타일 블록 (컴포넌트가 가져다 쓰는)
    ├── _index.scss          ← @forward 허브
    ├── _layout.scss         ← 통계 행
    ├── _cards.scss          ← 통계 카드
    ├── _markdown.scss       ← 마크다운 렌더링 (9개 mixin)
    ├── _chat.scss           ← 채팅 UI 요소 (6개 mixin)
    ├── _forms.scss          ← 설정 폼
    ├── _animations.scss     ← 애니메이션 (6개 mixin)
    ├── _chart.scss          ← 차트 빌더 (5개 mixin)
    └── _dashboard.scss      ← 대시보드 (2개 mixin)
```

---

## main.scss — 진입점의 역할

```scss
// main.scss (17줄)
@use './variables';           // 1. CSS 변수 선언
@use '../fonts/font-faces';   // 2. 폰트 선언
@use './modules/reset';       // 3. 브라우저 초기화
@use './modules/utilities';   // 4. 유틸리티 클래스
@use './modules/chat-global'; // 5. 공통 레이아웃
@use './modules/element-dark';// 6. 다크모드 오버라이드
@use './modules/dropdown';    // 7. 드롭다운 다크
```

```
앱 시작 시 로드 순서:

  main.js → import 'main.scss'
               │
               ├─ variables     → :root { --color-primary: #409eff; ... }
               ├─ font-faces    → @font-face { ... }
               ├─ reset         → *, html, body { ... }
               ├─ utilities     → .flex, .mt-10, .text-center ...
               ├─ chat-global   → .chat-container, .content-card ...
               ├─ element-dark  → [data-theme="dark"] .el-card { ... }
               └─ dropdown      → .dark-dropdown-popper { ... }
```

**핵심**: `modules/`는 앱 시작 시 한 번 로드되어 **전역으로** 적용됩니다.
반면 `mixins/`는 **각 컴포넌트가 필요할 때** `@include`로 가져다 씁니다.

---

## @use vs @import vs @forward

SCSS 최신 표준은 `@import` 대신 `@use`와 `@forward`를 사용합니다:

| 키워드 | 역할 | 비유 |
|--------|------|------|
| `@use` | 파일을 가져와 사용 | `import` (Python/JS) |
| `@forward` | 파일을 중계 (re-export) | `export { } from` (JS) |
| `@import` (구식) | 전역 가져오기 | `#include` (C) — 사용하지 않음 |

```
mixins/_index.scss ← @forward 허브
  │
  ├── @forward 'layout'      ← _layout.scss의 mixin들을 외부로 전달
  ├── @forward 'cards'
  ├── @forward 'markdown'
  ├── @forward 'chat'
  ├── @forward 'forms'
  ├── @forward 'animations'
  ├── @forward 'chart'
  └── @forward 'dashboard'

컴포넌트에서 사용:
  @use '@/assets/styles/mixins' as mixins;
  @include mixins.stat-card;
```

---

## modules/ vs mixins/ 차이

```
┌──────────────────────────────────────────────────────────┐
│                     modules/ (전역)                       │
│                                                          │
│  "앱 시작 시 자동 적용"                                    │
│  → .flex, .content-card, [data-theme="dark"] .el-card    │
│  → 모든 페이지에서 즉시 사용 가능                           │
│  → HTML에 클래스명만 붙이면 됨                              │
│                                                          │
│  비유: 건물 공용 시설 (복도 조명, 엘리베이터)                │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                     mixins/ (로컬)                        │
│                                                          │
│  "컴포넌트가 필요할 때 @include로 포함"                     │
│  → @include mixins.md-table-styles(12px);                │
│  → 파라미터로 커스터마이징 가능                              │
│  → scoped CSS 안에서 동작                                 │
│                                                          │
│  비유: 가구 세트 (원하는 방에 배치, 크기 조절 가능)           │
└──────────────────────────────────────────────────────────┘
```

---

## JS 유틸리티 전체 구조

```
frontend/src/utils/
│
├── markdownParser.js    ← 마크다운 → HTML 변환 + 테이블 복사
│   ├── formatMarkdownToHtml()     11단계 파이프라인
│   └── registerTableCopyFunction() 전역 복사 핸들러
│
├── format.js            ← 포맷팅 함수 모음
│   ├── formatDateTime()    → "2026.02.12 16:38:47"
│   ├── formatDate()        → "2026.02.12"
│   ├── formatNumber()      → "1,234,567"
│   ├── formatResponseTime()→ "123ms" / "1.5s"
│   └── truncateText()      → "긴 텍스트..." (말줄임)
│
└── exportUtils.js       ← 파일 내보내기 유틸리티
    ├── sanitizeFilename()      → 파일명 안전하게
    ├── formatTimestamp()       → "20260212_163847"
    ├── downloadBlob()          → Blob → 다운로드
    ├── downloadCsv()           → CSV 다운로드 (BOM 포함)
    ├── downloadDataUrl()       → data URL → 다운로드
    ├── captureElementPng()     → DOM → PNG (html-to-image)
    └── exportElementPdf()      → DOM → PDF (jsPDF 멀티페이지)
```

---

## 문서 목차

| 파일 | 주제 | 핵심 내용 |
|------|------|----------|
| **01** | CSS 변수 & 테마 | `:root` 라이트, `[data-theme="dark"]` 다크, 대시보드 격리, Element Plus 오버라이드 |
| **02** | SCSS Mixins | 8개 mixin 파일 상세, 파라미터 패턴, `:deep()` 활용 |
| **03** | 유틸리티 | JS 유틸리티 3종 + CSS 유틸리티 클래스 + 전역 모듈 |
| **04** | 어떻게 동작하나 | 다크모드 전환 시나리오, 마크다운 렌더링 파이프라인, PDF 내보내기 흐름 |

---

## 소스 파일 요약표

### SCSS 파일 (14개)

| 파일 | 줄 수 | 역할 |
|------|-------|------|
| `_variables.scss` | 302 | CSS 변수 정의 (라이트/다크/대시보드) |
| `main.scss` | 17 | 진입점 (@use로 모듈 조합) |
| `mixins/_index.scss` | 12 | Mixin 허브 (@forward 8개) |
| `mixins/_animations.scss` | 77 | 애니메이션 6종 |
| `mixins/_cards.scss` | 44 | 통계 카드 |
| `mixins/_markdown.scss` | 170 | 마크다운 렌더링 9종 |
| `mixins/_chat.scss` | 92 | 채팅 UI 6종 |
| `mixins/_forms.scss` | 30 | 설정 폼 2종 |
| `mixins/_layout.scss` | 13 | 통계 행 |
| `mixins/_chart.scss` | 76 | 차트 빌더 5종 |
| `mixins/_dashboard.scss` | 29 | 대시보드 2종 |
| `modules/_reset.scss` | 38 | 브라우저 초기화 + 스크롤바 |
| `modules/_utilities.scss` | 60 | 유틸리티 클래스 |
| `modules/_chat-global.scss` | 179 | 공통 레이아웃 클래스 |
| `modules/_element-dark.scss` | 376 | Element Plus 다크모드 |
| `modules/_dropdown.scss` | 77 | 드롭다운 다크 스타일 |

### JS 유틸리티 파일 (3개)

| 파일 | 줄 수 | 함수 수 | 역할 |
|------|-------|---------|------|
| `markdownParser.js` | 308 | 7 | 마크다운→HTML 변환 |
| `format.js` | 69 | 5 | 날짜/숫자/시간 포맷 |
| `exportUtils.js` | 188 | 7 | 파일 내보내기 |

---

## 리뷰 체크리스트 (Phase 8 전체)

- [ ] CSS 변수가 `:root`(라이트)와 `[data-theme="dark"]`(다크)에 쌍으로 정의되어 있는가?
- [ ] 모든 색상이 하드코딩 대신 CSS 변수(`var(--xxx)`)를 사용하는가?
- [ ] Mixin이 파라미터화되어 재사용성을 높이고 있는가?
- [ ] `:deep()` 선택자가 올바르게 사용되어 자식 컴포넌트에 스타일이 전달되는가?
- [ ] `escapeHtml()`로 XSS가 방지되고 있는가?
- [ ] CSV 내보내기에 BOM이 포함되어 한글이 깨지지 않는가?
- [ ] PDF 내보내기가 멀티페이지를 지원하는가?
