"""
Tools 패키지

AI Agent가 사용할 수 있는 도구들을 정의합니다.

확장성:
- 새로운 도구는 BaseTool을 상속하여 추가
- ToolRegistry에 자동 등록
- 플러그인 방식으로 동적 로드 가능
"""

from app.tools.base import BaseTool, ToolResult, ToolRegistry
from app.tools.sql_tool import SQLQueryTool
from app.tools.rag_tool import DocumentSearchTool
from app.tools.calculator_tool import CalculatorTool

# 도구 레지스트리 (확장 가능)
AVAILABLE_TOOLS = [
    SQLQueryTool,
    DocumentSearchTool,
    CalculatorTool,
]

__all__ = [
    "BaseTool",
    "ToolResult",
    "ToolRegistry",
    "SQLQueryTool",
    "DocumentSearchTool",
    "CalculatorTool",
    "AVAILABLE_TOOLS",
]
