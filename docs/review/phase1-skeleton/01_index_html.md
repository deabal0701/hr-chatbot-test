# 1. index.html - 앱의 시작점

> **파일 위치**: `frontend/index.html`

## 이 파일은 뭐하는 파일인가?

**웹 브라우저가 가장 먼저 읽는 파일**입니다. 우리 앱의 "현관문"이라고 생각하면 됩니다.

일반 웹사이트는 페이지마다 HTML 파일이 있지만(about.html, contact.html, ...), Vue.js 같은 **SPA(Single Page Application)**에서는 **이 파일 하나가 전부**입니다. 나머지 화면 전환은 JavaScript가 처리합니다.

## 전체 코드

```html
<!DOCTYPE html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <link rel="alternate icon" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>MUREUM</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.js"></script>
  </body>
</html>
```

## 한 줄씩 이해하기

### `<!DOCTYPE html>`
```html
<!DOCTYPE html>
```
- "이 문서는 HTML5입니다"라고 브라우저에 알려주는 선언문
- 모든 HTML 파일의 첫 줄에 반드시 있어야 함

### `<html lang="ko">`
```html
<html lang="ko">
```
- `lang="ko"` → 이 페이지의 언어가 **한국어**라는 뜻
- 검색 엔진(Google)과 스크린 리더(시각장애인용)가 이 정보를 활용함

### `<head>` 영역 - 보이지 않는 설정들
```html
<head>
  <meta charset="UTF-8" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="alternate icon" href="/favicon.ico" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>MUREUM</title>
</head>
```

| 태그 | 역할 |
|------|------|
| `charset="UTF-8"` | 한글이 깨지지 않도록 인코딩 설정 |
| `link rel="icon"` | 브라우저 탭에 보이는 작은 아이콘 (파비콘) |
| `link rel="alternate icon"` | SVG를 지원하지 않는 브라우저를 위한 대체 아이콘 |
| `viewport` | 모바일에서도 화면이 제대로 보이도록 설정 |
| `title` | 브라우저 탭에 표시되는 제목 → **"MUREUM"** |

### `<body>` 영역 - 핵심 2줄!

```html
<body>
  <div id="app"></div>                                    <!-- ① -->
  <script type="module" src="/src/main.js"></script>      <!-- ② -->
</body>
```

#### ① `<div id="app"></div>` - 빈 그릇

이것이 이 파일에서 **가장 중요한 줄**입니다!

- 처음에는 완전히 **비어있는 div** 태그
- Vue.js가 나중에 이 div 안에 전체 앱 화면을 그려 넣음
- `id="app"`이라는 이름표를 붙여서 Vue가 찾을 수 있게 함

```
처음 (HTML 로드 직후):        나중에 (Vue 실행 후):
┌──────────────────┐         ┌──────────────────┐
│  <div id="app">  │         │  <div id="app">  │
│                   │   →→→   │    ┌────────────┐│
│    (텅 비어있음)    │         │    │ 로그인 화면  ││
│                   │         │    │ 또는 채팅 화면││
│  </div>           │         │    └────────────┘│
└──────────────────┘         │  </div>           │
                              └──────────────────┘
```

#### ② `<script type="module" src="/src/main.js">` - 엔진 시동

- `type="module"` → ES Module 방식으로 JavaScript를 로드 (import/export 사용 가능)
- `src="/src/main.js"` → main.js 파일을 실행하라!
- 이 한 줄이 실행되면 **Vue 앱 전체가 시작**됨

## 왜 이렇게 간단한가?

**SPA(Single Page Application)의 핵심 원리** 때문입니다:

```
[전통적 웹사이트]                    [SPA - Vue.js]
─────────────────                   ─────────────────
about.html ← 서버 요청              index.html 하나!
contact.html ← 서버 요청            │
products.html ← 서버 요청           └→ JavaScript가 화면을
login.html ← 서버 요청                  동적으로 교체
                                       (서버 요청 없이!)
페이지 이동마다 → 전체 새로고침       페이지 이동마다 → 부분만 변경
화면 깜빡임 있음                      화면 깜빡임 없음 (빠름!)
```

## 리뷰 체크리스트

- [x] `lang="ko"`가 적절한가? → 한국어 서비스이므로 적절함
- [x] `charset="UTF-8"` 설정이 있는가? → 한글 깨짐 방지에 필수
- [x] `viewport` 메타 태그가 있는가? → 모바일 대응에 필수
- [x] favicon이 설정되어 있는가? → SVG + ICO 이중 설정 (좋음)
- [x] `<div id="app">` 마운트 포인트가 있는가? → Vue 앱의 필수 요소
- [x] script에 `type="module"`이 있는가? → ES Module 사용을 위해 필수

## 핵심 정리

| 개념 | 설명 |
|------|------|
| SPA | 하나의 HTML로 모든 화면을 처리하는 방식 |
| `<div id="app">` | Vue가 화면을 그릴 빈 그릇 |
| `type="module"` | 최신 JavaScript import/export 문법 사용 |
| `main.js` | 이 HTML이 로드한 후 실행되는 앱의 시작점 |

---
> **다음**: [02_package_json.md](02_package_json.md) - 앱에 필요한 재료(라이브러리) 목록
