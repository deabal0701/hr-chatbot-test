"""코드 관리 API 라우터 (Phase A: 코드 관리 시스템)

LLM 제공자, 모델, 임베딩 모델 등 코드성 데이터 관리를 위한 REST API
"""
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    CodeItem,
    CodeGroupResponse,
    CodeCreateRequest,
    CodeUpdateRequest,
    CodeReorderRequest,
)
from app.services.code_service import code_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()


@router.get("/codes/groups", response_model=List[str], tags=["codes"])
async def get_code_groups():
    """
    모든 코드 그룹 목록 조회

    Returns:
        코드 그룹 목록
    """
    try:
        groups = code_service.get_code_groups()
        return groups
    except Exception as e:
        logger.error(f"코드 그룹 조회 API 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"코드 그룹 조회 실패: {str(e)}"
        )


@router.get("/codes/{code_group}", response_model=CodeGroupResponse, tags=["codes"])
async def get_codes(code_group: str, include_inactive: bool = False):
    """
    특정 그룹의 코드 목록 조회

    Args:
        code_group: 코드 그룹명 (예: LLM_PROVIDER, LLM_MODEL_OPENAI)
        include_inactive: 비활성 코드 포함 여부 (기본: False)

    Returns:
        코드 그룹 정보 및 코드 목록
    """
    try:
        codes = code_service.get_codes_by_group(code_group, include_inactive)

        return CodeGroupResponse(
            code_group=code_group,
            codes=[CodeItem(**code) for code in codes],
            total_count=len(codes)
        )
    except Exception as e:
        logger.error(f"코드 조회 API 실패 (그룹: {code_group}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"코드 조회 실패: {str(e)}"
        )


@router.get("/codes/item/{code_id}", response_model=CodeItem, tags=["codes"])
async def get_code(code_id: int):
    """
    코드 단건 조회

    Args:
        code_id: 코드 ID

    Returns:
        코드 정보
    """
    try:
        code = code_service.get_code_by_id(code_id)
        if not code:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"코드를 찾을 수 없습니다: {code_id}"
            )
        return CodeItem(**code)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"코드 조회 API 실패 (ID: {code_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"코드 조회 실패: {str(e)}"
        )


@router.post("/codes", response_model=CodeItem, status_code=status.HTTP_201_CREATED, tags=["codes"])
async def create_code(request: CodeCreateRequest):
    """
    코드 생성 (사용자 코드만, is_system=False)

    Args:
        request: 코드 생성 요청

    Returns:
        생성된 코드 정보
    """
    try:
        code_data = request.model_dump(exclude_none=True)
        created_code = code_service.create_code(code_data)
        return CodeItem(**created_code)
    except ValueError as e:
        logger.warning(f"코드 생성 검증 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"코드 생성 API 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"코드 생성 실패: {str(e)}"
        )


@router.put("/codes/{code_id}", response_model=CodeItem, tags=["codes"])
async def update_code(code_id: int, request: CodeUpdateRequest):
    """
    코드 수정

    Args:
        code_id: 코드 ID
        request: 코드 수정 요청

    Returns:
        수정된 코드 정보
    """
    try:
        code_data = request.model_dump(exclude_none=True)
        updated_code = code_service.update_code(code_id, code_data)
        return CodeItem(**updated_code)
    except ValueError as e:
        logger.warning(f"코드 수정 검증 실패 (ID: {code_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"코드 수정 API 실패 (ID: {code_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"코드 수정 실패: {str(e)}"
        )


@router.delete("/codes/{code_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["codes"])
async def delete_code(code_id: int):
    """
    코드 삭제 (시스템 코드는 삭제 불가)

    Args:
        code_id: 코드 ID
    """
    try:
        code_service.delete_code(code_id)
        return None
    except ValueError as e:
        logger.warning(f"코드 삭제 검증 실패 (ID: {code_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"코드 삭제 API 실패 (ID: {code_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"코드 삭제 실패: {str(e)}"
        )


@router.post("/codes/{code_group}/reorder", tags=["codes"])
async def reorder_codes(code_group: str, request: CodeReorderRequest):
    """
    코드 순서 변경 (일괄 업데이트)

    Args:
        code_group: 코드 그룹명
        request: 코드 ID 순서 목록

    Returns:
        성공 메시지
    """
    try:
        code_service.reorder_codes(code_group, request.code_ids)
        return {"message": f"코드 순서 변경 완료: {code_group}"}
    except ValueError as e:
        logger.warning(f"코드 순서 변경 검증 실패 (그룹: {code_group}): {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"코드 순서 변경 API 실패 (그룹: {code_group}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"코드 순서 변경 실패: {str(e)}"
        )
