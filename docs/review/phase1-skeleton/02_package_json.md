# 2. package.json - 앱에 필요한 재료 목록

> **파일 위치**: `frontend/package.json`

## 이 파일은 뭐하는 파일인가?

**레시피 카드**와 같습니다. 이 앱을 만들기 위해 어떤 라이브러리(재료)가 필요하고, 어떤 명령어(조리법)로 실행하는지 적어놓은 파일입니다.

`npm install`을 실행하면 이 파일을 읽고 필요한 라이브러리를 모두 다운로드합니다.

## 전체 코드

```json
{
  "name": "mureum-frontend",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@element-plus/icons-vue": "^2.3.2",
    "axios": "^1.6.2",
    "echarts": "^6.0.0",
    "element-plus": "^2.4.4",
    "html-to-image": "^1.11.13",
    "jspdf": "^4.2.0",
    "vue": "^3.3.13",
    "vue-echarts": "^8.0.1",
    "vue-router": "^4.2.5",
    "vue3-grid-layout-next": "^1.0.7",
    "vuex": "^4.1.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.5.2",
    "sass": "^1.69.5",
    "vite": "^5.0.10"
  }
}
```

## 섹션별 이해하기

### 1. 기본 정보

```json
{
  "name": "mureum-frontend",    // 프로젝트 이름
  "version": "1.0.0",           // 버전 번호 (주.부.패치)
  "private": true,              // npm에 공개하지 않겠다는 뜻
  "type": "module"              // ES Module 방식 사용 (import/export)
}
```

- `private: true` → 실수로 `npm publish` 해도 공개되지 않도록 보호
- `type: "module"` → `require()` 대신 `import/export` 문법 사용

### 2. scripts - 실행 명령어

```json
"scripts": {
  "dev": "vite",              // 개발 서버 실행
  "build": "vite build",      // 배포용 빌드
  "preview": "vite preview"   // 빌드 결과물 미리보기
}
```

터미널에서 이렇게 사용합니다:

```bash
npm run dev       # 개발 서버 시작 → http://localhost:19080
npm run build     # 배포용 파일 생성 → dist/ 폴더에 출력
npm run preview   # build 결과물을 로컬에서 확인
```

```
[개발 중]                        [배포할 때]
npm run dev                      npm run build
    │                                │
    ▼                                ▼
Vite 개발 서버 실행               dist/ 폴더에 최적화된 파일 생성
http://localhost:19080            index.html, assets/js, assets/css
코드 수정 → 자동 반영 (HMR)      → 이 파일들을 서버에 올림
```

### 3. dependencies - 앱 실행에 필요한 라이브러리

이 라이브러리들은 **사용자 브라우저에서 실행**됩니다:

```json
"dependencies": {
  "vue": "^3.3.13",                        // ⭐ Vue.js 프레임워크 (핵심!)
  "vue-router": "^4.2.5",                  // 페이지 이동 (URL → 화면 매칭)
  "vuex": "^4.1.0",                        // 전역 데이터 저장소

  "element-plus": "^2.4.4",               // ⭐ UI 컴포넌트 (버튼, 테이블, 폼 등)
  "@element-plus/icons-vue": "^2.3.2",    // Element Plus 아이콘

  "axios": "^1.6.2",                      // ⭐ HTTP 통신 (백엔드 API 호출)

  "echarts": "^6.0.0",                    // 차트 라이브러리
  "vue-echarts": "^8.0.1",               // ECharts의 Vue 래퍼

  "vue3-grid-layout-next": "^1.0.7",     // 드래그 가능한 그리드 레이아웃
  "html-to-image": "^1.11.13",           // 화면을 이미지로 캡처
  "jspdf": "^4.2.0"                      // PDF 생성
}
```

**역할별로 분류하면:**

