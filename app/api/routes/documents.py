"""문서 관리 API 라우터 (Admin API)

권장 워크플로우:
1. POST / - 문서 저장 (임베딩 없이)
2. GET /?indexed=false - 미임베딩 문서 조회
3. POST /embedding/execute - 임베딩 실행
4. PUT /{id} - 문서 수정 (내용 변경 시 재임베딩 필요)
5. DELETE /{id} or POST /bulk-delete - 문서 삭제

아키텍처:
- Route (이 파일) → DocumentService (CRUD) → DB
- Route (이 파일) → DocumentService → VectorStoreService (임베딩)
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.models.documents import (
    DocumentSaveRequest,
    DocumentSaveResponse,
    DocumentUpdateRequest,
    DocumentUpdateResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentDeleteResponse,
    BulkDelete,
    Chunking,
)
from app.api.services.document_service import document_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/admin/v1/documents", tags=["admin-documents"])


# ============================================
# 문서 CRUD
# ============================================

@router.post("", response_model=DocumentSaveResponse, status_code=status.HTTP_201_CREATED)
async def save_document(doc: DocumentSaveRequest):
    """
    문서 저장 (임베딩 없이)

    문서를 먼저 저장합니다. 임베딩은 별도로 실행해야 합니다.

    워크플로우:
    1. 이 API로 문서 저장
    2. GET /pending로 미임베딩 문서 확인
    3. POST /embedding/execute로 임베딩 실행
    """
    try:
        logger.info(f"문서 저장 요청: title='{doc.title}', content_length={len(doc.content)}자")

        result = document_service.save_document(
            title=doc.title,
            doc_type=doc.doc_type,
            content=doc.content,
            language=doc.language,
            metadata=doc.metadata,
            source_type=doc.source_type,
            source_file=doc.source_file
        )

        return DocumentSaveResponse(
            success=True,
            message="문서가 저장되었습니다. 임베딩 실행이 필요합니다." if result['needs_chunking']
                    else "문서가 저장되었습니다. 임베딩 실행이 필요합니다.",
            doc_id=result['doc_id'],
            title=result['title'],
            content_length=result['content_length'],
            needs_chunking=result['needs_chunking'],
            recommended_chunks=result['recommended_chunks']
        )

    except ValueError as e:
        # 비즈니스 로직 오류 (중복 문서 등) → 400 Bad Request
        logger.warning(f"문서 저장 실패 - 유효성 오류: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        # DB 오류 등 시스템 오류 → 500 Internal Server Error
        logger.error(f"문서 저장 실패 - 시스템 오류: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 저장 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"문서 저장 중 오류가 발생했습니다: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    doc_type: Optional[str] = Query(None, description="문서 유형 필터 (policy, job_posting, faq, guide)"),
    source_type: Optional[str] = Query(None, description="소스 타입 필터 (ui_input, pdf, web, api)"),
    indexed: Optional[bool] = Query(None, description="임베딩 여부 필터 (true: 임베딩됨, false: 미임베딩, 미지정: 전체)"),
    include_chunks: bool = Query(False, description="청크 포함 여부 (기본: 원본만)"),
    limit: int = Query(100, ge=1, le=1000, description="최대 결과 수"),
    offset: int = Query(0, ge=0, description="시작 위치")
):
    """
    문서 목록 조회

    - indexed 파라미터로 임베딩 여부 필터링:
        - indexed=true: 임베딩 완료된 문서만
        - indexed=false: 미임베딩 문서만 (임베딩 실행 필요)
        - 미지정: 전체 문서
    - include_chunks=False (기본): 원본 문서만 조회
    - include_chunks=True: 청크 포함
    """
    try:
        documents, total_count = document_service.list_documents(
            doc_type=doc_type,
            source_type=source_type,
            indexed=indexed,
            include_chunks=include_chunks,
            limit=limit,
            offset=offset
        )

        return DocumentListResponse(
            total=total_count,
            documents=[DocumentListItem(**doc) for doc in documents]
        )

    except RuntimeError as e:
        logger.error(f"문서 목록 조회 실패 - 시스템 오류: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"문서 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/{doc_id}")
async def get_document(doc_id: int):
    """
    문서 상세 조회

    청킹된 문서의 경우 모든 청크 정보도 함께 반환합니다.
    """
    try:
        doc = document_service.get_document(doc_id)

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"문서를 찾을 수 없습니다: ID={doc_id}"
            )

        return doc

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"문서 조회 실패 - 시스템 오류: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 조회 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"문서 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/{doc_id}", response_model=DocumentUpdateResponse)
async def update_document(doc_id: int, doc: DocumentUpdateRequest):
    """
    문서 수정

    - 제목, 문서유형, 언어, 메타데이터만 수정: 임베딩 유지
    - 내용(content) 수정: 임베딩 무효화, 재임베딩 필요

    내용 수정 시 기존 청크는 자동 삭제됩니다.
    """
    try:
        result = document_service.update_document(
            doc_id=doc_id,
            title=doc.title,
            doc_type=doc.doc_type,
            content=doc.content,
            language=doc.language,
            metadata=doc.metadata
        )

        message = "문서가 수정되었습니다."
        if result['needs_reindex']:
            message += " 내용이 변경되어 재임베딩이 필요합니다."

        return DocumentUpdateResponse(
            success=True,
            message=message,
            doc_id=result['doc_id'],
            title=result['title'],
            content_length=result['content_length'],
            embedding_invalidated=result['embedding_invalidated'],
            needs_reindex=result['needs_reindex']
        )

    except ValueError as e:
        logger.warning(f"문서 수정 실패 - 유효성 오류: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        logger.error(f"문서 수정 실패 - 시스템 오류: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 수정 실패: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"문서 수정 중 오류가 발생했습니다: {str(e)}")


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(doc_id: int):
    """
    문서 삭제

    청킹된 문서의 경우 모든 청크도 함께 삭제됩니다.
    """
    try:
        deleted_count = document_service.delete_document(doc_id)

        if deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"문서를 찾을 수 없습니다: ID={doc_id}"
            )

        return DocumentDeleteResponse(
            success=True,
            message=f"{deleted_count}개 문서(청크 포함)가 삭제되었습니다.",
            deleted_count=deleted_count
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.error(f"문서 삭제 실패 - 시스템 오류: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 삭제 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 삭제 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/bulk-delete", response_model=BulkDelete.Response)
async def bulk_delete_documents(request: BulkDelete.Request):
    """
    문서 일괄 삭제

    여러 문서를 한 번에 삭제합니다.
    각 문서의 청크도 함께 삭제됩니다.
    """
    try:
        result = document_service.bulk_delete_documents(request.doc_ids)

        return BulkDelete.Response(
            success=len(result['failed_ids']) == 0,
            message=f"{result['total_deleted']}개 문서 삭제 완료" +
                    (f", {len(result['failed_ids'])}개 실패" if result['failed_ids'] else ""),
            total_requested=result['total_requested'],
            total_deleted=result['total_deleted'],
            failed_ids=result['failed_ids']
        )

    except RuntimeError as e:
        logger.error(f"일괄 삭제 실패 - 시스템 오류: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"일괄 삭제 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일괄 삭제 중 오류가 발생했습니다: {str(e)}"
        )


# ============================================
# 임베딩/청킹 관리
# ============================================

@router.post("/embedding/execute", response_model=Chunking.ExecuteResponse)
async def execute_embedding(request: Chunking.ExecuteRequest):
    """
    임베딩 실행 (청킹 포함)

    저장된 문서에 대해 임베딩을 실행합니다.
    긴 문서는 자동으로 청킹됩니다.

    - doc_ids: 임베딩할 문서 ID 목록
    - chunk_size: 청크 크기 (기본 1000자)
    - chunk_overlap: 청크 간 중복 (기본 100자)
    """
    try:
        logger.info(f"임베딩 실행 요청: doc_ids={request.doc_ids}, chunk_size={request.chunk_size}")

        results = document_service.execute_embedding(
            doc_ids=request.doc_ids,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap,
            delete_original=request.delete_original
        )

        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count

        return Chunking.ExecuteResponse(
            success=failed_count == 0,
            message=f"{success_count}개 문서 임베딩 완료" + (f", {failed_count}개 실패" if failed_count > 0 else ""),
            total_requested=len(request.doc_ids),
            total_success=success_count,
            total_failed=failed_count,
            results=[Chunking.ExecuteResultItem(**r) for r in results]
        )

    except Exception as e:
        logger.error(f"임베딩 실행 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"임베딩 실행 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/embedding/preview", response_model=Chunking.PreviewResponse)
async def preview_chunks(request: Chunking.PreviewRequest):
    """
    청킹 미리보기

    문서를 저장하기 전에 어떻게 청킹될지 미리 확인합니다.
    실제 임베딩이나 저장은 수행하지 않습니다.
    """
    try:
        chunks = document_service.preview_chunks(
            content=request.content,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )

        return Chunking.PreviewResponse(
            original_length=len(request.content),
            total_chunks=len(chunks),
            chunks=[Chunking.PreviewItem(**chunk) for chunk in chunks]
        )

    except Exception as e:
        logger.error(f"청킹 미리보기 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"청킹 미리보기 중 오류가 발생했습니다: {str(e)}"
        )
