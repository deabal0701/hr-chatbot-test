from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import DocumentCreate, DocumentResponse, MessageResponse
from app.services.vector_store import vector_store
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_document(doc: DocumentCreate):
    """문서 생성 (임베딩 포함)"""
    try:
        doc_id = vector_store.insert_document(
            title=doc.title,
            doc_type=doc.doc_type,
            content=doc.content,
            language=doc.language,
            metadata=doc.metadata
        )

        return MessageResponse(
            message=f"문서가 생성되었습니다. ID: {doc_id}",
            success=True
        )

    except Exception as e:
        logger.error(f"문서 생성 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: int):
    """문서 조회"""
    doc = vector_store.get_document_by_id(doc_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"문서를 찾을 수 없습니다: ID={doc_id}"
        )

    return DocumentResponse(**doc)


@router.delete("/{doc_id}", response_model=MessageResponse)
async def delete_document(doc_id: int):
    """문서 삭제"""
    success = vector_store.delete_document(doc_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"문서를 찾을 수 없습니다: ID={doc_id}"
        )

    return MessageResponse(
        message=f"문서가 삭제되었습니다. ID: {doc_id}",
        success=True
    )


@router.put("/{doc_id}/embedding", response_model=MessageResponse)
async def update_document_embedding(doc_id: int, content: str):
    """문서 임베딩 업데이트"""
    try:
        success = vector_store.update_document_embedding(doc_id, content)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"문서를 찾을 수 없습니다: ID={doc_id}"
            )

        return MessageResponse(
            message=f"문서 임베딩이 업데이트되었습니다. ID: {doc_id}",
            success=True
        )

    except Exception as e:
        logger.error(f"임베딩 업데이트 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"임베딩 업데이트 중 오류가 발생했습니다: {str(e)}"
        )
