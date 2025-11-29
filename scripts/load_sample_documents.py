"""
샘플 문서 로드 스크립트
RAG 테스트를 위한 샘플 문서를 API를 통해 등록합니다.

사용법:
    python scripts/load_sample_documents.py

옵션:
    --api-url: API 서버 URL (기본: http://localhost:8000)
    --embed: 등록 후 임베딩까지 실행
"""
import argparse
import json
import sys
from pathlib import Path

import requests


def load_sample_documents(api_url: str, with_embedding: bool = False):
    """샘플 문서를 API를 통해 등록"""

    # 샘플 문서 파일 경로
    sample_file = Path(__file__).parent.parent / "docs" / "sample_documents.json"

    if not sample_file.exists():
        print(f"❌ 샘플 파일을 찾을 수 없습니다: {sample_file}")
        sys.exit(1)

    # 샘플 문서 로드
    with open(sample_file, "r", encoding="utf-8") as f:
        documents = json.load(f)

    print(f"📄 {len(documents)}개의 샘플 문서를 로드했습니다.\n")

    # API 헬스 체크
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ API 서버에 연결할 수 없습니다: {api_url}")
            sys.exit(1)
        print(f"✅ API 서버 연결 확인: {api_url}\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ API 서버에 연결할 수 없습니다: {e}")
        sys.exit(1)

    # 문서 등록
    saved_ids = []
    for i, doc in enumerate(documents, 1):
        try:
            response = requests.post(
                f"{api_url}/api/admin/v1/documents",
                json={
                    "title": doc["title"],
                    "doc_type": doc["doc_type"],
                    "content": doc["content"],
                    "language": doc.get("language", "ko"),
                    "metadata": doc.get("metadata", {}),
                    "source_type": "api"
                },
                timeout=30
            )

            if response.status_code == 201:
                result = response.json()
                saved_ids.append(result["doc_id"])
                print(f"  [{i}/{len(documents)}] ✅ {doc['title']} (ID: {result['doc_id']})")
            else:
                print(f"  [{i}/{len(documents)}] ❌ {doc['title']} - {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"  [{i}/{len(documents)}] ❌ {doc['title']} - 요청 실패: {e}")

    print(f"\n📊 결과: {len(saved_ids)}/{len(documents)}개 문서 등록 완료")

    # 임베딩 실행 (옵션)
    if with_embedding and saved_ids:
        print(f"\n🔄 {len(saved_ids)}개 문서에 대해 임베딩을 실행합니다...")

        try:
            response = requests.post(
                f"{api_url}/api/admin/v1/documents/embedding/execute",
                json={
                    "doc_ids": saved_ids,
                    "chunk_size": 1000,
                    "chunk_overlap": 100
                },
                timeout=300  # 임베딩은 시간이 걸릴 수 있음
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 임베딩 완료: {result['message']}")
            else:
                print(f"❌ 임베딩 실패: {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"❌ 임베딩 요청 실패: {e}")

    return saved_ids


def main():
    parser = argparse.ArgumentParser(description="샘플 문서 로드 스크립트")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API 서버 URL (기본: http://localhost:8000)"
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="등록 후 임베딩까지 실행"
    )

    args = parser.parse_args()

    print("=" * 50)
    print("  HR Chatbot 샘플 문서 로드")
    print("=" * 50)
    print()

    load_sample_documents(args.api_url, args.embed)

    print()
    print("=" * 50)
    print("완료!")
    print()
    print("다음 단계:")
    print("1. 문서 목록 확인: GET /api/admin/v1/documents")
    print("2. 임베딩 실행: POST /api/admin/v1/documents/embedding/execute")
    print("3. RAG 테스트: POST /api/v1/search")
    print("=" * 50)


if __name__ == "__main__":
    main()
