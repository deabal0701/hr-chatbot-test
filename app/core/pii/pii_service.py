"""
PII(개인정보) 감지 및 마스킹 서비스

LangChain의 _redaction 모듈을 활용하여
SQL 결과 등 텍스트 데이터에서 PII를 감지하고 마스킹합니다.

PII 패턴 지원:
- 주민등록번호 (SSN) : 880101-1234567
- 전화번호 (Phone) : 010-1234-5678
- 계좌번호 (Bank Account) : 3세그먼트 + 4세그먼트 (은행별 다양한 형식)
- 이메일 (Email, 빌트인) : user@example.com
- 기타 LangChain 빌트인 PII 유형 지원

사용:
    from app.core.pii.pii_service import pii_service

    # 텍스트 마스킹
    masked = pii_service.mask_text("010-1234-5678")

    # SQL 결과 rows 마스킹
    masked_rows = pii_service.mask_sql_rows(rows, columns)
"""

import re
from typing import Any, Dict, List, Tuple

from langchain.agents.middleware._redaction import (
    PIIMatch,
    RedactionRule,
    ResolvedRedactionRule,
)

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# =========================================================================
# 커스텀 PII 감지기
# =========================================================================

def detect_korean_ssn(content: str) -> list[PIIMatch]:
    """주민등록번호 감지 (6자리-7자리)"""
    return [
        PIIMatch(type="korean_ssn", value=m.group(), start=m.start(), end=m.end())
        for m in re.finditer(r"\d{6}-?\d{7}", content)
    ]

def detect_korean_phone(content: str) -> list[PIIMatch]:
    """전화번호 감지 (01x-xxxx-xxxx)"""
    return [
        PIIMatch(type="korean_phone", value=m.group(), start=m.start(), end=m.end())
        for m in re.finditer(r"01[0-9]-?\d{3,4}-?\d{4}", content)
    ]


def detect_korean_bank_account(content: str) -> list[PIIMatch]:
    """계좌번호 감지 (은행별 다양한 형식, 전화번호 패턴 제외)

    3세그먼트: 신한(110-234-567890), 하나(123-123456-12345), 카카오(1234-12-1234567)
    4세그먼트: 국민(123-12-1234-123), 농협(123-1234-1234-12), 기업(123-123456-12-123)
    """
    matches = []
    seen_ranges = set()
    # 4세그먼트 먼저: 국민, 농협, 기업 등
    for m in re.finditer(r"\d{3,4}-\d{2,6}-\d{2,6}-\d{2,3}", content):
        value = m.group()
        if re.match(r"^01[0-9]-", value):
            continue
        matches.append(PIIMatch(type="korean_bank_account", value=value, start=m.start(), end=m.end()))
        seen_ranges.add((m.start(), m.end()))
    # 3세그먼트: 신한, 하나, 우리, 카카오 등 (4세그먼트와 중복 방지)
    for m in re.finditer(r"\d{3,4}-\d{2,6}-\d{4,7}", content):
        value = m.group()
        if re.match(r"^01[0-9]-", value):
            continue
        if any(m.start() >= s and m.start() < e for s, e in seen_ranges):
            continue
        matches.append(PIIMatch(type="korean_bank_account", value=value, start=m.start(), end=m.end()))
    return matches


# =========================================================================
# PII 서비스
# =========================================================================

class PIIService:
    """PII 감지 및 마스킹 서비스

    LangChain _redaction 모듈의 RedactionRule을 활용하여
    텍스트/SQL 결과에서 PII를 감지하고 지정된 전략으로 처리합니다.
    """

    def __init__(self):
        self._rules: list[ResolvedRedactionRule] = []
        self._enabled = True
        self._initialized = False

    def _ensure_initialized(self) -> None:
        """규칙 지연 초기화 (settings_config 순환 import 방지)"""
        if self._initialized:
            return
        self._initialized = True
        self._load_rules()

    def _load_rules(self) -> None:
        """설정에서 PII 규칙 로드"""
        try:
            from app.core.config.settings_config import settings_config

            self._enabled = settings_config.get_value("pii", "enabled", True)
            strategy = settings_config.get_value("pii", "strategy", "redact")

            self._rules = self._build_rules(strategy)

            logger.debug(f"PII 서비스 초기화 완료 | enabled={self._enabled}, strategy={strategy}, rules={len(self._rules)}")
        except Exception as e:
            logger.warning(f"PII 설정 로드 실패, 기본값 사용: {e}")
            self._enabled = True
            self._rules = self._build_rules("redact")

    def _build_rules(self, strategy: str) -> list[ResolvedRedactionRule]:
        """PII 감지 규칙 생성"""
        return [
            RedactionRule(pii_type="korean_ssn", strategy=strategy, detector=detect_korean_ssn).resolve(),
            RedactionRule(pii_type="korean_phone", strategy=strategy, detector=detect_korean_phone).resolve(),
            RedactionRule(pii_type="korean_bank_account", strategy=strategy, detector=detect_korean_bank_account).resolve(),
            RedactionRule(pii_type="email", strategy=strategy).resolve(),
        ]

    @property
    def enabled(self) -> bool:
        self._ensure_initialized()
        return self._enabled

    def reload(self) -> None:
        """설정 다시 로드 (Admin UI에서 설정 변경 시)"""
        self._initialized = False
        self._ensure_initialized()

    def mask_text(self, text: str) -> Tuple[str, int]:
        """텍스트에서 PII 감지 및 마스킹

        Args:
            text: 마스킹 대상 텍스트

        Returns:
            (마스킹된 텍스트, 감지된 PII 수)
        """
        self._ensure_initialized()

        if not self._enabled or not text or not isinstance(text, str):
            return text, 0

        total_matches = 0
        for rule in self._rules:
            text, matches = rule.apply(text)
            total_matches += len(matches)

        return text, total_matches

    def mask_value(self, value: Any) -> Any:
        """단일 값 마스킹 (str이 아니면 그대로 반환)"""
        if not isinstance(value, str):
            return value
        masked, _ = self.mask_text(value)
        return masked

    def mask_sql_rows(
        self, rows: List[Dict[str, Any]], columns: List[str] | None = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """SQL 결과 rows에서 PII 마스킹

        Args:
            rows: SQL 실행 결과 row 리스트 [{col: val, ...}, ...]
            columns: 마스킹 대상 컬럼 (None이면 전체 컬럼)

        Returns:
            (마스킹된 rows, 총 감지된 PII 수)
        """
        self._ensure_initialized()

        if not self._enabled or not rows:
            return rows, 0

        total_matches = 0
        masked_rows = []

        for row in rows:
            masked_row = {}
            for col, val in row.items():
                if columns and col not in columns:
                    masked_row[col] = val
                    continue

                if isinstance(val, str):
                    masked_val, match_count = self.mask_text(val)
                    masked_row[col] = masked_val
                    total_matches += match_count
                else:
                    masked_row[col] = val
            masked_rows.append(masked_row)

        return masked_rows, total_matches

    def detect_only(self, text: str) -> List[PIIMatch]:
        """PII 감지만 수행 (마스킹하지 않음)"""
        self._ensure_initialized()

        if not self._enabled or not text or not isinstance(text, str):
            return []

        all_matches = []
        for rule in self._rules:
            matches = rule.detector(text)
            all_matches.extend(matches)
        return all_matches


# 싱글톤 인스턴스
pii_service = PIIService()
