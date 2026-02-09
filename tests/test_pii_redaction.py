"""_redaction 모듈 마스킹 테스트"""
from langchain.agents.middleware._redaction import RedactionRule, PIIMatch, apply_strategy
import re

def main():
  # 1. 빌트인 email 마스킹 테스트
  rule_email = RedactionRule(pii_type="email", strategy="mask").resolve()
  text1 = "hong@company.com"
  result1, matches1 = rule_email.apply(text1)
  print(f"[email mask]   {text1} -> {result1}  (matches: {len(matches1)})")

  # 2. 빌트인 email redact 테스트
  rule_email_r = RedactionRule(pii_type="email", strategy="redact").resolve()
  result1r, _ = rule_email_r.apply(text1)
  print(f"[email redact] {text1} -> {result1r}")

  # 3. 커스텀 한국 전화번호 - mask (기본 fallback: ****끝4자리)
  def detect_kr_phone(content):
      return [PIIMatch(type="korean_phone", value=m.group(), start=m.start(), end=m.end())
              for m in re.finditer(r"01[0-9]-?\d{3,4}-?\d{4}", content)]

  rule_phone = RedactionRule(pii_type="korean_phone", strategy="mask", detector=detect_kr_phone).resolve()
  text2 = "010-1234-5678"
  result2, matches2 = rule_phone.apply(text2)
  print(f"[phone mask]   {text2} -> {result2}  (matches: {len(matches2)})")

  # 4. 커스텀 한국 전화번호 - redact
  rule_phone_r = RedactionRule(pii_type="korean_phone", strategy="redact", detector=detect_kr_phone).resolve()
  result2r, _ = rule_phone_r.apply(text2)
  print(f"[phone redact] {text2} -> {result2r}")

  # 5. 커스텀 주민번호 - mask
  def detect_kr_ssn(content):
      return [PIIMatch(type="korean_ssn", value=m.group(), start=m.start(), end=m.end())
              for m in re.finditer(r"\d{6}-?\d{7}", content)]

  rule_ssn = RedactionRule(pii_type="korean_ssn", strategy="mask", detector=detect_kr_ssn).resolve()
  text3 = "880101-1234567"
  result3, _ = rule_ssn.apply(text3)
  print(f"[ssn mask]     {text3} -> {result3}")

  rule_ssn_r = RedactionRule(pii_type="korean_ssn", strategy="redact", detector=detect_kr_ssn).resolve()
  result3r, _ = rule_ssn_r.apply(text3)
  print(f"[ssn redact]   {text3} -> {result3r}")

  # 6. 복합 테스트 - SQL 결과 row 시뮬레이션
  print("\n--- SQL 결과 Row 시뮬레이션 ---")
  row_text = "홍길동, 010-1234-5678, hong@company.com, 880101-1234567"
  print(f"[원본]         {row_text}")

  for rule in [rule_email, rule_phone, rule_ssn]:
      row_text, _ = rule.apply(row_text)
  print(f"[mask 적용]    {row_text}")

  row_text2 = "홍길동, 010-1234-5678, hong@company.com, 880101-1234567"
  for rule in [rule_email_r, rule_phone_r, rule_ssn_r]:
      row_text2, _ = rule.apply(row_text2)
  print(f"[redact 적용]  {row_text2}")

  # 7. SQL result rows Dict 마스킹 시뮬레이션
  print("\n--- SQL Result Dict 마스킹 ---")
  rows = [
      {"name": "홍길동", "phone": "010-1234-5678", "email": "hong@company.com", "ssn": "880101-1234567"},
      {"name": "김영희", "phone": "010-9876-5432", "email": "kim@test.co.kr", "ssn": "900505-2345678"},
  ]
  all_rules = [rule_email, rule_phone, rule_ssn]

  print("[원본]")
  for row in rows:
      print(f"  {row}")

  for row in rows:
      for col, val in row.items():
          if isinstance(val, str):
              for rule in all_rules:
                  val, _ = rule.apply(val)
              row[col] = val

  print("[마스킹 후]")
  for row in rows:
      print(f"  {row}")


if __name__ == "__main__":
    main()
