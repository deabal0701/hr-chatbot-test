"""
한글 키워드 추출기 (pg_trgm 검색용)

위치: app/core/vector/keyword_extractor.py

기능:
- 사용자 자연어 질의에서 pg_trgm 검색에 적합한 핵심 키워드 추출
- mode=none: 원본 그대로 반환 (테스트용)
- mode=rule: 2단계 규칙 기반 추출 (기본값)
  1단계: 공백 단위 독립 불용어 토큰 제거
  2단계: 토큰별 조사/어미 suffix 제거

설계 근거:
- pg_trgm은 문자(trigram) 기반 매칭 → 의미 분석 불필요
- 조사/어미가 trigram pool 오염 → word_similarity 점수 희석
- 규칙 기반만으로 충분 (LLM 대비 개선 효과 미미, 지연 없음)
"""
import re
from typing import List


class KeywordExtractor:
    """규칙 기반 한글 키워드 추출기"""

    # 독립 불용어: 공백으로 분리된 토큰 전체가 이 목록에 있으면 제거
    KO_STOPWORDS = {
        # 요청/의문 표현
        '해줘', '알려줘', '알려', '대해', '대해서',
        '어떻게', '무엇', '무슨', '뭐', '어떤', '어디', '언제', '누가',
        '주세요', '하세요', '궁금', '찾아줘', '찾아', '보여줘', '해주세요',
        '알려주세요', '알아봐', '설명해', '설명해줘',
        # 관계어
        '우리', '우리회사', '회사', '관련', '관한', '위한', '따른',
        # 기타 조사/접속어 독립 사용
        '것', '수', '등', '및', '또는', '그리고', '하지만',
        '있어', '있나요', '있는지', '있을까요', '있습니까',
        '이야', '이에요', '입니다', '됩니다', '될까요',
    }

    # 조사/어미 suffix: 긴 것 먼저 체크 (에서 vs 에 순서 중요)
    KO_PARTICLE_SUFFIXES = [
        '에서', '에게', '으로', '까지', '부터', '한테', '이랑', '하고',
        '는', '은', '를', '을', '과', '와', '가', '이', '의', '에', '로', '도', '만',
    ]

    # 토큰 끝 구두점 패턴 (조사 제거 전 제거)
    _TRAILING_PUNCT = re.compile(r'[?!.,。、]+$')

    # 영문/숫자 식별자 패턴 (보존 대상)
    _ALPHANUMERIC_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9\-\.]*$')

    def extract(self, query: str, mode: str = "rule") -> str:
        """
        키워드 추출

        Args:
            query: 원본 사용자 질의
            mode: "none" | "rule" (기본값: "rule")

        Returns:
            추출된 키워드 문자열 (공백 구분)
            결과가 비면 원본 반환 (fallback)

        Examples:
            "연차 휴가는 몇 일 까지 사용할 수 있어" → "연차 휴가"
            "법인카드 사용 규정은 어떻게 되나요"   → "법인카드 사용 규정"
            "ISO 27001 인증 절차를 알려줘"        → "ISO 27001 인증 절차"
        """
        if mode == "none" or not query.strip():
            return query
        return self._extract_rule(query)

    def _extract_rule(self, query: str) -> str:
        """2단계 규칙 기반 키워드 추출"""
        tokens = query.strip().split()
        result: List[str] = []

        for token in tokens:
            # 영문/숫자 패턴은 그대로 보존 (ISO, HR-001, 27001 등)
            if self._ALPHANUMERIC_PATTERN.match(token):
                result.append(token)
                continue

            # 1단계: 독립 불용어 토큰 제거
            if token in self.KO_STOPWORDS:
                continue

            # 구두점 제거 (사항은? → 사항은)
            token = self._TRAILING_PUNCT.sub('', token)
            if not token:
                continue

            # 2단계: 조사 suffix 제거
            cleaned = self._strip_particle(token)

            # suffix 제거 후 2글자 미만이면 제거
            if len(cleaned) < 2:
                continue

            # suffix 제거 후 불용어가 되면 제거 (예: "것을" → "것" → 불용어)
            if cleaned in self.KO_STOPWORDS:
                continue

            result.append(cleaned)

        # fallback: 결과가 비면 원본 반환
        return ' '.join(result) if result else query

    def _strip_particle(self, token: str) -> str:
        """토큰 끝의 조사/어미 suffix 제거 (긴 것 먼저)"""
        for suffix in self.KO_PARTICLE_SUFFIXES:
            if token.endswith(suffix):
                stripped = token[:-len(suffix)]
                # 제거 후 최소 2글자 이상 남아야 유효
                if len(stripped) >= 2:
                    return stripped
        return token


# 싱글톤 인스턴스
keyword_extractor = KeywordExtractor()
