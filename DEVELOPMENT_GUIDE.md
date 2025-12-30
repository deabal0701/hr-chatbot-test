# DEVELOPMENT GUIDE

HR Chatbot 프로젝트의 개발 가이드입니다. 이 문서는 일관된 코드 작성과 모듈화를 위한 표준을 제시합니다.

## 목차

1. [프로젝트 구조](#프로젝트-구조)
2. [백엔드 개발 가이드](#백엔드-개발-가이드)
3. [프론트엔드 개발 가이드](#프론트엔드-개발-가이드)
4. [데이터베이스 작업](#데이터베이스-작업)
5. [테스트 가이드](#테스트-가이드)
6. [코드 스타일 및 컨벤션](#코드-스타일-및-컨벤션)

---

## 프로젝트 구조

### 백엔드 (FastAPI + Python)

```
app/
├── main.py                    # FastAPI 애플리케이션 진입점
├── config.py                  # 설정 관리 (Pydantic Settings)
│
├── api/                       # API 라우터 레이어
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── search.py          # 검색 엔드포인트 (RAG, NL2SQL, Auto)
│       ├── documents.py       # 문서 관리 (Admin API)
│       └── settings.py        # 시스템 설정 (Admin API)
│
├── graphs/                    # LangGraph AI 워크플로우
│   ├── __init__.py
│   ├── rag_graph.py          # RAG 검색 그래프
│   └── nl2sql_graph.py       # NL2SQL 그래프
│
├── services/                  # 비즈니스 로직 서비스 레이어
│   ├── __init__.py
│   ├── vector_store.py       # 벡터 검색 및 임베딩
│   ├── sql_executor.py       # SQL 실행 및 검증
│   ├── schema_loader.py      # DB 스키마 로딩
│   └── settings_service.py   # 동적 설정 관리
│
├── models/                    # 데이터 모델
│   ├── __init__.py
│   └── schemas.py            # Pydantic 스키마 (Request/Response)
│
└── utils/                     # 유틸리티
    ├── __init__.py
    ├── database.py           # DB 연결 풀 관리
    ├── logger.py             # 로깅 설정
    ├── text_chunker.py       # 텍스트 청킹
    └── text_splitter.py      # 텍스트 분할

scripts/                       # 관리 스크립트
├── init_db.py                # DB 초기화
└── embed_documents.py        # 문서 임베딩

data/                          # 데이터 파일
└── documents.json            # 샘플 문서
```

### 프론트엔드 (Vue 3 + Vite)

```
frontend/src/
├── main.js                   # Vue 앱 진입점
├── App.vue                   # 루트 컴포넌트
├── router/                   # Vue Router
│   └── index.js
│
├── store/                    # Vuex 상태 관리
│   └── index.js
│
├── api/                      # API 클라이언트
│   ├── index.js             # Axios 인스턴스
│   ├── search.js            # 검색 API
│   ├── documents.js         # 문서 API
│   └── settings.js          # 설정 API
│
├── views/                    # 페이지 컴포넌트
│   ├── admin/               # 관리자 페이지
│   │   ├── AdminLayout.vue
│   │   ├── ChatView.vue
│   │   ├── DashboardView.vue
│   │   ├── DocumentsView.vue
│   │   ├── DocumentDetailView.vue
│   │   ├── DocumentEditView.vue
│   │   └── SettingsView.vue
│   └── user/                # 사용자 페이지
│       └── UserChatView.vue
│
├── components/               # 재사용 가능한 컴포넌트
│   ├── chat/
│   │   ├── ChatInput.vue
│   │   ├── ChatMessage.vue
│   │   └── SourceCard.vue
│   ├── documents/
│   │   └── ChunkPreview.vue
│   └── layout/
│       ├── AppHeader.vue
│       └── AppSidebar.vue
│
└── assets/                   # 정적 리소스
    └── styles/
```

---

## 백엔드 개발 가이드

### 1. 새로운 API 엔드포인트 추가하기

#### Step 1: Pydantic 스키마 정의

**위치**: `app/models/schemas.py`

```python
from typing import Optional
from pydantic import BaseModel, Field

# Request 스키마
class FeatureCreateRequest(BaseModel):
    """기능 생성 요청"""
    name: str = Field(..., description="기능 이름")
    description: Optional[str] = Field(None, description="기능 설명")
    enabled: bool = Field(default=True, description="활성화 여부")

# Response 스키마
class FeatureResponse(BaseModel):
    """기능 응답"""
    id: int
    name: str
    description: Optional[str]
    enabled: bool
    created_at: str

# 목록 응답
class FeatureListResponse(BaseModel):
    """기능 목록 응답"""
    total: int
    features: list[FeatureResponse]
```

**컨벤션**:
- Request 스키마는 `*Request` 접미사
- Response 스키마는 `*Response` 접미사
- Field에 `description` 필수 작성 (자동 API 문서화)
- 타입 힌팅 필수 사용

#### Step 2: 서비스 레이어 구현

**위치**: `app/services/feature_service.py` (새 파일 생성)

```python
from typing import List, Optional, Dict, Any
from app.utils.database import db_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class FeatureService:
    """기능 관리 서비스"""

    def create_feature(
        self,
        name: str,
        description: Optional[str] = None,
        enabled: bool = True
    ) -> Dict[str, Any]:
        """기능 생성

        Args:
            name: 기능 이름
            description: 기능 설명
            enabled: 활성화 여부

        Returns:
            생성된 기능 정보

        Raises:
            ValueError: 유효하지 않은 입력
        """
        # 입력 검증
        if not name or len(name.strip()) == 0:
            raise ValueError("기능 이름은 필수입니다")

        # DB 삽입
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO features (name, description, enabled, created_at)
                VALUES (%s, %s, %s, NOW())
                RETURNING id, name, description, enabled, created_at
            """, (name, description, enabled))

            row = cur.fetchone()

        logger.info(f"기능 생성 완료: id={row['id']}, name={row['name']}")

        return {
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'enabled': row['enabled'],
            'created_at': row['created_at'].isoformat()
        }

    def list_features(
        self,
        enabled: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int]:
        """기능 목록 조회

        Args:
            enabled: 활성화 필터 (None=전체)
            limit: 최대 결과 수
            offset: 시작 위치

        Returns:
            (기능 목록, 전체 개수)
        """
        # WHERE 절 구성
        where_clauses = []
        params = []

        if enabled is not None:
            where_clauses.append("enabled = %s")
            params.append(enabled)

        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        with db_manager.get_cursor() as cur:
            # 전체 개수
            cur.execute(f"SELECT COUNT(*) as count FROM features {where_sql}", params)
            total = cur.fetchone()['count']

            # 목록 조회
            cur.execute(f"""
                SELECT id, name, description, enabled, created_at
                FROM features
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [limit, offset])

            features = []
            for row in cur.fetchall():
                features.append({
                    'id': row['id'],
                    'name': row['name'],
                    'description': row['description'],
                    'enabled': row['enabled'],
                    'created_at': row['created_at'].isoformat()
                })

        return features, total

# 싱글톤 인스턴스
feature_service = FeatureService()
```

**서비스 레이어 컨벤션**:
- 클래스명: `*Service`
- 메서드는 비즈니스 로직에 집중
- DB 작업은 `db_manager.get_cursor()` 사용
- 읽기 전용: `get_cursor()`
- 쓰기 작업: `get_cursor(commit=True)`
- 상세한 docstring 작성 (Args, Returns, Raises)
- 입력 검증 포함
- 로깅 포함 (성공/실패)
- 싱글톤 인스턴스 export

#### Step 3: 라우터 생성

**위치**: `app/api/routes/features.py` (새 파일 생성)

```python
"""기능 관리 API 라우터"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.schemas import (
    FeatureCreateRequest,
    FeatureResponse,
    FeatureListResponse,
)
from app.services.feature_service import feature_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 라우터 생성
router = APIRouter(
    prefix="/api/v1/features",
    tags=["features"]
)


@router.post("", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED)
async def create_feature(request: FeatureCreateRequest):
    """
    기능 생성

    새로운 기능을 생성합니다.
    """
    try:
        result = feature_service.create_feature(
            name=request.name,
            description=request.description,
            enabled=request.enabled
        )

        return FeatureResponse(**result)

    except ValueError as e:
        # 비즈니스 로직 오류 (400)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # 시스템 오류 (500)
        logger.error(f"기능 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기능 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("", response_model=FeatureListResponse)
async def list_features(
    enabled: Optional[bool] = Query(None, description="활성화 필터"),
    limit: int = Query(100, ge=1, le=1000, description="최대 결과 수"),
    offset: int = Query(0, ge=0, description="시작 위치")
):
    """
    기능 목록 조회

    - enabled 파라미터로 활성화 여부 필터링
    - 페이지네이션 지원 (limit, offset)
    """
    try:
        features, total = feature_service.list_features(
            enabled=enabled,
            limit=limit,
            offset=offset
        )

        return FeatureListResponse(
            total=total,
            features=[FeatureResponse(**f) for f in features]
        )

    except Exception as e:
        logger.error(f"기능 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기능 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{feature_id}", response_model=FeatureResponse)
async def get_feature(feature_id: int):
    """
    기능 상세 조회

    특정 기능의 상세 정보를 조회합니다.
    """
    try:
        feature = feature_service.get_feature(feature_id)

        if not feature:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"기능을 찾을 수 없습니다: ID={feature_id}"
            )

        return FeatureResponse(**feature)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"기능 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"기능 조회 중 오류가 발생했습니다: {str(e)}"
        )
```

**라우터 컨벤션**:
- 파일명: 복수형 (features.py, documents.py)
- `APIRouter` prefix와 tags 설정
- `async def` 사용 (FastAPI 비동기)
- Query 파라미터에 `Query()` 사용하여 문서화
- 상세한 docstring (자동 API 문서에 표시)
- 예외 처리 3단계:
  1. `ValueError` → 400 Bad Request
  2. `HTTPException` → 그대로 전파
  3. `Exception` → 500 Internal Server Error
- 로깅 포함 (에러 발생 시)

#### Step 4: 메인 앱에 라우터 등록

**위치**: `app/main.py`

```python
# 기존 import에 추가
from app.api.routes import features

# 라우터 등록 섹션에 추가
app.include_router(features.router)
```

**컨벤션**:
- 라우터는 기능별로 그룹화
- 등록 순서: 공개 API → 관리자 API

---

### 2. LangGraph 워크플로우 추가하기

LangGraph는 AI 워크플로우를 상태 머신으로 구현하는 프레임워크입니다.

#### 워크플로우 구조

```python
from typing import Any, Dict, TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# Step 1: State 정의
class MyWorkflowState(TypedDict):
    """워크플로우 상태"""
    input: str              # 입력
    processed: str          # 처리된 데이터
    result: str             # 최종 결과
    metadata: Dict[str, Any]  # 메타데이터
    request_id: str         # 추적 ID


# Step 2: Graph 클래스 정의
class MyWorkflowGraph:
    """커스텀 워크플로우 그래프"""

    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """그래프 구성"""
        workflow = StateGraph(MyWorkflowState)

        # 노드 추가
        workflow.add_node("step1", self._step1)
        workflow.add_node("step2", self._step2)
        workflow.add_node("step3", self._step3)

        # 엣지 정의 (순서)
        workflow.set_entry_point("step1")
        workflow.add_edge("step1", "step2")

        # 조건부 엣지
        workflow.add_conditional_edges(
            "step2",
            self._should_continue,
            {
                "continue": "step3",
                "end": END
            }
        )

        workflow.add_edge("step3", END)

        return workflow.compile()

    def _step1(self, state: MyWorkflowState) -> MyWorkflowState:
        """첫 번째 단계"""
        request_id = state.get("request_id", "unknown")
        logger.info(f"[{request_id}] [STEP-1] 처리 시작")

        # 처리 로직
        processed = state["input"].upper()
        state["processed"] = processed

        logger.info(f"[{request_id}] [STEP-1] 처리 완료")
        return state

    def _step2(self, state: MyWorkflowState) -> MyWorkflowState:
        """두 번째 단계"""
        request_id = state.get("request_id", "unknown")
        logger.info(f"[{request_id}] [STEP-2] 검증 시작")

        # 검증 로직
        is_valid = len(state["processed"]) > 0
        state["metadata"]["is_valid"] = is_valid

        logger.info(f"[{request_id}] [STEP-2] 검증 완료: {is_valid}")
        return state

    def _should_continue(self, state: MyWorkflowState) -> str:
        """조건부 분기 결정"""
        return "continue" if state["metadata"]["is_valid"] else "end"

    def _step3(self, state: MyWorkflowState) -> MyWorkflowState:
        """세 번째 단계"""
        request_id = state.get("request_id", "unknown")
        logger.info(f"[{request_id}] [STEP-3] 최종 처리 시작")

        # 최종 결과 생성
        state["result"] = f"Result: {state['processed']}"

        logger.info(f"[{request_id}] [STEP-3] 완료")
        return state

    async def ainvoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """비동기 실행"""
        initial_state: MyWorkflowState = {
            "input": inputs["input"],
            "processed": "",
            "result": "",
            "metadata": {},
            "request_id": inputs.get("request_id", "unknown")
        }

        result = await self.graph.ainvoke(initial_state)
        return result

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """동기 실행"""
        initial_state: MyWorkflowState = {
            "input": inputs["input"],
            "processed": "",
            "result": "",
            "metadata": {},
            "request_id": inputs.get("request_id", "unknown")
        }

        result = self.graph.invoke(initial_state)
        return result


# 싱글톤 인스턴스
my_workflow_graph = MyWorkflowGraph()
```

**LangGraph 컨벤션**:
- State는 `TypedDict`로 정의
- 노드 메서드는 `_`로 시작 (private)
- 노드는 `state`를 받아서 수정된 `state` 반환
- `ainvoke`와 `invoke` 모두 구현
- 상세한 로깅 (각 단계마다)
- `request_id`로 추적 가능하게

---

### 3. 데이터베이스 작업

#### DB 연결 사용

```python
from app.utils.database import db_manager

# 읽기 전용 쿼리
with db_manager.get_cursor() as cur:
    cur.execute("SELECT * FROM table WHERE id = %s", (id,))
    row = cur.fetchone()
    rows = cur.fetchall()

# 쓰기 쿼리 (INSERT, UPDATE, DELETE)
with db_manager.get_cursor(commit=True) as cur:
    cur.execute("""
        INSERT INTO table (name, value)
        VALUES (%s, %s)
        RETURNING id
    """, (name, value))
    new_id = cur.fetchone()['id']
```

**DB 컨벤션**:
- **절대 문자열 포맷팅 금지** (SQL Injection 방지)
  - ❌ `f"SELECT * FROM table WHERE id = {id}"`
  - ✅ `"SELECT * FROM table WHERE id = %s", (id,)`
- `fetchone()` → dict (RealDictCursor)
- `fetchall()` → list[dict]
- 트랜잭션이 필요한 경우 `commit=True`
- 긴 쿼리는 여러 줄로 (Triple quotes)

#### 테이블 생성 스크립트

**위치**: `scripts/init_db.py`에 추가

```python
CREATE_FEATURES_TABLE = """
CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

CREATE INDEX idx_features_enabled ON features(enabled);
"""
```

---

## 프론트엔드 개발 가이드

### 1. API 클라이언트 추가

#### Step 1: API 모듈 생성

**위치**: `frontend/src/api/features.js` (새 파일)

```javascript
import apiClient from './index'

// 기능 관리 API
export default {
  /**
   * 기능 목록 조회
   * @param {Object} params - 조회 파라미터
   * @returns {Promise}
   */
  list(params = {}) {
    return apiClient.get('/api/v1/features', { params })
  },

  /**
   * 기능 상세 조회
   * @param {number} featureId - 기능 ID
   * @returns {Promise}
   */
  get(featureId) {
    return apiClient.get(`/api/v1/features/${featureId}`)
  },

  /**
   * 기능 생성
   * @param {Object} data - 기능 데이터
   * @returns {Promise}
   */
  create(data) {
    return apiClient.post('/api/v1/features', {
      name: data.name,
      description: data.description,
      enabled: data.enabled ?? true
    })
  },

  /**
   * 기능 수정
   * @param {number} featureId - 기능 ID
   * @param {Object} data - 수정할 데이터
   * @returns {Promise}
   */
  update(featureId, data) {
    return apiClient.put(`/api/v1/features/${featureId}`, data)
  },

  /**
   * 기능 삭제
   * @param {number} featureId - 기능 ID
   * @returns {Promise}
   */
  delete(featureId) {
    return apiClient.delete(`/api/v1/features/${featureId}`)
  }
}
```

**API 클라이언트 컨벤션**:
- 파일명: 백엔드 라우터와 일치
- Export default object
- JSDoc 주석 필수
- camelCase 사용 (JavaScript)
- snake_case ↔ camelCase 변환 처리

### 2. Vuex Store 모듈 추가

**위치**: `frontend/src/store/modules/features.js` (새 파일)

```javascript
import featuresApi from '@/api/features'
import { ElMessage } from 'element-plus'

const state = {
  features: [],
  currentFeature: null,
  loading: false,
  total: 0
}

const getters = {
  enabledFeatures: (state) => {
    return state.features.filter(f => f.enabled)
  }
}

const mutations = {
  SET_FEATURES(state, features) {
    state.features = features
  },

  SET_CURRENT_FEATURE(state, feature) {
    state.currentFeature = feature
  },

  SET_LOADING(state, loading) {
    state.loading = loading
  },

  SET_TOTAL(state, total) {
    state.total = total
  },

  ADD_FEATURE(state, feature) {
    state.features.unshift(feature)
    state.total += 1
  },

  UPDATE_FEATURE(state, updatedFeature) {
    const index = state.features.findIndex(f => f.id === updatedFeature.id)
    if (index !== -1) {
      state.features.splice(index, 1, updatedFeature)
    }
  },

  REMOVE_FEATURE(state, featureId) {
    const index = state.features.findIndex(f => f.id === featureId)
    if (index !== -1) {
      state.features.splice(index, 1)
      state.total -= 1
    }
  }
}

const actions = {
  async fetchFeatures({ commit }, params = {}) {
    commit('SET_LOADING', true)
    try {
      const response = await featuresApi.list(params)
      commit('SET_FEATURES', response.data.features)
      commit('SET_TOTAL', response.data.total)
    } catch (error) {
      ElMessage.error('기능 목록 조회 실패: ' + error.message)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  async fetchFeature({ commit }, featureId) {
    commit('SET_LOADING', true)
    try {
      const response = await featuresApi.get(featureId)
      commit('SET_CURRENT_FEATURE', response.data)
      return response.data
    } catch (error) {
      ElMessage.error('기능 조회 실패: ' + error.message)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },

  async createFeature({ commit }, data) {
    try {
      const response = await featuresApi.create(data)
      commit('ADD_FEATURE', response.data)
      ElMessage.success('기능이 생성되었습니다')
      return response.data
    } catch (error) {
      ElMessage.error('기능 생성 실패: ' + error.message)
      throw error
    }
  },

  async updateFeature({ commit }, { featureId, data }) {
    try {
      const response = await featuresApi.update(featureId, data)
      commit('UPDATE_FEATURE', response.data)
      ElMessage.success('기능이 수정되었습니다')
      return response.data
    } catch (error) {
      ElMessage.error('기능 수정 실패: ' + error.message)
      throw error
    }
  },

  async deleteFeature({ commit }, featureId) {
    try {
      await featuresApi.delete(featureId)
      commit('REMOVE_FEATURE', featureId)
      ElMessage.success('기능이 삭제되었습니다')
    } catch (error) {
      ElMessage.error('기능 삭제 실패: ' + error.message)
      throw error
    }
  }
}

export default {
  namespaced: true,
  state,
  getters,
  mutations,
  actions
}
```

**Vuex 컨벤션**:
- `namespaced: true` 필수
- Mutation: 대문자 + 언더스코어
- Action: camelCase
- 에러 처리: `ElMessage` 사용
- Loading 상태 관리

**Store 등록**: `frontend/src/store/index.js`

```javascript
import features from './modules/features'

export default createStore({
  modules: {
    features
  }
})
```

### 3. Vue 컴포넌트 작성

#### 목록 페이지 예시

**위치**: `frontend/src/views/admin/FeaturesView.vue`

```vue
<template>
  <div class="features-view">
    <!-- 헤더 -->
    <div class="page-header">
      <div>
        <h2>기능 관리</h2>
        <p class="subtitle">시스템 기능을 관리합니다</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="showCreateDialog">
        새 기능
      </el-button>
    </div>

    <!-- 필터 -->
    <div class="content-card filter-section">
      <el-select
        v-model="filters.enabled"
        placeholder="활성화 상태"
        clearable
        style="width: 150px"
        @change="handleFilterChange"
      >
        <el-option label="활성화됨" :value="true" />
        <el-option label="비활성화됨" :value="false" />
      </el-select>

      <el-button :icon="Refresh" @click="resetFilters">
        초기화
      </el-button>
    </div>

    <!-- 테이블 -->
    <div class="content-card">
      <el-table
        v-loading="loading"
        :data="features"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />

        <el-table-column prop="name" label="이름" min-width="200" />

        <el-table-column prop="description" label="설명" min-width="300" />

        <el-table-column label="상태" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'">
              {{ row.enabled ? '활성' : '비활성' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="작업" width="150" align="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              text
              :icon="Edit"
              @click="handleEdit(row)"
            >
              수정
            </el-button>
            <el-button
              type="danger"
              text
              :icon="Delete"
              @click="handleDelete(row)"
            >
              삭제
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 페이지네이션 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <!-- 생성/수정 다이얼로그 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '기능 수정' : '새 기능'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="이름" prop="name">
          <el-input v-model="form.name" placeholder="기능 이름" />
        </el-form-item>

        <el-form-item label="설명" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="기능 설명"
          />
        </el-form-item>

        <el-form-item label="활성화">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">취소</el-button>
        <el-button type="primary" @click="handleSubmit">
          {{ isEdit ? '수정' : '생성' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Refresh } from '@element-plus/icons-vue'

const store = useStore()

// State
const loading = computed(() => store.state.features.loading)
const features = computed(() => store.state.features.features)
const total = computed(() => store.state.features.total)

const filters = ref({
  enabled: null
})

const currentPage = ref(1)
const pageSize = ref(20)

const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)

const form = ref({
  id: null,
  name: '',
  description: '',
  enabled: true
})

const rules = {
  name: [
    { required: true, message: '이름을 입력하세요', trigger: 'blur' },
    { min: 2, max: 100, message: '2-100자로 입력하세요', trigger: 'blur' }
  ]
}

// Methods
const fetchData = async () => {
  await store.dispatch('features/fetchFeatures', {
    enabled: filters.value.enabled,
    limit: pageSize.value,
    offset: (currentPage.value - 1) * pageSize.value
  })
}

const handleFilterChange = () => {
  currentPage.value = 1
  fetchData()
}

const resetFilters = () => {
  filters.value = { enabled: null }
  currentPage.value = 1
  fetchData()
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchData()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

const showCreateDialog = () => {
  isEdit.value = false
  form.value = {
    id: null,
    name: '',
    description: '',
    enabled: true
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  form.value = { ...row }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  const valid = await formRef.value.validate()
  if (!valid) return

  try {
    if (isEdit.value) {
      await store.dispatch('features/updateFeature', {
        featureId: form.value.id,
        data: form.value
      })
    } else {
      await store.dispatch('features/createFeature', form.value)
    }

    dialogVisible.value = false
    fetchData()
  } catch (error) {
    // Error already handled in store
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `"${row.name}" 기능을 삭제하시겠습니까?`,
      '삭제 확인',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )

    await store.dispatch('features/deleteFeature', row.id)
    fetchData()
  } catch (error) {
    // User cancelled or error
  }
}

// Lifecycle
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.features-view {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 4px 0;
  font-size: 24px;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.content-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.filter-section {
  display: flex;
  gap: 12px;
  align-items: center;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
```

**Vue 컴포넌트 컨벤션**:
- Composition API (`<script setup>`) 사용
- Element Plus UI 라이브러리 사용
- 페이지 컴포넌트: `*View.vue`
- 재사용 컴포넌트: 명확한 이름
- Props validation 필수
- Emit events 명시
- Scoped styles 사용

---

## 데이터베이스 작업

### 1. 마이그레이션 가이드

현재 프로젝트는 간단한 스크립트 기반 마이그레이션을 사용합니다.

**새 테이블 추가**:

```python
# scripts/init_db.py 수정

CREATE_FEATURES_TABLE = """
CREATE TABLE IF NOT EXISTS features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,

    -- 인덱스
    CONSTRAINT features_name_check CHECK (char_length(name) >= 2)
);

CREATE INDEX IF NOT EXISTS idx_features_enabled ON features(enabled);
CREATE INDEX IF NOT EXISTS idx_features_created_at ON features(created_at DESC);

COMMENT ON TABLE features IS '시스템 기능 관리';
COMMENT ON COLUMN features.name IS '기능 이름 (고유)';
COMMENT ON COLUMN features.description IS '기능 설명';
"""

# main() 함수에 추가
conn.execute(CREATE_FEATURES_TABLE)
```

### 2. 쿼리 작성 베스트 프랙티스

```python
# ✅ GOOD: 파라미터 바인딩
cur.execute("""
    SELECT * FROM users
    WHERE email = %s AND status = %s
""", (email, status))

# ❌ BAD: 문자열 포맷팅 (SQL Injection 위험!)
cur.execute(f"""
    SELECT * FROM users
    WHERE email = '{email}'
""")

# ✅ GOOD: 복잡한 WHERE 절 구성
where_clauses = []
params = []

if email:
    where_clauses.append("email = %s")
    params.append(email)

if status:
    where_clauses.append("status = %s")
    params.append(status)

where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

cur.execute(f"""
    SELECT * FROM users
    {where_sql}
    ORDER BY created_at DESC
""", params)

# ✅ GOOD: JSON 타입 사용
import psycopg.types.json

cur.execute("""
    INSERT INTO documents (metadata)
    VALUES (%s)
""", (psycopg.types.json.Json({"key": "value"}),))

# ✅ GOOD: 배열 타입 (PostgreSQL)
cur.execute("""
    SELECT * FROM documents
    WHERE id = ANY(%s)
""", ([1, 2, 3],))
```

---

## 테스트 가이드

### 1. 백엔드 테스트

**위치**: `tests/` (생성 필요)

```python
# tests/test_features.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_feature():
    """기능 생성 테스트"""
    response = client.post("/api/v1/features", json={
        "name": "Test Feature",
        "description": "Test Description",
        "enabled": True
    })

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Feature"
    assert "id" in data


def test_list_features():
    """기능 목록 조회 테스트"""
    response = client.get("/api/v1/features")

    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "features" in data
    assert isinstance(data["features"], list)


def test_create_feature_invalid():
    """잘못된 입력 테스트"""
    response = client.post("/api/v1/features", json={
        "name": "",  # 빈 이름
        "enabled": True
    })

    assert response.status_code == 400
```

**실행**:
```bash
pytest tests/ -v
```

### 2. 프론트엔드 테스트

```javascript
// tests/unit/features.spec.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FeaturesView from '@/views/admin/FeaturesView.vue'

describe('FeaturesView', () => {
  it('renders properly', () => {
    const wrapper = mount(FeaturesView)
    expect(wrapper.find('h2').text()).toBe('기능 관리')
  })
})
```

---

## 코드 스타일 및 컨벤션

### Python (Backend)

```python
# 1. Import 순서
import os                          # 표준 라이브러리
import sys

from typing import List, Optional  # 타입 힌팅

import numpy as np                 # 서드파티
from fastapi import FastAPI

from app.config import settings    # 로컬 모듈
from app.utils.logger import logger


# 2. 함수/메서드 docstring
def calculate_score(
    value: float,
    threshold: float = 0.5
) -> tuple[bool, float]:
    """점수를 계산하고 임계값과 비교

    Args:
        value: 입력 값
        threshold: 임계값 (기본: 0.5)

    Returns:
        (통과 여부, 계산된 점수)

    Raises:
        ValueError: value가 음수인 경우

    Examples:
        >>> calculate_score(0.8)
        (True, 0.8)
    """
    if value < 0:
        raise ValueError("value는 0 이상이어야 합니다")

    passed = value >= threshold
    return passed, value


# 3. 클래스
class DataProcessor:
    """데이터 처리 클래스

    Attributes:
        config: 설정 딕셔너리
        cache: 캐시 저장소
    """

    def __init__(self, config: dict):
        self.config = config
        self.cache = {}

    def process(self, data: list) -> list:
        """데이터 처리"""
        # 구현
        pass


# 4. 상수
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"


# 5. 네이밍
# - 변수/함수: snake_case
# - 클래스: PascalCase
# - 상수: UPPER_SNAKE_CASE
# - Private: _leading_underscore
```

### JavaScript/Vue (Frontend)

```javascript
// 1. 변수 선언
const MAX_ITEMS = 100  // 상수: UPPER_SNAKE_CASE
let currentPage = 1    // 변수: camelCase
const userName = 'John'

// 2. 함수
/**
 * 사용자 데이터를 가져옵니다
 * @param {number} userId - 사용자 ID
 * @returns {Promise<Object>} 사용자 데이터
 */
async function fetchUserData(userId) {
  const response = await api.get(`/users/${userId}`)
  return response.data
}

// 3. 컴포넌트 네이밍
// - PascalCase: UserProfile.vue, ChatMessage.vue
// - kebab-case in template: <user-profile />, <chat-message />

// 4. Props
const props = defineProps({
  userId: {
    type: Number,
    required: true
  },
  userName: {
    type: String,
    default: ''
  },
  options: {
    type: Object,
    default: () => ({})
  }
})

// 5. Emit
const emit = defineEmits(['update', 'delete'])
emit('update', newData)
```

---

## 로깅 가이드

```python
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 레벨별 사용
logger.debug("상세 디버그 정보")           # 개발 시
logger.info("일반 정보 메시지")            # 주요 동작
logger.warning("경고 메시지")             # 주의 필요
logger.error("에러 발생", exc_info=True)  # 에러 (스택 트레이스 포함)

# 구조화된 로깅
logger.info(
    f"[{request_id}] [API] 요청 처리 완료",
    extra={
        "request_id": request_id,
        "endpoint": "/api/v1/search",
        "duration_ms": 1234,
        "status": "success"
    }
)
```

---

## 환경변수 관리

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 새 설정 추가
    new_api_key: str = Field(..., description="새 API 키")
    new_timeout: int = Field(default=30, description="타임아웃(초)")

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
```

`.env` 파일:
```bash
NEW_API_KEY=your-api-key-here
NEW_TIMEOUT=60
```

---

## 체크리스트

### 새 기능 추가 시

- [ ] Pydantic 스키마 정의 (`app/models/schemas.py`)
- [ ] 서비스 레이어 구현 (`app/services/*.py`)
- [ ] 라우터 생성 (`app/api/routes/*.py`)
- [ ] 메인 앱에 라우터 등록 (`app/main.py`)
- [ ] DB 테이블/마이그레이션 (`scripts/init_db.py`)
- [ ] API 클라이언트 (`frontend/src/api/*.js`)
- [ ] Vuex 스토어 모듈 (`frontend/src/store/modules/*.js`)
- [ ] Vue 컴포넌트 (`frontend/src/views/**/*.vue`)
- [ ] 테스트 작성
- [ ] 문서 업데이트

### 코드 리뷰 체크리스트

- [ ] 타입 힌팅 사용
- [ ] Docstring 작성
- [ ] 에러 처리
- [ ] 로깅 추가
- [ ] SQL Injection 방지
- [ ] 입력 검증
- [ ] 트랜잭션 처리 (필요 시)
- [ ] 성능 고려 (N+1 쿼리 등)
- [ ] 보안 고려
- [ ] 테스트 통과

---

## 추가 리소스

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Vue 3 공식 문서](https://vuejs.org/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [Pydantic 문서](https://docs.pydantic.dev/)
- [Element Plus 문서](https://element-plus.org/)

---

**작성일**: 2025-12-30
**버전**: 1.0.0
**관리**: 개발팀
