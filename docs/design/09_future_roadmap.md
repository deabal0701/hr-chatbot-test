# win-AI 추가 개발 로드맵

> **최종 업데이트**: 2026-02-21
> **현재 상태**: Core AI + Auth + Multi-Tenant + Dashboard 구현 완료

---

## 1. 보안/권한 고도화

### 1.1 NL2SQL 권한 필터 (미구현 - 우선순위: 높음)

현재 NL2SQL은 role_code 기반 데이터 범위 제한이 적용되지 않음. SQL 결과에 다른 테넌트의 데이터가 노출될 수 있음.

**필요 작업**:
- `sql_executor.py`에 `inject_permission_filter()` 구현
- NL2SQL 그래프에 UserContext 전달 (현재 없음)
- `prompt_build_node`에 scope 정보 포함
- 비즈니스 DB 테이블에 `tenant_id` 컬럼 추가

**구현 방향**:
```
GLOBAL → WHERE 필터 없음
TENANT → WHERE tenant_id = ?
USER   → WHERE tenant_id = ? AND emp_id = ?
```

**관련 파일**: `app/graphs/nl2sql/nodes.py`, `app/core/database/sql_executor.py`

### 1.2 Agent Tool 권한 필터 (미구현 - 우선순위: 높음)

Agent의 SQL Tool, RAG Tool도 사용자 scope에 따른 데이터 필터링 필요.

**현재 상태**: `tenant_context.py` (ContextVar)는 구현되어 있으나 Agent Tool에서 활용하지 않음.

**필요 작업**:
- `sql_tool.py`: `get_tenant_id()`로 scope 필터 적용
- `rag_tool.py`: 문서 검색 시 테넌트 필터 적용

### 1.3 AuthMiddleware 강제 모드 전환 (우선순위: 중간)

현재 AuthMiddleware는 **선택적 모드** (Phase 3a): 토큰 없는 요청도 통과시킴.

**필요 작업**: 운영 환경에서 필수 모드로 전환 (특정 경로 제외)

---

## 2. 멀티테넌트 데이터 격리

### 2.1 테넌트별 문서 격리 (우선순위: 높음)

현재 `tb_docs`에 `tenant_id`가 없어 모든 테넌트가 동일 문서를 공유함.

**필요 작업**:
- `tb_docs`에 `tenant_id` 컬럼 추가
- Document CRUD에 테넌트 필터 적용
- RAG 검색 시 테넌트 필터 적용
- 임베딩 작업 시 테넌트 분리

**관련 파일**: `app/api/services/document_service.py`, `app/core/vector/vector_store.py`

### 2.2 테넌트별 설정 격리 (우선순위: 중간)

현재 `tb_app_settings`는 전역 설정만 지원. 테넌트별 LLM 모델, RAG 파라미터 등을 다르게 설정할 수 없음.

**필요 작업**:
- `tb_app_settings`에 `tenant_id` 컬럼 추가
- `settings_service.get_value()`에 테넌트 우선순위 추가
- 설정 우선순위: 테넌트 설정 > 전역 설정 > 환경변수 > 기본값

### 2.3 테넌트별 비즈니스 DB 분리 (우선순위: 낮음)

현재 모든 테넌트가 동일한 External DB를 사용. 테넌트별 별도 DB 연결이 필요할 수 있음.

---

## 3. AI 기능 고도화

### 3.1 RAG 고도화 (우선순위: 중간)

| 항목 | 설명 |
|------|------|
| Hybrid Search | 키워드(BM25) + 벡터 검색 결합 |
| Reranking | Cross-encoder로 검색 결과 재순위 |
| Query Decomposition | 복잡한 질문을 하위 질문으로 분해 |
| Chunk Overlap 최적화 | 현재 고정 크기 → 의미 단위 분할 |
| Multi-modal RAG | 이미지/표 포함 문서 처리 |

### 3.2 NL2SQL 고도화 (우선순위: 중간)

| 항목 | 설명 |
|------|------|
| Self-correction | SQL 실행 에러 시 자동 수정 강화 |
| Query Complexity 분류 | 복잡도별 다른 전략 (simple→template, complex→LLM) |
| SQL 캐싱 | 동일 패턴 질문의 SQL 재활용 |
| 결과 시각화 제안 | SQL 결과에 적합한 차트 타입 자동 추천 |

### 3.3 Agent 고도화 (우선순위: 낮음)

| 항목 | 설명 |
|------|------|
| Tool 플러그인 시스템 | 동적 Tool 등록/해제 |
| Agent 체인 | 복수 Agent 협업 (Supervisor 패턴) |
| 실행 계획 미리보기 | Tool 호출 전 사용자 확인 |
| 대화 요약 | 장기 세션 시 히스토리 요약 |

---

## 4. 성능/안정성 개선

