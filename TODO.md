## Todos
1. langgraph.checkpoint.memory(InMemorySaver) 을 통한 메모리(short term memory) 관리와 현재의 방법의 차이는?
2. agent를 생성시 create_agent를 사용하지 않는지? 현재의 방법과 langchain에서 생성하는 방식의 차이는?
create_agent(model, tools, checkpointer=InMemorySaver) -> create_agent 를 사용하지 않는 이점이 훨신 더 많음으로 판정.

3. middleware를 사용한 섬세하고 디테일한 컨트롤
 -> agent 내부활동 모니터링 및 컨트롤, 출력포맷설정, 가드레일(개인정보, 프롬프트인젝션)
 -> builtin middleware를 통한 카드번호등 마스킹
 -> human-the-roop, Model Call Limit, 

4. 장기메모리 및 긴대화 압축


## 학습

Python과 LangChain 코드를 효과적으로 분석하고 학습하는 방법을 단계별로 안내해드리겠습니다.

1. 체계적인 학습 순서
🎯 추천 학습 경로 (이 프로젝트 기준)

Level 1: 기본 구조 파악 (1-2일)
↓
Level 2: 핵심 개념 이해 (3-5일)
↓
Level 3: 실제 코드 분석 (5-7일)
↓
Level 4: 실습 및 수정 (지속적)
2. Level 1: 기본 구조 파악
Step 1: 프로젝트 전체 구조 시각화

# 프로젝트 구조 확인
tree app -L 2 -I "__pycache__|*.pyc"
우선 읽어야 할 문서 순서:

README.md - 프로젝트 개요
CLAUDE.md - 아키텍처 핵심 개념 (방금 보신 파일)
ARCHITECTURE.md - 상세 설계
PYTHON_CODE_GUIDE.md - 파일별 상세 설명
Step 2: 데이터 흐름 이해하기
시각적으로 이해하기:


사용자 질문
    ↓
FastAPI 엔드포인트 (api/routes/)
    ↓
의도 분류 (RAG vs NL2SQL)
    ↓
LangGraph 실행 (graphs/)
    ↓ ↓ ↓
[Node1] → [Node2] → [Node3]
    ↓
응답 반환
3. Level 2: 핵심 개념 이해
🔑 반드시 이해해야 할 5가지 개념
(1) LangGraph의 상태 기반 실행

# 전통적인 방식 (이 프로젝트는 이렇게 안 함!)
result = llm.invoke("질문")

# 이 프로젝트의 방식 (LangGraph)
state = {"query": "질문", "sql": None, "result": None}
final_state = await graph.ainvoke(state)  # 여러 노드를 거쳐감
실습 방법:

app/graphs/nl2sql_graph.py의 GraphState 클래스 보기
각 노드가 state를 어떻게 수정하는지 추적하기
(2) Async/Await 패턴

# 동기 방식 (느림)
def search(query):
    result = llm.invoke(query)  # 3초 대기
    return result

# 비동기 방식 (빠름)
async def search(query):
    result = await graph.ainvoke({"query": query})  # 다른 작업 가능
    return result
왜 중요한가: 여러 사용자 요청을 동시에 처리 가능

(3) Dynamic Settings (DB 기반 설정)

# 하드코딩 (나쁨)
model = "gpt-4o"

# 환경변수 (보통)
model = os.getenv("LLM_MODEL")

# 이 프로젝트 방식 (좋음)
model = settings_service.get_value("llm", "model", default)
# DB → .env → default 순서로 찾음
실습: Admin UI에서 설정 변경 → 코드 재시작 없이 반영되는지 확인

(4) Vector Embeddings (벡터 임베딩)

# 텍스트를 숫자 배열로 변환
"재택근무 정책" → [0.234, -0.891, 0.445, ..., 0.123]  # 1536개 숫자

