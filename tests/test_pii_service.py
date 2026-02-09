"""PII 서비스 테스트"""
import pytest
from app.core.pii.pii_service import PIIService, detect_korean_ssn, detect_korean_phone, detect_korean_bank_account


class TestDetectors:
    """한국어 PII 감지기 단위 테스트"""

    def test_detect_korean_ssn(self):
        matches = detect_korean_ssn("주민번호는 880101-1234567입니다.")
        assert len(matches) == 1
        assert matches[0]["value"] == "880101-1234567"
        assert matches[0]["type"] == "korean_ssn"

    def test_detect_korean_ssn_no_dash(self):
        matches = detect_korean_ssn("8801011234567")
        assert len(matches) == 1

    def test_detect_korean_phone(self):
        matches = detect_korean_phone("연락처: 010-1234-5678")
        assert len(matches) == 1
        assert matches[0]["value"] == "010-1234-5678"

    def test_detect_korean_phone_no_dash(self):
        matches = detect_korean_phone("01012345678")
        assert len(matches) == 1

    def test_detect_korean_bank_account_3seg(self):
        """3세그먼트 계좌번호 (신한, 하나 등)"""
        matches = detect_korean_bank_account("계좌: 110-234-567890")
        assert len(matches) == 1
        assert matches[0]["value"] == "110-234-567890"

    def test_detect_korean_bank_account_3seg_hana(self):
        """3세그먼트 계좌번호 - 하나은행 (123-123456-12345)"""
        matches = detect_korean_bank_account("하나: 123-123456-12345")
        assert len(matches) == 1
        assert matches[0]["value"] == "123-123456-12345"

    def test_detect_korean_bank_account_4seg_kb(self):
        """4세그먼트 계좌번호 - 국민은행 (123-12-1234-123)"""
        matches = detect_korean_bank_account("국민: 123-12-1234-123")
        assert len(matches) == 1
        assert matches[0]["value"] == "123-12-1234-123"

    def test_detect_korean_bank_account_4seg_nh(self):
        """4세그먼트 계좌번호 - 농협 (123-1234-1234-12)"""
        matches = detect_korean_bank_account("농협: 123-1234-1234-12")
        assert len(matches) == 1
        assert matches[0]["value"] == "123-1234-1234-12"

    def test_detect_korean_bank_account_no_phone_false_positive(self):
        """전화번호가 계좌번호로 오감지되지 않아야 함"""
        matches = detect_korean_bank_account("010-1234-5678")
        assert len(matches) == 0

    def test_no_false_positive(self):
        matches = detect_korean_phone("부서코드 A001, 사원번호 2024")
        assert len(matches) == 0


class TestPIIService:
    """PII 서비스 통합 테스트"""

    def setup_method(self):
        self.service = PIIService()
        self.service._enabled = True
        self.service._initialized = True
        from langchain.agents.middleware._redaction import RedactionRule
        self.service._rules = self.service._build_rules("redact")

    def test_mask_text_phone(self):
        masked, count = self.service.mask_text("010-1234-5678")
        assert count == 1
        assert "010-1234-5678" not in masked
        assert "REDACTED" in masked

    def test_mask_text_email(self):
        masked, count = self.service.mask_text("hong@company.com")
        assert count == 1
        assert "hong@company.com" not in masked

    def test_mask_text_ssn(self):
        masked, count = self.service.mask_text("880101-1234567")
        assert count == 1
        assert "880101-1234567" not in masked

    def test_mask_text_no_pii(self):
        text = "2024년 입사자 수는 5명입니다."
        masked, count = self.service.mask_text(text)
        assert count == 0
        assert masked == text

    def test_mask_text_multiple(self):
        text = "홍길동 010-1234-5678 hong@test.com 880101-1234567"
        masked, count = self.service.mask_text(text)
        assert count == 3
        assert "010-1234-5678" not in masked
        assert "hong@test.com" not in masked
        assert "880101-1234567" not in masked

    def test_mask_sql_rows(self):
        rows = [
            {"name": "홍길동", "phone": "010-1234-5678", "email": "hong@test.com", "dept": "개발팀"},
            {"name": "김영희", "phone": "010-9876-5432", "email": "kim@test.com", "dept": "인사팀"},
        ]
        masked_rows, count = self.service.mask_sql_rows(rows)
        assert count == 4  # 2 phones + 2 emails
        assert masked_rows[0]["dept"] == "개발팀"  # non-PII 컬럼은 변경 없음
        assert "010-1234-5678" not in masked_rows[0]["phone"]
        assert "hong@test.com" not in masked_rows[0]["email"]

    def test_mask_sql_rows_empty(self):
        masked_rows, count = self.service.mask_sql_rows([])
        assert count == 0
        assert masked_rows == []

    def test_mask_value_non_string(self):
        assert self.service.mask_value(12345) == 12345
        assert self.service.mask_value(None) is None

    def test_disabled(self):
        self.service._enabled = False
        masked, count = self.service.mask_text("010-1234-5678")
        assert count == 0
        assert masked == "010-1234-5678"

    def test_detect_only(self):
        matches = self.service.detect_only("010-1234-5678 hong@test.com")
        assert len(matches) == 2
        types = {m["type"] for m in matches}
        assert "korean_phone" in types
        assert "email" in types
