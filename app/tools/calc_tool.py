"""
계산기 도구

기능:
- 안전한 수식 계산 (AST 파싱)
- 기본 산술 연산
- 통계 함수 (확장)

확장성:
- 통계 함수: mean, median, std
- 재무 함수: 이자 계산, 환율 변환
- 날짜 계산: 근무일수, 기간 계산
"""

from typing import Dict, Any
import ast
import operator
import math
from langchain_core.tools import tool

from app.tools.base import BaseTool, ToolResult
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CalculatorTool(BaseTool):
    """계산기 도구"""

    # 허용된 연산자
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
    }

    # 허용된 함수 (확장 가능)
    ALLOWED_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "len": len,
        "pow": pow,
        "sqrt": math.sqrt,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    @property
    def name(self) -> str:
        return "calculate"

    @property
    def description(self) -> str:
        return """Perform mathematical calculations.

Use this tool when you need to:
- Calculate percentages, averages, sums (e.g., "what is 15% of 100?")
- Perform arithmetic operations (e.g., "(50+30)/2")
- Compare numeric values (e.g., "100 * 1.15")
- Statistical calculations (e.g., "average of [10, 20, 30]")

DO NOT use this tool for:
- Database queries (use query_database instead)
- Document searches (use search_documents instead)

Supported operations:
- Basic: +, -, *, /, //, %, **
- Functions: abs, round, min, max, sum, len, pow, sqrt, ceil, floor

Args:
    expression: Mathematical expression as string

Returns:
    Calculation result

Examples:
    - "100 * 0.15" → 15.0
    - "(5000 + 6000) / 2" → 5500.0
    - "sum([10, 20, 30])" → 60
    - "round(123.456, 2)" → 123.46

Safety: Only supports whitelisted operations (no eval(), no exec())
"""

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression (e.g., '100 * 1.15', 'sum([10,20,30])')"
                }
            },
            "required": ["expression"]
        }

    def _execute(self, expression: str, **kwargs) -> ToolResult:
        """실제 실행 로직"""

        try:
            # 공백 제거 및 정리
            expression = expression.strip()

            logger.info(f"[{self.name}] Evaluating: {expression}")

            # AST 파싱
            tree = ast.parse(expression, mode='eval')

            # 안전 평가
            result = self._safe_eval(tree.body)

            # 결과 포맷팅 (소수점 4자리까지)
            if isinstance(result, float):
                result = round(result, 4)

            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "original_expression": expression,
                    "result_type": type(result).__name__
                }
            ) # type: ignore

        except SyntaxError as e:
            logger.error(f"[{self.name}] Syntax error: {e}")
            return ToolResult(
                success=False,
                error=f"Invalid mathematical expression: {str(e)}",
                metadata={"original_expression": expression}
            ) # type: ignore

        except ValueError as e:
            logger.error(f"[{self.name}] Value error: {e}")
            return ToolResult(
                success=False,
                error=f"Calculation error: {str(e)}",
                metadata={"original_expression": expression}
            ) # type: ignore

        except ZeroDivisionError:
            logger.error(f"[{self.name}] Division by zero")
            return ToolResult(
                success=False,
                error="Division by zero",
                metadata={"original_expression": expression}
            ) # type: ignore

        except Exception as e:
            logger.error(f"[{self.name}] Unexpected error: {e}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Calculation failed: {str(e)}",
                metadata={"original_expression": expression}
            ) # type: ignore

    def _safe_eval(self, node):
        """
        안전한 AST 평가 (화이트리스트 기반)

        확장 포인트:
        - 새로운 함수 추가
        - 새로운 연산자 추가
        """
        # 숫자
        if isinstance(node, ast.Num):
            return node.n

        # 상수 (Python 3.8+)
        if isinstance(node, ast.Constant):
            return node.value

        # 이진 연산 (+, -, *, /, 등)
        if isinstance(node, ast.BinOp):
            op = type(node.op)
            if op not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator {op.__name__} not allowed")

            left = self._safe_eval(node.left)
            right = self._safe_eval(node.right)
            return self.ALLOWED_OPERATORS[op](left, right)

        # 단항 연산 (+x, -x)
        if isinstance(node, ast.UnaryOp):
            op = type(node.op)
            if op not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator {op.__name__} not allowed")

            operand = self._safe_eval(node.operand)
            return self.ALLOWED_OPERATORS[op](operand)

        # 함수 호출
        if isinstance(node, ast.Call):
            func_name = node.func.id if isinstance(node.func, ast.Name) else None

            if func_name not in self.ALLOWED_FUNCTIONS:
                raise ValueError(f"Function {func_name} not allowed")

            # 인자 평가
            args = [self._safe_eval(arg) for arg in node.args]

            # 함수 실행
            return self.ALLOWED_FUNCTIONS[func_name](*args)

        # 리스트 (배열)
        if isinstance(node, ast.List):
            return [self._safe_eval(elem) for elem in node.elts]

        # 튜플
        if isinstance(node, ast.Tuple):
            return tuple(self._safe_eval(elem) for elem in node.elts)

        # 비교 연산 (<, >, ==, 등)
        if isinstance(node, ast.Compare):
            left = self._safe_eval(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                right = self._safe_eval(comparator)

                if isinstance(op, ast.Lt):
                    result = left < right
                elif isinstance(op, ast.LtE):
                    result = left <= right
                elif isinstance(op, ast.Gt):
                    result = left > right
                elif isinstance(op, ast.GtE):
                    result = left >= right
                elif isinstance(op, ast.Eq):
                    result = left == right
                elif isinstance(op, ast.NotEq):
                    result = left != right
                else:
                    raise ValueError(f"Comparison {type(op).__name__} not allowed")

                if not result:
                    return False
                left = right

            return True

        raise ValueError(f"Expression type {type(node).__name__} not allowed")

    def add_custom_function(self, name: str, func: callable):
        """
        커스텀 함수 추가 (확장 포인트)

        Example:
            calculator.add_custom_function("mean", statistics.mean)
        """
        self.ALLOWED_FUNCTIONS[name] = func
        logger.info(f"[{self.name}] Custom function registered: {name}")


# LangChain tool 래퍼
@tool
def calculate_tool(expression: str) -> str:
    """
    수학 계산을 수행합니다.

    이 도구를 사용하는 경우:
    - 산술 연산 (덧셈, 뺄셈, 곱셈, 나눗셈)
    - 백분율 계산 (예: "15% of 100", "100 * 0.15")
    - 평균, 합계 계산 (예: "sum([10,20,30])", "평균")
    - 비교 연산 (예: "100 * 1.15")

    지원되는 연산:
    - 기본: +, -, *, /, //, %, **
    - 함수: abs, round, min, max, sum, len, pow, sqrt, ceil, floor

    Args:
        expression: 수학 표현식 (예: "100 * 1.15", "sum([10,20,30])", "(50+30)/2")

    Returns:
        계산 결과

    예시:
        - "100 * 0.15" → 15.0
        - "(5000 + 6000) / 2" → 5500.0
        - "sum([10, 20, 30])" → 60
        - "round(123.456, 2)" → 123.46

    보안: 화이트리스트된 연산만 지원 (eval() 사용 안 함)
    """
    tool_instance = CalculatorTool()
    result = tool_instance.execute(expression=expression)

    if result.success:
        return str(result.data)
    else:
        return f"Error: {result.error}"