# 유사도 검색
query_vector = embed("재택근무 언제 가능?")
similar_docs = vector_search(query_vector, top_k=5)
# → "재택근무 정책" 문서 찾아냄
실습: app/services/vector_store.py의 embed_query() 함수 읽기

(5) SQL Injection 방어

# 위험한 쿼리 차단
"DROP TABLE employee;"  # ❌ 차단됨
"SELECT * FROM tb_docs; DELETE FROM employee;"  # ❌ 차단됨

# 허용되는 쿼리
"SELECT name FROM employee WHERE dept='HR'"  # ✅ 안전함
실습: app/services/sql_executor.py의 validate_sql() 함수 읽기

4. Level 3: 실제 코드 분석 방법
🔍 추천 분석 순서
Phase 1: 간단한 파일부터 (30분)

1. app/config.py          # 설정 구조 이해
2. app/models/schemas.py  # 데이터 모델 이해
3. app/utils/logger.py    # 로깅 패턴 이해
Phase 2: 핵심 서비스 (2시간)

4. app/services/settings_service.py  # 동적 설정 로직
5. app/services/vector_store.py      # 임베딩 & 검색
6. app/services/sql_executor.py      # SQL 실행 & 보안
Phase 3: LangGraph 워크플로우 (3-4시간)

7. app/graphs/rag_graph.py     # RAG 워크플로우 (상대적으로 단순)
8. app/graphs/nl2sql_graph.py  # NL2SQL 워크플로우 (복잡함)
Phase 4: API 레이어 (1시간)

9. app/api/routes/search.py   # 검색 엔드포인트
10. app/main.py               # FastAPI 앱 초기화
📝 코드 읽는 실전 기법
기법 1: Request ID 추적


# 로그에서 하나의 요청 전체 흐름 보기
cat logs/app.log | grep "a1b2c3d4"  # request_id

# 출력 예시:
[a1b2c3d4] [STEP 0] [INIT] Starting NL2SQL
[a1b2c3d4] [STEP 1] [GENERATE] Generated SQL: SELECT...
[a1b2c3d4] [STEP 2] [VALIDATE] Validation passed
[a1b2c3d4] [STEP 3] [EXECUTE] Query returned 5 rows
[a1b2c3d4] [STEP 4] [ANSWER] Generated answer
기법 2: 브레이크포인트 디버깅


# 코드에 추가
import pdb; pdb.set_trace()  # 이 줄에서 멈춤

# 또는 IDE 브레이크포인트 사용 (VSCode)
# F9로 브레이크포인트 설정 → F5로 디버깅 시작
기법 3: 타입 힌트 활용


def process(state: GraphState) -> GraphState:
    # Ctrl+Click으로 GraphState 정의 보기
    # 마우스 오버로 타입 확인
5. Level 4: 실습 프로젝트
🎓 초보자용 실습 과제 (난이도순)
과제 1: 로그 메시지 추가 (⭐ 쉬움)

# app/graphs/nl2sql_graph.py의 _generate_sql() 함수에 로그 추가
logger.info(f"[{request_id}] [내가 추가한 로그] SQL 길이: {len(sql)}")
학습 목표: 코드 실행 흐름 파악

과제 2: 새로운 설정 추가 (⭐⭐ 보통)

# 1. config.py에 추가
max_retry: int = 3

# 2. DB에 추가
INSERT INTO tb_app_settings (category, key, value, value_type)
VALUES ('llm', 'max_retry', '3', 'integer');

# 3. 코드에서 사용
retry = settings_service.get_value("llm", "max_retry", 3)
학습 목표: 동적 설정 시스템 이해

과제 3: 간단한 노드 추가 (⭐⭐⭐ 어려움)

# RAG 그래프에 "문서 개수 세기" 노드 추가
def _count_documents(self, state: GraphState) -> GraphState:
    docs = state.get("documents", [])
    doc_count = len(docs)
    
    logger.info(f"Retrieved {doc_count} documents")
    state["doc_count"] = doc_count
    return state

