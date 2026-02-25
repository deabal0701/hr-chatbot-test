"""
PII Middleware

Agent 미들웨어에서 개인정보를 감지 및 마스킹합니다.
core PIIService(app/core/pii/pii_service.py)를 사용하여
NL2SQL과 동일한 PII 보호 수준을 제공합니다.

보호 대상 (PIIService 기준):
- 주민등록번호 (SSN): 880101-1234567
- 전화번호 (Phone): 010-1234-5678
- 계좌번호 (Bank Account): 다양한 은행 형식
- 이메일 (Email): user@example.com
"""

from typing import Any, Dict

from app.graphs.agent.middleware.base import Middleware
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class PIIMiddleware(Middleware):
    """
    개인정보 보호 미들웨어

    core PIIService를 사용하여 NL2SQL과 동일한 마스킹 적용:
    - 입력(process_input): PII 감지 시 경고 로깅 (마스킹 안 함, 사용자 본인 입력)
    - 출력(process_output): answer 텍스트 + sql_result rows PII 마스킹
    """

    async def process_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        입력 처리 (PII 감지 경고)

        사용자 질문에 PII가 포함된 경우 경고 로깅만 수행합니다.
        사용자가 의도적으로 입력한 것이므로 마스킹은 하지 않습니다.
        """
        from app.core.pii.pii_service import pii_service

        request_id = data.get("request_id", "unknown")
        question = data.get("question", "")

        if not pii_service.enabled:
            log_step(logger, request_id, "MIDDLEWARE", "PII", "INPUT", "PII 필터 비활성화")
            return data

        if not question:
            return data

        detected = pii_service.detect_only(question)
        if detected:
            pii_types = list({m.type for m in detected})
            log_step(logger, request_id, "MIDDLEWARE", "PII", "INPUT", f"사용자 질문에 PII 감지 | types={pii_types}, count={len(detected)}", level="WARNING")
        else:
            log_step(logger, request_id, "MIDDLEWARE", "PII", "INPUT", "PII 미감지", level="DEBUG")

        return data

    async def process_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        출력 처리 (PII 마스킹)

        최종 답변(answer)과 SQL 결과(sql_result)에서 PII를 마스킹합니다.
        """
        from app.core.pii.pii_service import pii_service

        request_id = data.get("request_id", "unknown")

        if not pii_service.enabled:
            log_step(logger, request_id, "MIDDLEWARE", "PII", "OUTPUT", "PII 필터 비활성화")
            return data

        total_masked = 0

        # 1. answer 텍스트 마스킹
        answer = data.get("answer", "")
        if answer:
            masked_answer, count = pii_service.mask_text(answer)
            if count > 0:
                data["answer"] = masked_answer
                total_masked += count

        # 2. sql_result rows 마스킹
        sql_result = data.get("sql_result")
        if sql_result and isinstance(sql_result, dict):
            rows = sql_result.get("rows", [])
            if rows:
                masked_rows, count = pii_service.mask_sql_rows(rows)
                if count > 0:
                    sql_result["rows"] = masked_rows
                    data["sql_result"] = sql_result
                    total_masked += count

        if total_masked > 0:
            log_step(logger, request_id, "MIDDLEWARE", "PII", "OUTPUT", f"PII 마스킹 완료 | detected={total_masked}, answer={bool(answer)}, rows={len(sql_result.get('rows', [])) if sql_result else 0}")
        else:
            log_step(logger, request_id, "MIDDLEWARE", "PII", "OUTPUT", "PII 미감지", level="DEBUG")

        return data
