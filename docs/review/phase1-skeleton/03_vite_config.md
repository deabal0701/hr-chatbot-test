# 3. vite.config.js - 빌드 도구 설정

> **파일 위치**: `frontend/vite.config.js`

## 이 파일은 뭐하는 파일인가?

**Vite(비트)**는 Vue.js 앱의 **"주방 설비"**입니다. 개발할 때 서버를 띄워주고, 배포할 때 코드를 최적화해서 묶어줍니다.

이 설정 파일은 Vite에게 **"이렇게 동작해라"**라고 알려주는 지시서입니다.

## Vite가 하는 일 (쉽게)

```
[개발할 때 - npm run dev]
┌──────────────────────────────────────┐
│  .vue 파일 수정 → 브라우저 즉시 반영   │  ← HMR (Hot Module Replacement)
│  SCSS 파일 수정 → 스타일 즉시 반영     │
│  저장만 하면 끝! 새로고침 필요 없음      │
└──────────────────────────────────────┘

[배포할 때 - npm run build]
┌──────────────────────────────────────┐
│  50개 .vue 파일 → 최적화된 JS 3-4개   │  ← 번들링
│  20개 .scss 파일 → CSS 1-2개          │
│  이미지 최적화, 코드 압축               │
│  결과물: dist/ 폴더                    │
└──────────────────────────────────────┘
```

## 전체 코드

```javascript
import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src')
      }
    },
    css: {
      preprocessorOptions: {
        scss: {
          api: 'modern-compiler'
        }
      }
    },
    server: {
      port: 19080,
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:8000',
          changeOrigin: true
        }
      }
    },
    build: {
      outDir: 'dist',
      sourcemap: false
    }
  }
})
```

## 블록별 이해하기

### 1. import - 필요한 도구 가져오기

```javascript
import { defineConfig, loadEnv } from 'vite'   // Vite 설정 도구
import vue from '@vitejs/plugin-vue'            // .vue 파일 처리 플러그인
import path from 'path'                         // 파일 경로 처리 (Node.js 내장)
```

### 2. defineConfig - 설정을 감싸는 함수

```javascript
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())
  // ...
})
```

- `mode` → 현재 실행 모드 (`development`, `production`)
- `loadEnv(mode, ...)` → `.env.development` 또는 `.env.production` 파일을 읽음

```
npm run dev   → mode = "development" → .env.development 읽음
npm run build → mode = "production"  → .env.production 읽음
```

**.env 파일들의 내용:**

| 파일 | VITE_API_URL | 용도 |
|------|-------------|------|
| `.env.development` | `http://localhost:19090` | 로컬 개발 |
| `.env.docker` | (빈 값) | Docker 환경 (nginx 프록시) |
| `.env.production` | `https://api.yourcompany.com` | 실제 서비스 |

### 3. plugins - Vue 플러그인

```javascript
plugins: [vue()]
```

- Vite는 기본적으로 `.vue` 파일을 모름
- 이 플러그인이 `.vue` 파일을 → JavaScript로 변환해줌

```
MyComponent.vue                 변환 후
┌──────────────┐               ┌──────────────┐
│ <template>   │               │              │
│   <div>Hi</div>  ──────→    │  JavaScript  │
│ <script>     │               │  코드        │
│   ...        │               │              │
│ <style>      │               │  + CSS       │
│   ...        │               │              │
└──────────────┘               └──────────────┘
```

### 4. resolve.alias - 경로 단축키 ⭐

```javascript
resolve: {
  alias: {
    '@': path.resolve(__dirname, 'src')
  }
}
```

**이 설정이 없다면:**
```javascript
// ❌ 상대 경로 지옥 - 파일 위치에 따라 경로가 달라짐
import Header from '../../../components/layout/AppHeader.vue'
import api from '../../../../api/index.js'
```

**이 설정이 있으면:**
```javascript
// ✅ 항상 src/ 기준으로 작성 - 파일을 어디로 옮겨도 경로 불변
import Header from '@/components/layout/AppHeader.vue'
import api from '@/api/index.js'
```

```
@ = frontend/src/

@/api/auth.js       → frontend/src/api/auth.js
@/views/LoginView.vue → frontend/src/views/LoginView.vue
@/store/index.js    → frontend/src/store/index.js
```

### 5. css - SCSS 설정

```javascript
css: {
  preprocessorOptions: {
    scss: {
      api: 'modern-compiler'    // 최신 Sass 컴파일러 API 사용
    }
  }
}
```

