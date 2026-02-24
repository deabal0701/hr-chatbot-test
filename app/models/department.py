"""
조직(부서) 관리 스키마

위치: app/models/department.py
부서 트리 CRUD 관련 모델
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 부서 (Department)
# ===================================

class DeptBase(BaseModel):
    """부서 기본 필드"""
    dept_code: str = Field(..., min_length=1, max_length=50, description="부서 코드 (테넌트 내 유니크)")
    dept_name: str = Field(..., min_length=1, max_length=200, description="부서명")

    @field_validator("dept_code")
    @classmethod
    def validate_dept_code(cls, v: str) -> str:
        """부서 코드: 영문 대문자 + 숫자 + 언더스코어만 허용"""
        v = v.upper().strip()
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("부서 코드는 영문, 숫자, 언더스코어(_)만 사용 가능합니다")
        return v


class DeptCreate(DeptBase):
    """부서 생성 요청"""
    tenant_id: int = Field(..., description="소속 테넌트 ID")
    parent_dept_id: Optional[int] = Field(None, description="상위 부서 ID (NULL이면 최상위)")
    sort_order: int = Field(default=0, description="정렬 순서")
    is_active: bool = Field(default=True, description="활성 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "dept_code": "DEV_01",
                "dept_name": "개발1팀",
                "tenant_id": 2,
                "parent_dept_id": 1,
                "sort_order": 1,
                "is_active": True
            }
        }
    }


class DeptUpdate(BaseModel):
    """부서 수정 요청 (모든 필드 Optional, exclude_unset 사용)"""
    dept_name: Optional[str] = Field(None, max_length=200, description="부서명")
    parent_dept_id: Optional[int] = Field(None, description="상위 부서 ID (null이면 최상위로 변경)")
    sort_order: Optional[int] = Field(None, description="정렬 순서")
    is_active: Optional[bool] = Field(None, description="활성 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "dept_name": "개발1팀 (수정)",
                "sort_order": 2
            }
        }
    }


class DeptResponse(BaseModel):
    """부서 상세 응답 (트리 조회 시 children 포함)"""
    dept_id: int = Field(..., description="부서 ID")
    dept_code: str = Field(..., description="부서 코드")
    dept_name: str = Field(..., description="부서명")
    parent_dept_id: Optional[int] = Field(None, description="상위 부서 ID")
    tenant_id: int = Field(..., description="소속 테넌트 ID")
    tenant_name: Optional[str] = Field(None, description="테넌트명")
    depth: int = Field(default=0, description="트리 깊이 (0=최상위)")
    sort_order: int = Field(default=0, description="정렬 순서")
    is_active: bool = Field(default=True, description="활성 여부")
    user_count: int = Field(default=0, description="소속 사용자 수")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    children: List["DeptResponse"] = Field(default_factory=list, description="하위 부서")

    model_config = {
        "json_schema_extra": {
            "example": {
                "dept_id": 1,
                "dept_code": "HQ_DEV",
                "dept_name": "개발본부",
                "parent_dept_id": None,
                "tenant_id": 2,
                "tenant_name": "DEMO",
                "depth": 0,
                "sort_order": 1,
                "is_active": True,
                "user_count": 3,
                "children": []
            }
        }
    }


# ===================================
# 부서 순서 변경 (Reorder)
# ===================================

class DeptReorderItem(BaseModel):
    """부서 순서 변경 항목"""
    dept_id: int = Field(..., description="부서 ID")
    sort_order: int = Field(..., description="새 정렬 순서")


class DeptReorderRequest(BaseModel):
    """부서 순서 일괄 변경 요청 (드래그앤드롭용)"""
    items: List[DeptReorderItem] = Field(..., min_length=1, description="순서 변경 목록")
