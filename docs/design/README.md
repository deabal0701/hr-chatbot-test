# MUREUM 설계 문서 인덱스

> **최종 업데이트**: 2026-03-10

## 문서 목록

| # | 문서 | 영역 | 설명 | 상태 |
|---|------|------|------|------|
| 00 | [architecture_overview](00_architecture_overview.md) | 아키텍처 | 시스템 전체 구조, 기술 스택, 레이어 구성 | 완료 |
| 01 | [ai_workflows](01_ai_workflows.md) | AI 핵심 | Agent(ReAct), NL2SQL(멀티턴), RAG 워크플로우 | 완료 |
| 02 | [auth_and_permission](02_auth_and_permission.md) | 보안 | JWT 인증, 메뉴 기반 CRUD 권한, 역할 계층 | 완료 |
| 03 | [database](03_database.md) | 데이터 | ERD, 테이블 명세, 커넥션 관리, 어댑터 패턴 | 완료 |
| 04 | [api_reference](04_api_reference.md) | API | 전체 엔드포인트 레퍼런스 (13개 그룹) | 완료 |
| 05 | [frontend](05_frontend.md) | 프론트엔드 | Vue 3 아키텍처, Vuex, 라우팅, SCSS | 완료 |
| 06 | [deployment](06_deployment.md) | 운영 | Docker, Nginx, 배포 스크립트, 모니터링 | 완료 |
| 07 | [user_role_design](07_user_role_design.md) | 보안 상세 | 사용자/역할/권한 관리 상세 설계 (v3.0) | 완료 |
| 08 | [dashboard_design](08_dashboard_design.md) | 화면 설계 | 대시보드 전면 보완 설계 (KPI, 차트) | 완료 |
| 09 | [future_roadmap](09_future_roadmap.md) | 로드맵 | 추가 개발 필요 사항 정리 | 신규 |
| 10 | [nl2sql_accuracy_analysis](10_nl2sql_accuracy_analysis.md) | AI 분석 | NL2SQL 정확도 분석 보고서 (Oracle DB) | 완료 |
| 11 | [department_sso_design](11_department_sso_design.md) | 보안 | 부서 관리(완료) + SSO 연동(Phase 4 구현 완료, Phase 5 미착수) | 완료 |
| 12 | [hybrid_search_design](12_hybrid_search_design.md) | AI 검색 | 하이브리드 검색 (Vector+pg_trgm+RRF) + 리랭킹 확장 아키텍처 | 설계완료/구현예정 |

## 영역별 분류

### 시스템 기반
- **00_architecture_overview** — 전체 아키텍처, 레이어 구조, 기술 스택
- **03_database** — 데이터베이스 설계, ERD, 커넥션 관리
- **06_deployment** — 배포, Docker, Nginx, 환경 설정

### AI 핵심 기능
- **01_ai_workflows** — Agent(ReAct), NL2SQL(멀티턴+의도분석), RAG
- **10_nl2sql_accuracy_analysis** — NL2SQL 정확도 분석 보고서 (Oracle DB 대상)

### 보안/인증
- **02_auth_and_permission** — JWT 인증, 권한 모델 개요
- **07_user_role_design** — 사용자/역할/메뉴/테넌트 상세 설계 (v3.0)

### API/화면
- **04_api_reference** — 전체 API 엔드포인트 레퍼런스
- **05_frontend** — Vue 3 프론트엔드 아키텍처
- **08_dashboard_design** — 대시보드 화면 설계

### AI 검색 고도화
- **12_hybrid_search_design** — 하이브리드 검색 설계 (Vector + pg_trgm + RRF 융합, Reranker 확장)

### 로드맵
- **09_future_roadmap** — 미구현 사항, 개선 과제, 추가 개발 계획
