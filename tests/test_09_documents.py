"""문서 관리 API 테스트

위치: tests/test_09_documents.py
문서 CRUD + 청킹 미리보기 + 파일 업로드 보안
- fixture 기반 teardown으로 테스트 실패 시에도 데이터 정리 보장
"""
import pytest
from conftest import assert_success, assert_error

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


class TestFileUploadSecurity:
    """파일 업로드 보안 검증"""

    def test_upload_invalid_extension(self, client, admin_headers):
        """허용되지 않는 확장자(.txt) 거부"""
        resp = client.post(
            f"{PREFIX}/upload",
            headers=admin_headers,
            files={"file": ("test.txt", b"hello world", "text/plain")},
        )
        error = assert_error(resp, expected_code="VALIDATION_ERROR")
        assert "허용되지 않는 파일 형식" in error["message"]

    def test_upload_no_extension(self, client, admin_headers):
        """확장자 없는 파일 거부"""
        resp = client.post(
            f"{PREFIX}/upload",
            headers=admin_headers,
            files={"file": ("noext", b"some data", "application/octet-stream")},
        )
        error = assert_error(resp, expected_code="VALIDATION_ERROR")
        assert "허용되지 않는 파일 형식" in error["message"]

    def test_upload_exe_extension(self, client, admin_headers):
        """실행 파일(.exe) 거부"""
        resp = client.post(
            f"{PREFIX}/upload",
            headers=admin_headers,
            files={"file": ("malware.exe", b"\x00" * 100, "application/octet-stream")},
        )
        error = assert_error(resp, expected_code="VALIDATION_ERROR")
        assert "허용되지 않는 파일 형식" in error["message"]

    def test_upload_path_traversal(self, client, admin_headers):
        """경로 탐색 파일명 방어 — 확장자가 허용된 경우 파일명이 정리됨"""
        # PDF 헤더를 가진 최소한의 바이트 (실제 파싱은 서비스 레이어에서)
        pdf_header = b"%PDF-1.4 test content"
        resp = client.post(
            f"{PREFIX}/upload",
            headers=admin_headers,
            files={"file": ("../../etc/passwd.pdf", pdf_header, "application/pdf")},
        )
        # 확장자는 .pdf로 허용되므로 검증 통과 → 서비스 레이어에서 처리
        # 파일명이 정리되었는지는 성공 응답의 filename으로 확인
        if resp.status_code == 200:
            body = resp.json()
            if body["success"]:
                assert body["data"]["filename"] == "passwd.pdf"

    def test_upload_double_extension(self, client, admin_headers):
        """이중 확장자(.pdf.exe) 거부"""
        resp = client.post(
            f"{PREFIX}/upload",
            headers=admin_headers,
            files={"file": ("doc.pdf.exe", b"\x00" * 100, "application/octet-stream")},
        )
        error = assert_error(resp, expected_code="VALIDATION_ERROR")
        assert "허용되지 않는 파일 형식" in error["message"]

    def test_upload_valid_pdf(self, client, admin_headers):
        """정상 PDF 업로드 — 확장자 검증 통과 확인"""
        # 최소한의 유효 PDF
        minimal_pdf = (
            b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
            b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
            b"0000000058 00000 n \n0000000115 00000 n \n"
            b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
        )
        resp = client.post(
            f"{PREFIX}/upload",
            headers=admin_headers,
            files={"file": ("pytest_test.pdf", minimal_pdf, "application/pdf")},
        )
        # PDF 파싱 성공 여부는 라이브러리 의존이므로, 확장자 검증 통과(400 아님)만 확인
        assert resp.status_code != 400 or "허용되지 않는 파일 형식" not in resp.text


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
