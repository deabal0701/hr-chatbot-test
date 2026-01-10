# 로컬 폰트 설정

폐쇄망 환경에서 사용하기 위해 폰트 파일을 로컬에 저장합니다.

## 폰트 파일 위치

폰트 파일은 `public/fonts/` 폴더에 위치합니다 (Vite 정적 파일 제공).

## 폴더 구조

```
frontend/
├── public/
│   └── fonts/
│       ├── inter/
│       │   ├── Inter-Regular.woff2
│       │   ├── Inter-Medium.woff2
│       │   ├── Inter-SemiBold.woff2
│       │   └── Inter-Bold.woff2
│       └── pretendard/
│           ├── Pretendard-Regular.woff2
│           ├── Pretendard-Medium.woff2
│           ├── Pretendard-SemiBold.woff2
│           └── Pretendard-Bold.woff2
└── src/
    └── assets/
        └── fonts/
            ├── README.md (이 파일)
            └── fonts.scss (@font-face 정의)
```

## 폰트 스택

적용되는 폰트 우선순위:
1. **Inter** - 영문 기본 폰트
2. **Pretendard** - 한글 기본 폰트
3. **시스템 폰트** - -apple-system, BlinkMacSystemFont, Segoe UI, Roboto 등

## 다운로드 소스 (참고)

- Inter: https://github.com/rsms/inter/releases
- Pretendard: https://github.com/orioncactus/pretendard/releases