# _build_graph()에 추가
workflow.add_node("count", self._count_documents)
workflow.add_edge("retrieve", "count")  # retrieve 다음에 실행
workflow.add_edge("count", "generate")
학습 목표: LangGraph 구조 이해

과제 4: 커스텀 검증 규칙 추가 (⭐⭐⭐⭐ 고급)

# sql_executor.py에 "최대 JOIN 개수 제한" 추가
def validate_sql(sql: str) -> tuple[bool, str]:
    # 기존 검증...
    
    # 새 규칙: JOIN 3개 이상 금지
    join_count = sql.upper().count(" JOIN ")
    if join_count > 3:
        return False, "Too many JOINs (max 3)"
    
    return True, ""
학습 목표: 보안 로직 이해 및 확장

6. 추천 학습 리소스
📚 필수 문서 (이 프로젝트)
CLAUDE.md - 지금 보고 계신 파일 (핵심 개념)
PYTHON_CODE_GUIDE.md - 파일별 상세 설명 (사전처럼 사용)
ARCHITECTURE.md - 시스템 설계 (큰 그림)
🌐 외부 학습 자료
LangChain 기초:

공식 문서: https://python.langchain.com/docs/get_started/introduction
튜토리얼: "LangChain Crash Course" (YouTube)
LangGraph 이해:

공식 가이드: https://langchain-ai.github.io/langgraph/
핵심 개념: StateGraph, Nodes, Edges, Conditional Routing
FastAPI 기초:

공식 문서: https://fastapi.tiangolo.com/ko/tutorial/
비동기 프로그래밍: async/await 개념
Vector DB & RAG:

"What is RAG?" (개념 이해)
pgvector 문서: https://github.com/pgvector/pgvector
7. 실전 디버깅 워크플로우
🐛 "이 코드가 뭐하는 거지?" 해결 프로세스

# 1단계: 함수 시그니처 확인
grep -r "def function_name" app/

# 2단계: 호출 위치 찾기
grep -r "function_name(" app/

# 3단계: 로그 추가해서 실행
# (함수 시작/끝에 logger.info() 추가)

# 4단계: 실제 실행해보기
curl -X POST "http://localhost:8000/api/v1/rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "테스트", "mode": "rag"}'

# 5단계: 로그 확인
tail -f logs/app.log
8. 학습 체크리스트
✅ 기본 이해 (1주차 목표)
 FastAPI의 @router.post() 데코레이터 이해
 async def와 await 차이 이해
 LangGraph의 State 개념 이해
 환경변수 vs DB 설정 차이 이해
 로그에서 request_id 추적 가능
✅ 중급 이해 (2주차 목표)
 LangGraph 노드 간 연결 방식 이해
 Conditional edges 동작 이해
 Vector embeddings 개념 이해
 SQL validation 로직 이해
 간단한 노드 수정 가능
✅ 고급 이해 (3-4주차 목표)
 전체 워크플로우 그릴 수 있음
 새로운 그래프 노드 추가 가능
 보안 검증 로직 수정 가능
 성능 병목 지점 파악 가능
 에러 디버깅 독립적으로 가능
9. 실용적인 팁
💡 코드 읽기 꿀팁
Tip 1: 작은 것부터


# ❌ 처음부터 전체 그래프 이해하려고 함
# ✅ 하나의 노드 함수만 집중해서 읽기

# 예: _generate_sql() 함수만 먼저 완전히 이해
Tip 2: 실행하면서 배우기


# 코드 수정 → 저장 → 자동 재시작 (--reload 덕분)
uvicorn app.main:app --reload

# 브라우저에서 즉시 테스트
http://localhost:8000/docs  # Swagger UI
Tip 3: 문서와 코드 같이 보기


화면 분할:
좌측 - VSCode (코드)
우측 - 브라우저 (CLAUDE.md)
Tip 4: 메모하면서 읽기


# 내가 이해한 내용 (노트 작성)

