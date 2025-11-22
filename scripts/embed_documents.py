import json
import os
import sys
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.vector_store import vector_store
from app.utils.database import db_manager
from app.utils.logger import setup_logger
from app.utils.text_splitter import create_chunks

# 환경 변수 로드
load_dotenv()

logger = setup_logger(__name__)


def embed_from_file(file_path: str):
    """파일에서 문서를 읽어 임베딩"""
    file_path = Path(file_path)

    if not file_path.exists():
        logger.error(f"파일을 찾을 수 없습니다: {file_path}")
        return

    logger.info(f"파일 로드 중: {file_path}")

    # JSON 파일 형식: [{"title": "...", "doc_type": "...", "content": "...", "metadata": {...}}, ...]
    with open(file_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)

    logger.info(f"문서 {len(documents)}개 발견")

    for i, doc in enumerate(documents, 1):
        try:
            title = doc.get('title', f'문서 {i}')
            doc_type = doc.get('doc_type', 'general')
            content = doc.get('content', '')
            language = doc.get('language', 'ko')
            metadata = doc.get('metadata', {})

            # 문서가 너무 길면 청킹
            if len(content) > 1000:
                logger.info(f"문서가 길어 청킹: {title}")
                chunks = create_chunks(content, chunk_size=800, chunk_overlap=100)

                for j, chunk in enumerate(chunks, 1):
                    chunk_title = f"{title} (Part {j}/{len(chunks)})"
                    chunk_metadata = {**metadata, "chunk": j, "total_chunks": len(chunks)}

                    doc_id = vector_store.insert_document(
                        title=chunk_title,
                        doc_type=doc_type,
                        content=chunk,
                        language=language,
                        metadata=chunk_metadata
                    )

                    logger.info(f"[{i}/{len(documents)}] 청크 임베딩 완료: {chunk_title} (ID: {doc_id})")
            else:
                doc_id = vector_store.insert_document(
                    title=title,
                    doc_type=doc_type,
                    content=content,
                    language=language,
                    metadata=metadata
                )

                logger.info(f"[{i}/{len(documents)}] 임베딩 완료: {title} (ID: {doc_id})")

        except Exception as e:
            logger.error(f"문서 임베딩 실패 [{i}]: {e}")
            continue

    logger.info("모든 문서 임베딩 완료!")