- SCSS는 CSS의 **확장 버전** (변수, 중첩, 믹스인 사용 가능)
- `modern-compiler` → 최신 Dart Sass 컴파일러를 사용하겠다는 뜻

```scss
// SCSS (개발자가 작성)          →  CSS (브라우저가 이해)
$primary: #409eff;                 .button { color: #409eff; }
.button {                          .button:hover { color: #66b1ff; }
  color: $primary;
  &:hover { color: lighten($primary, 10%); }
}
```

### 6. server - 개발 서버 설정 ⭐⭐

```javascript
server: {
  port: 19080,               // 개발 서버 포트
  proxy: {
    '/api': {                 // '/api'로 시작하는 요청은...
      target: env.VITE_API_URL || 'http://localhost:8000',  // 백엔드로 전달
      changeOrigin: true      // 요청 헤더의 host를 백엔드 주소로 변경
    }
  }
}
```

**프록시(Proxy)가 왜 필요한가?**

웹 브라우저는 **보안 정책(CORS)** 때문에 다른 포트/도메인으로 직접 API 호출이 차단됩니다:

```
[프록시 없이] ❌ CORS 에러 발생!
브라우저(19080) ──직접──→ 백엔드(19090)
                 "다른 포트잖아! 차단!"

[프록시 있으면] ✅ 정상 동작
브라우저(19080) → Vite 프록시(19080) → 백엔드(19090)
                 "같은 포트니까 OK"     "서버끼리는 CORS 없음"
```

**실제 요청 흐름:**
```
프론트엔드 코드:  axios.get('/api/v1/users')

    ↓ 브라우저가 보내는 요청

http://localhost:19080/api/v1/users    (프론트엔드 포트)

    ↓ Vite 프록시가 가로채서 변환

http://localhost:19090/api/v1/users    (백엔드 포트로 전달!)

    ↓ 백엔드 응답을 받아서

브라우저에 돌려줌 (마치 19080에서 온 것처럼)
```

### 7. build - 빌드 설정

```javascript
build: {
  outDir: 'dist',         // 빌드 결과물이 저장될 폴더
  sourcemap: false         // 소스맵 생성 안 함 (보안, 용량 절약)
}
```

- `sourcemap: false` → 프로덕션에서는 원본 소스코드를 노출하지 않음
- 개발 중에는 Vite가 자동으로 소스맵을 제공 (브라우저 개발자 도구에서 디버깅 가능)

## 환경별 동작 비교

```
┌──────────────────────────────────────────────────────────┐
│  npm run dev (개발 모드)                                  │
│  ────────────────────────────                             │
│  • .env.development 로드                                  │
│  • http://localhost:19080 에서 서버 실행                   │
│  • /api → http://localhost:19090 으로 프록시               │
│  • 코드 수정 시 자동 반영 (HMR)                            │
│  • 소스맵 있음 (디버깅 편리)                               │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  npm run build (배포 모드)                                │
│  ────────────────────────────                             │
│  • .env.production 로드                                   │
│  • dist/ 폴더에 최적화된 파일 생성                          │
│  • JavaScript 코드 압축 (minify)                          │
│  • 사용하지 않는 코드 제거 (tree-shaking)                   │
│  • 소스맵 없음 (보안)                                     │
└──────────────────────────────────────────────────────────┘
```

## 리뷰 체크리스트

- [x] `@` 별칭이 설정되어 있는가? → import 경로 단순화에 필수
- [x] API 프록시가 설정되어 있는가? → 개발 중 CORS 문제 방지
- [x] 프록시 대상이 환경변수에서 읽히는가? → 환경별 분리 가능
- [x] sourcemap이 프로덕션에서 비활성화인가? → 보안상 적절
- [x] SCSS 설정이 있는가? → modern-compiler 사용

## 핵심 정리

| 개념 | 설명 |
|------|------|
| Vite | 빌드 도구 (개발 서버 + 번들링) |
| `@` 별칭 | `@` = `src/` 폴더. import 경로를 짧고 명확하게 |
| 프록시 | 브라우저의 CORS 제한을 우회. 개발 시 프론트→백엔드 연결 |
| `.env` 파일 | 환경별 설정값 분리 (개발/도커/프로덕션) |
| HMR | 코드 수정 시 새로고침 없이 즉시 반영 |

---
> **이전**: [02_package_json.md](02_package_json.md) - 의존성과 스크립트
> **다음**: [04_main_js.md](04_main_js.md) - 앱 초기화의 핵심
