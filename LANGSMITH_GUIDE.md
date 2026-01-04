# LangSmith 통합 가이드

InsightLink 프로젝트에 LangSmith를 통합하여 LangChain 애플리케이션의 성능을 모니터링하고 디버깅할 수 있습니다.

## 📋 목차

1. [LangSmith란?](#langsmith란)
2. [설정 방법](#설정-방법)
3. [사용 방법](#사용-방법)
4. [주요 기능](#주요-기능)
5. [문제 해결](#문제-해결)

## 🎯 LangSmith란?

**LangSmith**는 LangChain 팀이 제공하는 LLM 애플리케이션 개발 플랫폼입니다.

### 주요 기능

- **트레이싱(Tracing)**: LLM 호출, 체인 실행, 에이전트 동작을 실시간 추적
- **모니터링(Monitoring)**: 응답 시간, 토큰 사용량, 비용 분석
- **디버깅(Debugging)**: 각 단계별 입출력, 에러 추적
- **평가(Evaluation)**: 모델 성능 평가 및 A/B 테스트
- **데이터셋 관리**: 테스트 케이스 관리

공식 사이트: https://smith.langchain.com/

## ⚙️ 설정 방법

### 1. LangSmith 계정 생성

1. [LangSmith](https://smith.langchain.com/) 접속
2. 회원가입 (GitHub 계정 연동 가능)
3. API 키 발급:
   - 대시보드 → Settings → API Keys
   - "Create API Key" 클릭
   - 발급된 키 복사 (한 번만 표시됨)

### 2. 환경 변수 설정

`.env` 파일에 다음 내용을 추가하세요:

```bash
# LangSmith 설정
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=hr-chatbot-insightlink
```

**주의**: `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다.

### 3. 프로젝트 설정 확인

환경 변수가 올바르게 설정되었는지 확인:

```python
from app.config import settings

print(f"LangSmith 활성화: {settings.langsmith_enabled}")
```

## 🚀 사용 방법

### 자동 트레이싱

InsightLink는 애플리케이션 시작 시 자동으로 LangSmith를 초기화합니다.

```python
# app/main.py에서 자동 실행됨
from app.utils.langsmith import init_langsmith

init_langsmith()
```

환경 변수가 설정되어 있으면 모든 LangChain 호출이 자동으로 트레이싱됩니다.

### 트레이싱 확인

1. 서버 시작:
   ```bash
   uvicorn app.main:app --reload
   ```

2. API 호출 (예: Agent 검색):
   ```bash
   curl -X POST "http://localhost:8000/api/v1/agent/search" \
     -H "Content-Type: application/json" \
     -d '{"question": "2023년 입사자 정보를 알려줘", "session_id": "test-session"}'
   ```

3. LangSmith 대시보드 확인:
   - https://smith.langchain.com/ 접속
   - 프로젝트 `hr-chatbot-insightlink` 선택
   - 실시간 트레이스 확인

### 수동 트레이싱 (고급)

특정 함수나 작업만 트레이싱하려면:

```python
from langchain.callbacks.tracers import LangChainTracer

# 트레이서 생성
tracer = LangChainTracer(project_name="hr-chatbot-insightlink")

# LLM 호출 시 콜백으로 전달
result = llm.invoke(
    "질문",
    config={"callbacks": [tracer]}
)
```

### 개발/프로덕션 환경 분리

환경별로 다른 프로젝트 사용:

```bash
# .env.development
LANGCHAIN_PROJECT=hr-chatbot-insightlink-dev

# .env.production
LANGCHAIN_PROJECT=hr-chatbot-insightlink-prod
```

## 🎨 주요 기능

### 1. 트레이스 뷰어

각 API 요청에 대해:
- **타임라인**: 각 단계별 실행 시간
- **입출력**: 프롬프트, 응답, 중간 결과
- **메타데이터**: 모델, 토큰 수, 비용

### 2. Agent 실행 추적

Agent 모드 사용 시:
- 사고 과정(Thought)
- 도구 선택(Action)
- 도구 실행 결과(Observation)
- 반복 횟수

### 3. 성능 모니터링

- **응답 시간**: P50, P95, P99 지연 시간
- **토큰 사용량**: 입력/출력 토큰 통계
- **비용 분석**: 모델별 사용 비용
- **에러율**: 실패한 요청 비율

### 4. 데이터셋 & 평가

테스트 케이스 관리:

```python
from langsmith import Client

client = Client()

# 데이터셋 생성
dataset = client.create_dataset("hr-qa-test")

# 예시 추가
client.create_example(
    inputs={"question": "재택근무 정책이 뭐야?"},
    outputs={"answer": "재택근무는 주 2회까지 가능합니다."},
    dataset_id=dataset.id
)
```

## 🔧 문제 해결

### LangSmith가 활성화되지 않음

**증상**: 트레이스가 대시보드에 표시되지 않음

**해결책**:
1. 환경 변수 확인:
   ```python
   import os
   print(os.environ.get("LANGCHAIN_TRACING_V2"))  # "true"
   print(os.environ.get("LANGCHAIN_API_KEY"))     # 키 값
   ```

2. API 키 유효성 확인:
   ```bash
   curl -H "x-api-key: YOUR_API_KEY" https://api.smith.langchain.com/info
   ```

3. 서버 재시작:
   ```bash
   # 환경 변수 변경 후 반드시 재시작
   uvicorn app.main:app --reload
   ```

### 트레이스가 느림

**증상**: 트레이싱으로 인해 API 응답이 느려짐

**해결책**:
- LangSmith는 비동기로 데이터를 전송하므로 성능 영향이 적습니다
- 프로덕션에서는 샘플링 사용:

```python
# 10%만 트레이싱
import random

def should_trace():
    return random.random() < 0.1

if should_trace():
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
```

### API 키 노출 방지

**주의사항**:
- `.env` 파일을 Git에 커밋하지 마세요 (`.gitignore`에 포함됨)
- 프로덕션 환경에서는 환경 변수로 주입:
  ```bash
  export LANGCHAIN_API_KEY=xxx
  ```

### 비용 관리

**참고**: LangSmith는 무료 티어 제공
- 무료: 5,000 트레이스/월
- Plus: $39/월, 100,000 트레이스
- Enterprise: 커스텀 가격

자세한 가격: https://www.langchain.com/pricing

## 📊 실전 활용 예시

### 1. 디버깅: 느린 쿼리 찾기

LangSmith 대시보드에서:
1. "Traces" 탭
2. "Sort by Duration" (내림차순)
3. 가장 느린 트레이스 클릭
4. 타임라인에서 병목 구간 확인

### 2. 비용 최적화

1. "Analytics" 탭
2. "Token Usage" 차트 확인
3. 불필요하게 긴 프롬프트 식별
4. 컨텍스트 길이 조정

### 3. 에러 추적

1. "Errors" 필터 적용
2. 에러 메시지 및 스택 트레이스 확인
3. 입력값 재현하여 로컬에서 디버깅

## 🔗 추가 자료

- [LangSmith 공식 문서](https://docs.smith.langchain.com/)
- [LangChain Tracing 가이드](https://python.langchain.com/docs/langsmith/walkthrough)
- [Best Practices](https://docs.smith.langchain.com/best_practices)

## 💡 팁

1. **프로젝트 분리**: 개발/스테이징/프로덕션 환경별로 다른 프로젝트 사용
2. **태그 활용**: 트레이스에 태그 추가하여 필터링
3. **주기적 검토**: 주 1회 대시보드 확인하여 성능 트렌드 파악
4. **알림 설정**: 에러율이 임계값을 넘으면 슬랙/이메일 알림

---

**문의**: LangSmith 관련 질문은 [LangChain Discord](https://discord.gg/langchain)에서 커뮤니티 지원 받을 수 있습니다.