## _generate_sql() 함수
- 역할: 자연어 → SQL 변환
- 입력: state["query"], state["schema"]
- 출력: state["sql"]
- LLM 모델: settings에서 동적 로드
- 프롬프트: system + user 메시지 조합
10. 다음 단계
🚀 학습 완료 후 할 수 있는 것들
기능 확장: 새로운 검색 모드 추가
최적화: 캐싱 로직 추가로 속도 개선
모니터링: Prometheus 메트릭 추가
테스트: Pytest로 자동화 테스트 작성
💬 추천 학습 순서 요약

Day 1-2:   문서 읽기 (CLAUDE.md, README.md)
Day 3-5:   간단한 파일 분석 (config.py, schemas.py)
Day 6-10:  핵심 서비스 분석 (vector_store.py, sql_executor.py)
Day 11-15: LangGraph 분석 (rag_graph.py, nl2sql_graph.py)
Day 16-20: 실습 과제 해결 (위의 과제 1-4)
Day 21+:   자유 탐색 및 기능 추가
가장 중요한 것:

코드를 실행하면서 배우기
작은 수정을 직접 해보면서 이해하기
모르는 것은 로그를 추가해서 확인하기
궁금한 특정 파일이나 개념이 있으면 알려주세요. 더 자세히 설명해드리겠습니다!



@TODO
1. NL2SQL SQL 검증노드 추가 함.



@TODO2
NL2SQL 완성도 향상을 위한 기능 제안
Phase 1: 검증 강화 (먼저 구현)
기능	    현재	        개선	                우선순위
문법 검증	sqlparse 파싱만	EXPLAIN으로 DB 레벨 검증	 ⭐⭐⭐
컬럼 검증	❌ 없음	스키마 기반 컬럼 존재 확인	        ⭐⭐⭐
집계 함수 검증	❌ 없음	GROUP BY 정합성 체크	        ⭐⭐
조인 검증	❌ 없음	FK 관계 기반 조인 유효성	        ⭐⭐
Phase 2: 재시도 로직 (검증 후 구현)

1차 SQL 생성
     ↓
┌─────────────────────────────────────┐
│  SQL Validator                       │
│  ├─ 1. 문법 검증 (EXPLAIN)          │
│  ├─ 2. 컬럼 존재 검증               │
│  ├─ 3. 테이블 화이트리스트          │
│  └─ 4. 집계/GROUP BY 정합성         │
└─────────────────────────────────────┘
     ↓
❌ 오류 → 오류 원인 + 스키마 + 예시 재주입 → 2차 SQL 생성 (최대 2-3회)


✅ 정상 → 실행
Phase 3: 프롬프트 품질 향상
기능	설명	효과
Few-shot Examples	유사 질문-SQL 쌍 제공	정확도 20-30%↑
스키마 관계 정보	FK, 조인 관계 명시	조인 오류 감소
샘플 데이터	컬럼별 실제 값 예시	필터 조건 정확도↑
비즈니스 용어집	"입사자"="hire_date 기준"	도메인 이해도↑

Phase 4: 고급 기능
기능	설명
LLM 셀프 체크	생성 SQL을 LLM이 다시 검토 후 수정
쿼리 분해	복잡한 질문을 여러 단계로 나눠 처리
실행 오류 피드백	DB 오류 메시지를 LLM에 전달하여 수정
의도 확인	모호한 질문 시 사용자에게 확인 요청
권장 구현 순서

1. EXPLAIN 기반 문법 검증 추가 (sql_executor.py)
2. 컬럼 존재 검증 추가 (schema_loader 활용)
3. 재시도 노드 추가 (nl2sql_graph.py)
4. 오류 피드백 프롬프트 설계
5. Few-shot examples 저장/관리 기능
6. (선택) LLM 셀프 체크 노드


이 순서로 진행하시겠습니까? 먼저 Phase 1 (EXPLAIN 검증 + 컬럼 검증)부터 시작하는 것을 권장합니다.