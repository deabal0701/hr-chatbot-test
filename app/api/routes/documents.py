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

from fastapi import APIRouter, Depends, Query, UploadFile, File, status

from app.core.security.permission import require_menu_permission
from app.models.auth import UserContext
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
    FileUpload,
)
from app.api.services.document_service import document_service
from app.core.errors import APIException, ErrorCode, success_response
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/admin/v1/documents", tags=["admin-documents"])


# ============================================
# 문서 CRUD
# ============================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def save_document(doc: DocumentSaveRequest, current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "create"))):
    """문서 저장 (임베딩 없이)"""
    try:
        # tenant_id 결정: GLOBAL은 요청값 또는 공용('1'), TENANT/USER는 자기 테넌트 강제
        if current_user.is_global:
            tenant_id = doc.tenant_id or '1'
        else:
            tenant_id = str(current_user.tenant_id)

        logger.info(f"문서 저장 요청: title='{doc.title}', content_length={len(doc.content)}자, tenant_id={tenant_id}")

        result = document_service.save_document(
            title=doc.title, doc_type=doc.doc_type, content=doc.content,
            language=doc.language, metadata=doc.metadata, context_data=doc.context_data,
            source_type=doc.source_type, source_file=doc.source_file, usage_type=doc.usage_type,
            tenant_id=tenant_id
        )

        response = DocumentSaveResponse(
            success=True,
            message="문서가 저장되었습니다. 임베딩 실행이 필요합니다.",
            doc_id=result['doc_id'], title=result['title'],
            content_length=result['content_length'],
            needs_chunking=result['needs_chunking'],
            recommended_chunks=result['recommended_chunks']
        )
        return success_response(response.model_dump())

    except ValueError as e:
        logger.warning(f"문서 저장 실패 - 유효성 오류: {e}")
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except RuntimeError as e:
        logger.error(f"문서 저장 실패 - 시스템 오류: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.DATABASE_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 저장 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("")
async def list_documents(
    doc_type: Optional[str] = Query(None, description="문서 유형 필터"),
    source_type: Optional[str] = Query(None, description="소스 타입 필터"),
    usage_type: Optional[str] = Query(None, description="문서 용도 필터"),
    indexed: Optional[bool] = Query(None, description="임베딩 여부 필터"),
    include_chunks: bool = Query(False, description="청크 포함 여부"),
    tenant_id: Optional[str] = Query(None, description="테넌트 필터 (GLOBAL 역할 전용)"),
    limit: int = Query(100, ge=1, le=1000, description="최대 결과 수"),
    offset: int = Query(0, ge=0, description="시작 위치"),
    current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "read")),
):
    """문서 목록 조회"""
    try:
        documents, total_count = document_service.list_documents(
            doc_type=doc_type, source_type=source_type, indexed=indexed,
            include_chunks=include_chunks, usage_type=usage_type, limit=limit, offset=offset,
            current_user=current_user, tenant_id_filter=tenant_id
        )

        response = DocumentListResponse(
            total=total_count,
            items=[DocumentListItem(**doc) for doc in documents]
        )
        return success_response(response.model_dump())

    except RuntimeError as e:
        logger.error(f"문서 목록 조회 실패 - 시스템 오류: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.DATABASE_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 목록 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/{doc_id}")