### 4.1 Memory Leak 해결 (우선순위: 높음)

**현재 상태**: `BoundedInMemorySaver` 구현 완료 (`app/core/checkpoint.py`), 미적용.

**필요 작업**:
- `app/graphs/agent/graph.py`: `InMemorySaver` → `BoundedInMemorySaver` 교체
- `app/graphs/nl2sql/graph.py`: 동일 교체
- TTL, max_sessions 파라미터 설정 최적화

### 4.2 LLM 인스턴스 캐싱 (우선순위: 중간)

현재 매 요청마다 LLM 인스턴스를 새로 생성. 설정이 변경되지 않는 한 재사용 가능.

**필요 작업**:
- `LLMConfigManager`에 캐싱 레이어 추가
- 설정 변경 감지 시 캐시 무효화

### 4.3 Tool 인스턴스 재사용 (우선순위: 낮음)

Agent Tool 인스턴스도 매 요청 재생성. 싱글톤 또는 풀링 적용 가능.

### 4.4 DB Connection Pool 최적화 (우선순위: 중간)

- Connection health check 주기 최적화
- Pool overflow 시 대기 전략 검토
- 장기 유휴 커넥션 자동 정리

---

## 5. 사용자 경험 개선

### 5.1 사용자 Soft Delete (우선순위: 중간)

현재 물리 삭제 → `is_active=false` 전환으로 변경하여 데이터 보존.

### 5.2 API History FK 연결 (우선순위: 낮음)

`tb_api_history`에 `user_id` FK 추가 (SET NULL). 현재는 user 추적 불가.

### 5.3 감사 로그 (Audit Log) (우선순위: 중간)

관리 작업(사용자 생성/수정/삭제, 권한 변경, 설정 변경) 이력 추적.

**필요 작업**:
- `tb_audit_log` 테이블 생성
- 주요 서비스에 audit 기록 추가
- 감사 로그 조회 UI

### 5.4 사용자 챗 히스토리 저장 (우선순위: 중간)

현재 채팅 히스토리는 InMemorySaver에만 저장 (서버 재시작 시 소멸).

**필요 작업**:
- 채팅 세션/메시지를 DB에 영속 저장
- 이전 대화 이어하기 기능
- 대화 내역 검색

### 5.5 피드백 시스템 (우선순위: 낮음)

AI 응답에 대한 사용자 피드백 (좋아요/싫어요) 수집 및 분석.

---

## 6. 운영/모니터링

### 6.1 Prometheus 메트릭 활성화 (우선순위: 중간)

의존성은 설치되어 있으나 (`prometheus-client`) 메트릭 수집이 미구현.

**필요 메트릭**:
- 요청 수/응답 시간 (히스토그램)
- LLM API 호출 수/비용 추적
- DB 커넥션 풀 사용률
- 에러율

### 6.2 Health Check 고도화 (우선순위: 낮음)

현재 `/health`는 단순 OK 응답. DB, LLM API, 외부 DB 연결 상태 확인 포함.

### 6.3 로그 중앙화 (우선순위: 낮음)

JSON 포맷 로그 → ELK/Loki 등 로그 수집 시스템 연동.

---

## 7. 프론트엔드 개선

### 7.1 대시보드 자동 새로고침 (우선순위: 중간)

60초 polling + `visibilitychange` API로 비활성 탭 시 중지.

### 7.2 반응형 모바일 최적화 (우선순위: 낮음)

현재 데스크톱 중심 레이아웃. 태블릿/모바일 대응 필요.

### 7.3 다크모드 일관성 (우선순위: 낮음)

User 채팅과 Admin 모두 다크모드 기본. 테마 전환 시 일부 컴포넌트 스타일 미적용.

### 7.4 국제화 (i18n) (우선순위: 낮음)

현재 한국어 하드코딩. 다국어 지원 필요 시 vue-i18n 적용.

---

## 8. 구현 우선순위 요약

### Phase 5: 데이터 격리 (높음)
1. NL2SQL 권한 필터
2. Agent Tool 권한 필터
3. 테넌트별 문서 격리
4. Memory Leak 해결 (BoundedInMemorySaver 적용)

### Phase 6: 고도화 (중간)
1. 테넌트별 설정 격리
2. 감사 로그
3. 사용자 챗 히스토리 DB 저장
4. LLM 인스턴스 캐싱
5. RAG Hybrid Search
6. Prometheus 메트릭
7. 대시보드 자동 새로고침
8. AuthMiddleware 강제 모드

### Phase 7: 부가 기능 (낮음)
1. Soft Delete
2. API History FK
3. Agent 고도화 (플러그인, 체인)
4. NL2SQL 캐싱
5. Health Check 고도화
6. 반응형 모바일
7. 국제화
8. 피드백 시스템
