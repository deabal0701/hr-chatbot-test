"""문서 관리 API 테스트

위치: tests/test_09_documents.py
문서 CRUD + 청킹 미리보기 (임베딩 실행은 외부 API 의존이므로 선택적)
- fixture 기반 teardown으로 테스트 실패 시에도 데이터 정리 보장
"""
import pytest
from conftest import assert_success

PREFIX = "/api/admin/v1/documents"


class TestDocumentCRUD:
    created_id = None

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        """teardown: 테스트 실패 시에도 생성된 문서 삭제"""
        yield
        if TestDocumentCRUD.created_id:
            client.delete(f"{PREFIX}/{TestDocumentCRUD.created_id}", headers=admin_headers)

    def test_create(self, client, admin_headers):
        """문서 생성"""
        data = assert_success(client.post(PREFIX, headers=admin_headers, json={
            "title": "PyTest 문서",
            "doc_type": "guide",
            "content": "이것은 PyTest에서 생성한 테스트 문서입니다. " * 10,
            "source_type": "ui_input",
            "usage_type": "rag_knowledge",
        }), status_code=201)
        assert data["doc_id"] > 0
        TestDocumentCRUD.created_id = data["doc_id"]

    def test_list(self, client, admin_headers):
        """문서 목록 조회"""
        data = assert_success(client.get(PREFIX, headers=admin_headers, params={"limit": 10}))
        assert "items" in data
        assert "total" in data

    def test_list_filter(self, client, admin_headers):
        """필터 조회"""
        data = assert_success(client.get(PREFIX, headers=admin_headers, params={
            "doc_type": "guide",
            "indexed": False,
        }))
        assert "items" in data

    def test_get(self, client, admin_headers):
        """문서 상세"""
        data = assert_success(client.get(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        assert data["title"] == "PyTest 문서"

    def test_update(self, client, admin_headers):
        """문서 수정"""
        data = assert_success(client.put(f"{PREFIX}/{self.created_id}", headers=admin_headers, json={
            "title": "PyTest 수정 문서",
        }))
        assert data["title"] == "PyTest 수정 문서"

    def test_delete(self, client, admin_headers):
        """문서 삭제"""
        data = assert_success(client.delete(f"{PREFIX}/{self.created_id}", headers=admin_headers))
        assert data["deleted_count"] >= 1
        TestDocumentCRUD.created_id = None  # teardown에서 이중 삭제 방지


class TestBulkDelete:
    def test_bulk_delete(self, client, admin_headers):
        """일괄 삭제"""
        ids = []
        try:
            for i in range(2):
                d = assert_success(client.post(PREFIX, headers=admin_headers, json={
                    "title": f"PyTest 일괄삭제 {i}",
                    "doc_type": "faq",
                    "content": f"테스트 내용 {i}" * 5,
                }), status_code=201)
                ids.append(d["doc_id"])
            data = assert_success(client.post(f"{PREFIX}/bulk-delete", headers=admin_headers, json={
                "doc_ids": ids,
            }))
            assert data["total_deleted"] == 2
            ids.clear()  # 삭제 완료
        finally:
            for doc_id in ids:
                client.delete(f"{PREFIX}/{doc_id}", headers=admin_headers)


class TestChunkPreview:
    def test_preview(self, client, admin_headers):
        """청킹 미리보기"""
        data = assert_success(client.post(f"{PREFIX}/embedding/preview", headers=admin_headers, json={
            "content": "테스트 문서 내용. " * 200,
            "chunk_size": 500,
            "chunk_overlap": 50,
        }))
        assert data["total_chunks"] >= 1
        assert len(data["chunks"]) == data["total_chunks"]