def embed_sample_documents():
    """샘플 문서 임베딩"""
    sample_docs = [
        {
            "title": "2024년 재택근무 정책",
            "doc_type": "policy",
            "language": "ko",
            "content": """
2024년부터 시행되는 새로운 재택근무 정책을 안내드립니다.

1. 재택근무 일수
- 주 2회 재택근무가 가능합니다
- 팀 업무 특성에 따라 팀장 승인 하에 조정 가능합니다

2. 신청 방법
- 재택근무 전날까지 팀장에게 사전 승인 받아야 합니다
- 그룹웨어 시스템에서 신청서를 작성하세요

3. 근무 수칙
- 정규 근무 시간(09:00-18:00)을 준수해야 합니다
- 협업 툴(Slack, Zoom)을 통해 즉시 연락 가능한 상태를 유지하세요
- 일일 업무 보고를 작성하여 공유하세요

4. 장비 지원
- 노트북, 모니터 등 필요한 장비를 회사에서 지원합니다
- IT 팀에 문의하여 신청하세요
            """,
            "metadata": {"year": 2024, "department": "전사", "category": "근무제도"}
        },
        {
            "title": "연차 휴가 사용 가이드",
            "doc_type": "guide",
            "language": "ko",
            "content": """
연차 휴가 사용에 대한 상세 가이드입니다.

1. 연차 발생 기준
- 입사 1년 차: 15일
- 2년 차 이상: 15일 + 근속년수별 추가 (최대 25일)
- 매년 1월 1일 기준으로 발생

2. 사용 방법
- 그룹웨어에서 최소 1일 전 신청
- 팀장 승인 후 사용 가능
- 긴급한 경우 유선 승인 후 사후 신청 가능

3. 미사용 연차
- 연차는 당해 연도 내 사용이 원칙
- 미사용 연차는 익년 상반기까지 사용 가능
- 그 이후 자동 소멸됨

4. 연차 사용 촉진
- 분기별 5일 이상 사용 권장
- 연말 집중 사용을 지양하고 계획적으로 사용하세요
            """,
            "metadata": {"year": 2024, "department": "HR", "category": "휴가"}
        },
        {
            "title": "2024년 상반기 백엔드 개발자 채용",
            "doc_type": "job_posting",
            "language": "ko",
            "content": """
백엔드 개발자를 모집합니다!

[모집 부문]
- 직무: 백엔드 개발
- 경력: 3년 이상
- 채용 인원: 00명

[자격 요건]
- Python, Django/FastAPI 프레임워크 실무 경험 3년 이상
- RESTful API 설계 및 개발 경험
- PostgreSQL, MySQL 등 RDBMS 활용 경험
- Git을 활용한 협업 경험

[우대 사항]
- AWS, GCP 등 클라우드 서비스 경험
- Docker, Kubernetes 등 컨테이너 기술 활용 경험
- Redis, Elasticsearch 등 사용 경험
- 대용량 트래픽 처리 경험

[근무 조건]
- 근무지: 서울 강남구
- 근무 시간: 주 5일 (09:00-18:00)
- 재택근무: 주 2회 가능
- 급여: 경력에 따라 협의

[전형 절차]
1. 서류 전형
2. 코딩 테스트
3. 1차 면접 (기술)
4. 2차 면접 (컬처핏)
5. 최종 합격

[지원 방법]
- 이메일: recruit@company.com
- 제출 서류: 이력서, 포트폴리오
            """,
            "metadata": {"year": 2024, "department": "개발", "position": "백엔드개발자", "region": "서울"}
        },
        {
            "title": "인사평가 제도 FAQ",
            "doc_type": "faq",
            "language": "ko",
            "content": """
인사평가 제도에 대해 자주 묻는 질문입니다.

Q1. 인사평가는 언제 실시되나요?
A1. 연 2회 실시됩니다. 상반기 평가는 7월, 하반기 평가는 1월에 진행됩니다.

Q2. 평가 등급은 어떻게 나뉘나요?
A2. S, A, B, C, D 총 5단계로 구분됩니다.
    - S등급: 탁월한 성과 (상위 10%)
    - A등급: 우수한 성과 (상위 20%)
    - B등급: 기대 수준 충족 (50%)
    - C등급: 개선 필요 (15%)
    - D등급: 현저히 미흡 (5%)

Q3. 평가 결과는 어떻게 활용되나요?
A3. 승진, 보상, 교육 등에 활용됩니다.
    - 승진: S, A 등급 누적 시 승진 대상
    - 인센티브: 등급별 차등 지급
    - 교육: C, D 등급자 대상 역량 개발 교육

Q4. 평가에 이의가 있을 경우?
A4. 평가 결과 공개 후 2주 이내 HR팀에 이의 신청이 가능합니다.

Q5. 신입사원도 평가 대상인가요?
A5. 입사 6개월 이상 경과 시 평가 대상에 포함됩니다.
            """,
            "metadata": {"year": 2024, "department": "HR", "category": "평가"}
        }
    ]

    logger.info(f"샘플 문서 {len(sample_docs)}개 임베딩 시작")

    for i, doc in enumerate(sample_docs, 1):
        try:
            doc_id = vector_store.insert_document(
                title=doc['title'],
                doc_type=doc['doc_type'],
                content=doc['content'],
                language=doc['language'],
                metadata=doc['metadata']
            )

            logger.info(f"[{i}/{len(sample_docs)}] 임베딩 완료: {doc['title']} (ID: {doc_id})")

        except Exception as e:
            logger.error(f"샘플 문서 임베딩 실패 [{i}]: {e}")
            continue

    logger.info("샘플 문서 임베딩 완료!")


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="문서 임베딩 스크립트")
    parser.add_argument(
        '--file',
        type=str,
        help='JSON 파일 경로 (선택사항)'
    )
    parser.add_argument(
        '--sample',
        action='store_true',
        help='샘플 문서 임베딩 (테스트용)'
    )

    args = parser.parse_args()

    # 데이터베이스 초기화
    db_manager.initialize()
    logger.info("데이터베이스 연결 완료")

    try:
        if args.sample:
            embed_sample_documents()
        elif args.file:
            embed_from_file(args.file)
        else:
            print("사용법:")
            print("  샘플 문서 임베딩: python scripts/embed_documents.py --sample")
            print("  파일에서 임베딩: python scripts/embed_documents.py --file data/documents.json")

    finally:
        db_manager.close()
        logger.info("데이터베이스 연결 종료")


if __name__ == "__main__":
    print("=" * 60)
    print("HR Chatbot - 문서 임베딩 파이프라인")
    print("=" * 60)
    main()