```
┌──────────────────────────────────────────────────────┐
│                    Vue 생태계 (핵심)                    │
│  vue ─────── 화면을 그리는 프레임워크                     │
│  vue-router ─ URL에 따라 다른 화면 표시                  │
│  vuex ────── 여러 컴포넌트가 공유하는 데이터 저장소         │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                    UI 컴포넌트                         │
│  element-plus ─── 미리 만들어진 버튼, 테이블, 폼 등       │
│  @element-plus/icons-vue ─── 아이콘 모음               │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                    데이터 & 통신                       │
│  axios ──── 백엔드 서버와 HTTP 통신                     │
│  echarts ── 데이터를 차트(그래프)로 시각화                │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                    부가 기능                           │
│  vue3-grid-layout-next ── 대시보드 위젯 드래그 배치      │
│  html-to-image ────────── 화면 캡처                    │
│  jspdf ────────────────── PDF 내보내기                 │
└──────────────────────────────────────────────────────┘
```

### 4. devDependencies - 개발할 때만 필요한 도구

이 라이브러리들은 **개발자의 컴퓨터에서만 실행**되고, 사용자 브라우저에는 포함되지 않습니다:

```json
"devDependencies": {
  "vite": "^5.0.10",              // ⭐ 빌드 도구 (개발 서버 + 번들링)
  "@vitejs/plugin-vue": "^4.5.2", // Vite가 .vue 파일을 이해하도록
  "sass": "^1.69.5"               // SCSS → CSS 변환
}
```

```
[dependencies vs devDependencies 차이]

dependencies (앱 실행에 필요):
  사용자 브라우저에서 실행됨
  build 결과물에 포함됨
  예: vue, axios, element-plus

devDependencies (개발에만 필요):
  개발자 PC에서만 실행됨
  build 결과물에 포함 안 됨
  예: vite, sass
```

### 5. 버전 표기법 `^`의 의미

```
"vue": "^3.3.13"

^3.3.13 의 의미:
  3.3.13 이상, 4.0.0 미만

  ✅ 3.3.13  ← 정확히 이 버전
  ✅ 3.3.14  ← 패치 업데이트 (버그 수정)
  ✅ 3.4.0   ← 마이너 업데이트 (기능 추가)
  ❌ 4.0.0   ← 메이저 업데이트 (호환성 깨질 수 있음)
```

이렇게 하면 **버그 수정은 자동으로 받되, 큰 변경은 차단**합니다.

## 이 프로젝트에서 가장 중요한 3가지 라이브러리

| 순위 | 라이브러리 | 왜 중요한가 |
|------|-----------|------------|
| 1 | **Vue 3** | 이 앱의 프레임워크. 없으면 앱 자체가 없음 |
| 2 | **Element Plus** | 모든 UI(버튼, 테이블, 폼)가 이 라이브러리. 없으면 맨땅에 CSS 작성 |
| 3 | **Axios** | 백엔드 API와의 모든 통신 담당. 없으면 데이터를 가져올 수 없음 |

## 리뷰 체크리스트

- [x] `private: true`로 설정되어 있는가? → 실수로 npm에 공개되는 것 방지
- [x] Vue 3 기반인가? → `"vue": "^3.3.13"` 확인
- [x] dev/build/preview 스크립트가 있는가? → 개발~배포 흐름 완비
- [x] devDependencies가 적절히 분리되어 있는가? → vite, sass는 개발 전용
- [ ] 사용하지 않는 의존성은 없는가? → 주기적 점검 필요
- [ ] 보안 취약점이 있는 패키지는 없는가? → `npm audit`으로 확인

## 핵심 정리

| 개념 | 설명 |
|------|------|
| `scripts` | `npm run [이름]`으로 실행하는 명령어 모음 |
| `dependencies` | 앱 실행에 필수인 라이브러리 (브라우저에 포함) |
| `devDependencies` | 개발할 때만 필요한 도구 (빌드 결과에 미포함) |
| `^` (캐럿) | 메이저 버전은 고정, 마이너/패치는 허용 |
| `npm install` | package.json을 읽고 모든 의존성을 설치 |

---
> **이전**: [01_index_html.md](01_index_html.md) - SPA의 유일한 HTML
> **다음**: [03_vite_config.md](03_vite_config.md) - 빌드 도구 설정
