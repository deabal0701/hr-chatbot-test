"""
PII Middleware (껍데기)

개인정보 감지 및 마스킹 미들웨어입니다.

TODO: 실제 PII 감지/마스킹 로직 구현
- 주민번호, 전화번호, 이메일 등 패턴 감지
- 입력에서 PII 감지 시 경고 로깅
- 출력에서 PII 마스킹 적용
"""

from typing import Any, Dict

from app.graphs.agent.middleware.base import Middleware
from app.utils.logger import log_step


class PIIMiddleware(Middleware):
    """
    개인정보 보호 미들웨어 (껍데기)

    추후 구현 예정:
    - 입력: PII 감지 및 경고
    - 출력: PII 마스킹

    현재는 아무 처리 없이 데이터를 그대로 통과시킵니다.
    """

    # TODO: 실제 PII 패턴 정의
    # PII_PATTERNS = {
    #     "주민번호": r"\d{6}-?\d{7}",
    #     "전화번호": r"01[0-9]-?\d{3,4}-?\d{4}",
    #     "이메일": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    #     "계좌번호": r"\d{3,4}-?\d{2,4}-?\d{4,6}",
    # }

    async def process_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        입력 처리 (PII 감지)

        TODO: 실제 PII 감지 로직 구현
        - question에서 PII 패턴 검색
        - 감지 시 경고 로깅
        - data["_pii_detected"] = {...} 설정

        Args:
            data: 요청 데이터

        Returns:
            처리된 요청 데이터
        """
        request_id = data.get("request_id", "unknown")
        log_step(request_id, "MIDDLEWARE", "PII", "INPUT", "PII 감지 (미구현 - 패스스루)", level="DEBUG")

        # TODO: 실제 구현
        # question = data.get("question", "")
        # detected = self._detect_pii(question)
        # if detected:
        #     data["_pii_detected"] = detected
        #     log_step(request_id, "MIDDLEWARE", "PII", "DETECT",
        #             f"PII 감지: {list(detected.keys())}", level="WARNING")

        return data

    async def process_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        출력 처리 (PII 마스킹)

        TODO: 실제 PII 마스킹 로직 구현
        - answer에서 PII 패턴 검색
        - 감지 시 마스킹 적용
        - data["_pii_masked_count"] = N 설정

        Args:
            data: 응답 데이터

        Returns:
            처리된 응답 데이터
        """
        request_id = data.get("request_id", "unknown")
        log_step(request_id, "MIDDLEWARE", "PII", "OUTPUT", "PII 마스킹 (미구현 - 패스스루)", level="DEBUG")

        # TODO: 실제 구현
        # answer = data.get("answer", "")
        # masked, count = self._mask_pii(answer)
        # if count > 0:
        #     data["answer"] = masked
        #     data["_pii_masked_count"] = count
        #     log_step(request_id, "MIDDLEWARE", "PII", "MASK",
        #             f"PII 마스킹 적용: {count}건")

        return data

    # TODO: 실제 구현 시 주석 해제
    # def _detect_pii(self, text: str) -> Dict[str, List[str]]:
    #     """PII 감지"""
    #     import re
    #     detected = {}
    #     for pii_type, pattern in self.PII_PATTERNS.items():
    #         matches = re.findall(pattern, text)
    #         if matches:
    #             detected[pii_type] = matches
    #     return detected

    # def _mask_pii(self, text: str) -> tuple[str, int]:
    #     """PII 마스킹"""
    #     import re
    #     count = 0
    #     for pii_type, pattern in self.PII_PATTERNS.items():
    #         matches = re.findall(pattern, text)
    #         count += len(matches)
    #         text = re.sub(pattern, f"[{pii_type} 마스킹됨]", text)
    #     return text, count
