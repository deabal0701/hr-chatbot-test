# Phase 4. API 통신 - 백엔드와 어떻게 대화하는가?

## 이 Phase에서 배우는 것

Phase 3에서 Store가 `authApi.login()`, `searchApi.search()` 등을 호출하는 것을 보았습니다.
이제 이 **API 호출이 어떻게 구성되어 있고, 요청/응답이 어떻게 처리되는지** 이해합니다.

## 비유로 이해하기

API 통신 계층은 **우편 시스템**과 같습니다:

```
[프론트엔드]                  [우편 시스템]              [백엔드 서버]

Store가 질문 작성              Axios가 배달
    │                            │                        │
    ▼                            ▼                        ▼
authApi.login(id, pw)  →  POST /api/v1/auth/login  →  FastAPI 처리
                             ├ 토큰 자동 첨부               │
                             ├ JSON 변환                    │
                             └ 에러 시 자동 재시도            ▼
                                                      { success, data, error }
                                  ◄────────────────  응답 발송

                             인터셉터가 응답 처리:
                             ├ data 자동 추출
                             ├ 401 → 토큰 갱신
                             └ 에러 → 표준 형식
                                  │
                                  ▼
                          Store로 결과 전달
```

## 파일 구조

```
frontend/src/api/
├── index.js             ← ⭐ Axios 인스턴스 + 인터셉터 (핵심!)
├── sse.js               ← ⭐ SSE 스트리밍 클라이언트
├── auth.js              ← 인증 API (login, logout, refresh)
├── search.js            ← 검색 API (RAG, NL2SQL, 스트리밍)
├── agent.js             ← AI Agent API (스트리밍 포함)
├── users.js             ← 사용자 CRUD API
├── roles.js             ← 역할 CRUD API
├── menus.js             ← 메뉴 CRUD API
├── tenants.js           ← 테넌트 CRUD API
├── documents.js         ← 문서 CRUD API
├── settings.js          ← 시스템 설정 API
├── codes.js             ← 코드 관리 API
├── history.js           ← 검색 이력 API
├── dashboard.js         ← 관리자 대시보드 API
├── personalDashboard.js ← 개인 대시보드 API
└── departments.js       ← 부서 조회 API
```

**핵심 2개 + 대표 패턴 2개**를 집중적으로 다룹니다:

## 리뷰 파일 목록

| 순서 | 리뷰 문서 | 핵심 |
|------|-----------|------|
| 1 | [01_axios_basics.md](01_axios_basics.md) | Axios 인스턴스, 인터셉터, 토큰 갱신 |
| 2 | [02_api_modules.md](02_api_modules.md) | API 모듈 패턴 (auth, users, search) |
| 3 | [03_sse_streaming.md](03_sse_streaming.md) | SSE 스트리밍 클라이언트 (sse.js) |
| 4 | [04_how_it_works.md](04_how_it_works.md) | 동작 원리 종합 (요청→응답 추적) |

## 리뷰 시 스스로 답해볼 질문

1. 모든 API 요청에 토큰이 자동으로 붙는 원리는?
2. 백엔드 응답 `{success, data, error}`가 프론트엔드에서 어떻게 처리되는가?
3. 토큰이 만료되면 어떻게 자동으로 갱신되는가?
4. SSE 스트리밍이 일반 HTTP 요청과 다른 점은?
5. 16개 API 모듈이 모두 같은 패턴인 이유는?
