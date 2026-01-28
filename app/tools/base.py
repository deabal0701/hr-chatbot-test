"""
Tool 베이스 클래스 및 레지스트리

확장성:
- BaseTool: 모든 도구의 추상 베이스 클래스
- ToolResult: 표준화된 결과 포맷
- ToolRegistry: 도구 자동 등록 및 관리
- ToolValidator: 입력/출력 검증 (보안)
- ToolMetrics: 도구 사용 메트릭 수집
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Type
from datetime import datetime
from pydantic import BaseModel, Field
import time

from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class ToolResult(BaseModel):
    """Tool 실행 결과 (표준화)"""
    success: bool = Field(..., description="실행 성공 여부")
    data: Any = Field(None, description="결과 데이터")
    error: Optional[str] = Field(None, description="에러 메시지")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="메타데이터")
    execution_time_ms: int = Field(0, description="실행 시간(ms)")

    class Config:
        arbitrary_types_allowed = True


class ToolValidator:
    """Tool 입력/출력 검증 (보안 강화)"""

    @staticmethod
    def validate_input(tool_name: str, required_params: Optional[List[str]] = None, **kwargs) -> tuple[bool, Optional[str]]:
        """
        Tool 입력 검증

        Args:
            tool_name: 도구 이름
            required_params: 필수 파라미터 목록 (None이면 모든 None 값 거부)
            **kwargs: 검증할 파라미터들

        확장 포인트:
        - SQL Injection 방지
        - Path Traversal 방지
        - XSS 방지
        - 민감 정보 필터링
        """
        # 필수 파라미터만 None 체크 (선택적 파라미터는 허용)
        if required_params is not None:
            # 명시적으로 required_params가 제공된 경우, 해당 파라미터만 검증
            for param in required_params:
                if param in kwargs and kwargs[param] is None:
                    return False, f"Required parameter '{param}' is None"
                elif param not in kwargs:
                    return False, f"Required parameter '{param}' is missing"
        # else: required_params가 None이면 검증 스킵 (하위 호환성)

        # 도구별 커스텀 검증 (확장 가능)
        if tool_name == "SQLQueryTool":
            question = kwargs.get("question", "")
            # 위험한 패턴 체크
            dangerous_patterns = ["--", "/*", "*/", "xp_", "sp_"]
            for pattern in dangerous_patterns:
                if pattern in question.lower():
                    log_step("SYSTEM", "TOOL", tool_name, "VALIDATE", f"Suspicious pattern detected: {pattern}", level="WARNING")

        return True, None

    @staticmethod
    def validate_output(tool_name: str, result: ToolResult) -> tuple[bool, Optional[str]]:
        """
        Tool 출력 검증

        확장 포인트:
        - 민감 정보 마스킹 (주민번호, 계좌번호 등)
        - 출력 크기 제한
        - 포맷 검증
        """
        # 출력 크기 제한 (10MB)
        max_size = 10 * 1024 * 1024
        data_str = str(result.data)
        if len(data_str) > max_size:
            return False, f"Output size exceeds limit: {len(data_str)} > {max_size}"

        return True, None


class ToolMetrics:
    """Tool 사용 메트릭 수집 (확장성)"""

    _metrics: Dict[str, List[Dict[str, Any]]] = {}

    @classmethod
    def record(cls, tool_name: str, execution_time_ms: int, success: bool, error: Optional[str] = None):
        """메트릭 기록"""
        if tool_name not in cls._metrics:
            cls._metrics[tool_name] = []

        cls._metrics[tool_name].append({
            "timestamp": datetime.now().isoformat(),
            "execution_time_ms": execution_time_ms,
            "success": success,
            "error": error
        })

        # 메모리 관리: 최근 1000개만 유지
        if len(cls._metrics[tool_name]) > 1000:
            cls._metrics[tool_name] = cls._metrics[tool_name][-1000:]

    @classmethod
    def get_stats(cls, tool_name: str) -> Dict[str, Any]:
        """도구별 통계"""
        if tool_name not in cls._metrics or not cls._metrics[tool_name]:
            return {"total_calls": 0}

        records = cls._metrics[tool_name]
        total = len(records)
        success_count = sum(1 for r in records if r["success"])
        avg_time = sum(r["execution_time_ms"] for r in records) / total

        return {
            "total_calls": total,
            "success_rate": success_count / total,
            "avg_execution_time_ms": avg_time,
            "last_used": records[-1]["timestamp"]
        }


class BaseTool(ABC):
    """
    모든 Tool의 베이스 클래스

    확장 포인트:
    - before_execute(): 전처리 훅
    - after_execute(): 후처리 훅
    - validate(): 커스텀 검증
    """

    def __init__(self):
        self.validator = ToolValidator()
        self.enabled = True  # 동적 활성화/비활성화

    @property
    @abstractmethod
    def name(self) -> str:
        """도구 이름 (LangChain function name)"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """도구 설명 (LLM이 읽는 설명)"""
        pass

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """
        파라미터 스키마 (JSON Schema)

        확장 포인트: 각 도구가 오버라이드하여 정의
        """
        return {}

    @abstractmethod
    def _execute(self, **kwargs) -> ToolResult:
        """실제 실행 로직 (서브클래스에서 구현)"""
        pass

    def before_execute(self, **kwargs) -> Dict[str, Any]:
        """
        전처리 훅

        확장 포인트:
        - 입력 변환
        - 캐싱 체크
        - 인증/인가
        """
        return kwargs

    def after_execute(self, result: ToolResult) -> ToolResult:
        """
        후처리 훅

        확장 포인트:
        - 결과 변환
        - 캐싱 저장
        - 알림 발송
        """
        return result

    def execute(self, **kwargs) -> ToolResult:
        """
        도구 실행 (템플릿 메서드 패턴)

        순서:
        1. 활성화 체크
        2. 입력 검증
        3. 전처리
        4. 실제 실행
        5. 출력 검증
        6. 후처리
        7. 메트릭 기록
        """
        start_time = time.time()

        try:
            # 1. 활성화 체크
            if not self.enabled:
                return ToolResult(
                    success=False,
                    error=f"Tool '{self.name}' is disabled",
                    metadata={"disabled": True}
                ) # type: ignore

            # 2. 입력 검증 (스키마 기반)
            # 스키마에서 required 파라미터 목록 추출
            schema = self.parameters_schema
            required_params = schema.get("required", []) if schema else None

            valid, error_msg = self.validator.validate_input(
                self.name,
                required_params=required_params,
                **kwargs
            )
            if not valid:
                log_step("SYSTEM", "TOOL", self.name, "VALIDATE", f"Input validation failed: {error_msg}", level="WARNING")
                return ToolResult(
                    success=False,
                    error=f"Input validation failed: {error_msg}",
                    metadata={"validation_error": True}
                ) # type: ignore

            # 3. 전처리
            kwargs = self.before_execute(**kwargs)

            # 4. 실제 실행
            log_step("SYSTEM", "TOOL", self.name, "EXECUTE", "도구 실행 시작", level="DEBUG", params=list(kwargs.keys()))
            result = self._execute(**kwargs)

            # 5. 출력 검증
            valid, error_msg = self.validator.validate_output(self.name, result)
            if not valid:
                log_step("SYSTEM", "TOOL", self.name, "VALIDATE", f"Output validation failed: {error_msg}", level="WARNING")
                result.success = False
                result.error = error_msg

            # 6. 후처리
            result = self.after_execute(result)

            # 실행 시간 기록
            execution_time_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time_ms

            # 7. 메트릭 기록
            ToolMetrics.record(self.name, execution_time_ms, result.success, result.error)

            log_step("SYSTEM", "TOOL", self.name, "COMPLETE", "도구 실행 완료", level="DEBUG", success=result.success, time_ms=execution_time_ms)
            return result

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            log_step("SYSTEM", "TOOL", self.name, "ERROR", f"도구 실행 실패: {e}", level="ERROR")

            # 메트릭 기록
            ToolMetrics.record(self.name, execution_time_ms, False, str(e))

            return ToolResult(
                success=False,
                error=f"Tool execution error: {str(e)}",
                metadata={"exception": type(e).__name__},
                execution_time_ms=execution_time_ms
            ) # type: ignore


class ToolRegistry:
    """
    Tool 레지스트리 (싱글톤)

    확장 포인트:
    - 동적 도구 등록/해제
    - 도구 버전 관리
    - 도구 권한 관리
    """

    _instance = None
    _tools: Dict[str, Type[BaseTool]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, tool_class: Type[BaseTool]):
        """도구 등록"""
        tool_instance = tool_class()
        self._tools[tool_instance.name] = tool_class
        log_step("SYSTEM", "TOOL", tool_instance.name, "REGISTER", "도구 등록 완료")

    def unregister(self, tool_name: str):
        """도구 해제"""
        if tool_name in self._tools:
            del self._tools[tool_name]
            log_step("SYSTEM", "TOOL", tool_name, "UNREGISTER", "도구 해제 완료")

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """도구 가져오기"""
        tool_class = self._tools.get(tool_name)
        if tool_class:
            return tool_class()
        return None

    def list_tools(self) -> List[str]:
        """등록된 도구 목록"""
        return list(self._tools.keys())

    def get_all_tools(self) -> List[BaseTool]:
        """모든 도구 인스턴스"""
        return [tool_class() for tool_class in self._tools.values()]

    def get_tools_info(self) -> List[Dict[str, Any]]:
        """도구 정보 목록 (메타데이터 포함)"""
        info = []
        for tool_class in self._tools.values():
            tool = tool_class()
            stats = ToolMetrics.get_stats(tool.name)
            info.append({
                "name": tool.name,
                "description": tool.description,
                "enabled": tool.enabled,
                "stats": stats
            })
        return info