async def get_document(doc_id: int, current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "read"))):
    """문서 상세 조회"""
    try:
        doc = document_service.get_document(doc_id, current_user=current_user)
        if not doc:
            raise APIException(error_code=ErrorCode.DOCUMENT_NOT_FOUND, message=f"문서를 찾을 수 없습니다: ID={doc_id}")
        return success_response(doc)
    except APIException:
        raise
    except RuntimeError as e:
        logger.error(f"문서 조회 실패 - 시스템 오류: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.DATABASE_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.put("/{doc_id}")
async def update_document(doc_id: int, doc: DocumentUpdateRequest, current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "update"))):
    """문서 수정"""
    try:
        result = document_service.update_document(
            doc_id=doc_id, title=doc.title, doc_type=doc.doc_type,
            content=doc.content, language=doc.language,
            metadata=doc.metadata, context_data=doc.context_data,
            current_user=current_user
        )

        message = "문서가 수정되었습니다."
        if result['needs_reindex']:
            message += " 내용이 변경되어 재임베딩이 필요합니다."

        response = DocumentUpdateResponse(
            success=True, message=message, doc_id=result['doc_id'],
            title=result['title'], content_length=result['content_length'],
            embedding_invalidated=result['embedding_invalidated'],
            needs_reindex=result['needs_reindex']
        )
        return success_response(response.model_dump())

    except ValueError as e:
        logger.warning(f"문서 수정 실패 - 유효성 오류: {e}")
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except RuntimeError as e:
        logger.error(f"문서 수정 실패 - 시스템 오류: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.DATABASE_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 수정 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(doc_id: int, current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "delete"))):
    """문서 삭제"""
    try:
        deleted_count = document_service.delete_document(doc_id, current_user=current_user)
        if deleted_count == 0:
            raise APIException(error_code=ErrorCode.DOCUMENT_NOT_FOUND, message=f"문서를 찾을 수 없습니다: ID={doc_id}")

        response = DocumentDeleteResponse(
            success=True,
            message=f"{deleted_count}개 문서(청크 포함)가 삭제되었습니다.",
            deleted_count=deleted_count
        )
        return success_response(response.model_dump())

    except APIException:
        raise
    except RuntimeError as e:
        logger.error(f"문서 삭제 실패 - 시스템 오류: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.DATABASE_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"문서 삭제 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/bulk-delete")
async def bulk_delete_documents(request: BulkDelete.Request, current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "delete"))):
    """문서 일괄 삭제"""
    try:
        result = document_service.bulk_delete_documents(request.doc_ids, current_user=current_user)

        response = BulkDelete.Response(
            success=len(result['failed_ids']) == 0,
            message=f"{result['total_deleted']}개 문서 삭제 완료" +
                    (f", {len(result['failed_ids'])}개 실패" if result['failed_ids'] else ""),
            total_requested=result['total_requested'],
            total_deleted=result['total_deleted'],
            failed_ids=result['failed_ids']
        )
        return success_response(response.model_dump())

    except RuntimeError as e:
        logger.error(f"일괄 삭제 실패 - 시스템 오류: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.DATABASE_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"일괄 삭제 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# 파일 업로드
# ============================================

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "create"))):
    """파일 업로드 및 텍스트 추출 (PDF, DOCX)"""
    try:
        file_bytes = await file.read()
        filename = file.filename or "unknown"

        logger.info(f"파일 업로드 요청: filename='{filename}', size={len(file_bytes)}bytes")

        result = document_service.extract_from_file(filename, file_bytes)

        response = FileUpload.Response(
            success=True,
            message="파일에서 텍스트가 추출되었습니다.",
            filename=result["filename"],
            source_type=result["source_type"],
            extracted_text=result["extracted_text"],
            content_length=result["content_length"],
            page_count=result["page_count"],
            file_size=result["file_size"],
        )
        return success_response(response.model_dump())

    except ValueError as e:
        logger.warning(f"파일 업로드 실패 - 유효성 오류: {e}")
        raise APIException(error_code=ErrorCode.VALIDATION_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"파일 업로드 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


# ============================================
# 임베딩/청킹 관리
# ============================================

@router.post("/embedding/execute")
async def execute_embedding(request: Chunking.ExecuteRequest, current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "update"))):
    """임베딩 실행 (청킹 포함)"""
    try:
        logger.info(f"임베딩 실행 요청: doc_ids={request.doc_ids}, chunk_size={request.chunk_size}")

        results = document_service.execute_embedding(
            doc_ids=request.doc_ids, chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap, delete_original=request.delete_original
        )

        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count

        response = Chunking.ExecuteResponse(
            success=failed_count == 0,
            message=f"{success_count}개 문서 임베딩 완료" + (f", {failed_count}개 실패" if failed_count > 0 else ""),
            total_requested=len(request.doc_ids),
            total_success=success_count,
            total_failed=failed_count,
            results=[Chunking.ExecuteResultItem(**r) for r in results]
        )
        return success_response(response.model_dump())

    except Exception as e:
        logger.error(f"임베딩 실행 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.EMBEDDING_FAILED, detail=str(e))


@router.post("/embedding/preview")
async def preview_chunks(request: Chunking.PreviewRequest, current_user: UserContext = Depends(require_menu_permission("DOC_MGMT", "read"))):
    """청킹 미리보기"""
    try:
        chunks = document_service.preview_chunks(
            content=request.content,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )

        response = Chunking.PreviewResponse(
            original_length=len(request.content),
            total_chunks=len(chunks),
            chunks=[Chunking.PreviewItem(**chunk) for chunk in chunks]
        )
        return success_response(response.model_dump())

    except Exception as e:
        logger.error(f"청킹 미리보기 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))
