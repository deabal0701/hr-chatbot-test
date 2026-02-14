"""
메뉴 및 사용자 메뉴 권한 스키마 (v2.0)

위치: app/models/menu.py
메뉴 트리 CRUD, 사용자별 메뉴 CRUD 권한 관련 모델
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 메뉴 (Menu)
# ===================================

class MenuBase(BaseModel):
    """메뉴 기본 필드"""
    menu_code: str = Field(..., min_length=1, max_length=50, description="메뉴 코드")
    menu_name: str = Field(..., min_length=1, max_length=100, description="메뉴 표시명")
    menu_type: str = Field(..., description="메뉴 타입 (DIRECTORY, PAGE, API)")
    parent_menu_id: Optional[int] = Field(None, description="상위 메뉴 ID (NULL이면 루트)")
    menu_path: Optional[str] = Field(None, max_length=200, description="프론트엔드 URL 경로")
    api_pattern: Optional[str] = Field(None, max_length=200, description="API 경로 패턴")
    icon: Optional[str] = Field(None, max_length=50, description="아이콘 클래스")
    sort_order: int = Field(default=0, description="정렬 순서")
    description: Optional[str] = Field(None, description="설명")

    @field_validator("menu_type")
    @classmethod
    def validate_menu_type(cls, v: str) -> str:
        valid = ["DIRECTORY", "PAGE", "API"]
        v = v.upper()
        if v not in valid:
            raise ValueError(f"menu_type은 {valid} 중 하나여야 합니다")
        return v

    @field_validator("menu_code")
    @classmethod
    def validate_menu_code(cls, v: str) -> str:
        v = v.upper().strip()
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("메뉴 코드는 영문, 숫자, 언더스코어(_)만 사용 가능합니다")
        return v


class MenuCreate(MenuBase):
    """메뉴 생성 요청"""
    is_active: bool = Field(default=True, description="활성 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "menu_code": "REPORTS",
                "menu_name": "리포트",
                "menu_type": "PAGE",
                "parent_menu_id": 1,
                "menu_path": "/admin/reports",
                "icon": "chart",
                "sort_order": 11,
                "is_active": True
            }
        }
    }


class MenuUpdate(BaseModel):
    """메뉴 수정 요청 (모든 필드 Optional, exclude_unset 사용)"""
    menu_name: Optional[str] = Field(None, max_length=100, description="메뉴 표시명")
    menu_type: Optional[str] = Field(None, description="메뉴 타입 (DIRECTORY, PAGE, API)")
    parent_menu_id: Optional[int] = Field(None, description="상위 메뉴 ID (null이면 루트로 변경)")
    menu_path: Optional[str] = Field(None, max_length=200, description="프론트엔드 URL 경로")
    api_pattern: Optional[str] = Field(None, max_length=200, description="API 경로 패턴")
    icon: Optional[str] = Field(None, max_length=50, description="아이콘 클래스")
    sort_order: Optional[int] = Field(None, description="정렬 순서")
    is_active: Optional[bool] = Field(None, description="활성 여부")
    description: Optional[str] = Field(None, description="설명")

    @field_validator("menu_type")
    @classmethod
    def validate_menu_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        valid = ["DIRECTORY", "PAGE", "API"]
        v = v.upper()
        if v not in valid:
            raise ValueError(f"menu_type은 {valid} 중 하나여야 합니다")
        return v


class MenuResponse(BaseModel):
    """메뉴 상세 응답"""
    menu_id: int = Field(..., description="메뉴 ID")
    parent_menu_id: Optional[int] = Field(None, description="상위 메뉴 ID")
    menu_code: str = Field(..., description="메뉴 코드")
    menu_name: str = Field(..., description="메뉴 표시명")
    menu_type: str = Field(..., description="메뉴 타입")
    menu_path: Optional[str] = Field(None, description="프론트엔드 URL 경로")
    api_pattern: Optional[str] = Field(None, description="API 경로 패턴")
    icon: Optional[str] = Field(None, description="아이콘 클래스")
    sort_order: int = Field(default=0, description="정렬 순서")
    depth: int = Field(default=0, description="트리 깊이")
    is_active: bool = Field(default=True, description="활성 여부")
    description: Optional[str] = Field(None, description="설명")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    children: List["MenuResponse"] = Field(default_factory=list, description="하위 메뉴")

    model_config = {
        "json_schema_extra": {
            "example": {
                "menu_id": 4,
                "parent_menu_id": 1,
                "menu_code": "DASHBOARD",
                "menu_name": "대시보드",
                "menu_type": "PAGE",
                "menu_path": "/admin/dashboard",
                "icon": "dashboard",
                "sort_order": 1,
                "depth": 1,
                "is_active": True,
                "children": []
            }
        }
    }


class MenuTreeResponse(BaseModel):
    """메뉴 트리 응답 (전체 트리)"""
    items: List[MenuResponse] = Field(default_factory=list, description="루트 메뉴 목록 (하위 포함)")


# ===================================
# 메뉴 순서 변경 (Reorder)
# ===================================

class MenuReorderItem(BaseModel):
    """메뉴 순서 변경 항목"""
    menu_id: int = Field(..., description="메뉴 ID")
    sort_order: int = Field(..., description="새 정렬 순서")


class MenuReorderRequest(BaseModel):
    """메뉴 순서 일괄 변경 요청 (드래그앤드롭용)"""
    items: List[MenuReorderItem] = Field(..., min_length=1, description="순서 변경 목록")


# ===================================
# 사용자-메뉴 권한 (UserMenu)
# ===================================

class UserMenuPermission(BaseModel):
    """사용자 메뉴 권한 항목 (할당 요청 시 사용)"""
    menu_id: int = Field(..., description="메뉴 ID")
    can_create: bool = Field(default=False, description="등록 권한")
    can_read: bool = Field(default=True, description="조회 권한")
    can_update: bool = Field(default=False, description="수정 권한")
    can_delete: bool = Field(default=False, description="삭제 권한")
    can_export: bool = Field(default=False, description="내보내기 권한")


class UserMenuAssign(BaseModel):
    """사용자 메뉴 권한 일괄 할당 요청"""
    menus: List[UserMenuPermission] = Field(..., min_length=1, description="메뉴 권한 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "menus": [
                    {"menu_id": 4, "can_create": False, "can_read": True, "can_update": False, "can_delete": False, "can_export": False},
                    {"menu_id": 5, "can_create": True, "can_read": True, "can_update": False, "can_delete": False, "can_export": False}
                ]
            }
        }
    }


class UserMenuResponse(BaseModel):
    """사용자별 메뉴 권한 응답 (메뉴 정보 포함)"""
    menu_id: int = Field(..., description="메뉴 ID")
    menu_code: str = Field(..., description="메뉴 코드")
    menu_name: str = Field(..., description="메뉴 표시명")
    menu_type: str = Field(..., description="메뉴 타입")
    menu_path: Optional[str] = Field(None, description="프론트엔드 URL 경로")
    icon: Optional[str] = Field(None, description="아이콘 클래스")
    depth: int = Field(default=0, description="트리 깊이")
    sort_order: int = Field(default=0, description="정렬 순서")
    can_create: bool = Field(default=False, description="등록 권한")
    can_read: bool = Field(default=True, description="조회 권한")
    can_update: bool = Field(default=False, description="수정 권한")
    can_delete: bool = Field(default=False, description="삭제 권한")
    can_export: bool = Field(default=False, description="내보내기 권한")
    granted_at: Optional[datetime] = Field(None, description="부여일시")
