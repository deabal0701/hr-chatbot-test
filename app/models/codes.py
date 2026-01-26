"""
코드 관리 스키마

공통 코드(LLM_PROVIDER, LLM_MODEL 등) 관리 관련 모델
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ===================================
# 코드 그룹 조회
# ===================================

class CodeGroupItem(BaseModel):
    """코드 그룹 아이템 (그룹 목록 조회용)"""
    code_value: str  # 그룹 코드 (예: LLM_PROVIDER)
    code_name: str   # 그룹 표시명 (예: LLM 제공자)
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True

    model_config = {
        "json_schema_extra": {
            "example": {
                "code_value": "LLM_PROVIDER",
                "code_name": "LLM 제공자",
                "description": "사용 가능한 LLM 제공자 목록",
                "sort_order": 1,
                "is_active": True
            }
        }
    }


# ===================================
# 코드 조회
# ===================================

class CodeItem(BaseModel):
    """코드 아이템 (응답용)"""
    code_id: int
    code_group: str
    code_value: str
    code_name: str
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    sort_order: int = 0
    is_active: bool = True
    is_system: bool = False
    created_at: str  # ISO 형식 문자열
    updated_at: str  # ISO 형식 문자열

    model_config = {
        "json_schema_extra": {
            "example": {
                "code_id": 1,
                "code_group": "LLM_PROVIDER",
                "code_value": "openai",
                "code_name": "OpenAI",
                "description": "OpenAI LLM 제공자",
                "metadata": {
                    "default_model": "gpt-4o",
                    "pricing_link": "https://platform.openai.com/docs/pricing"
                },
                "sort_order": 1,
                "is_active": True,
                "is_system": True,
                "created_at": "2024-01-07T10:00:00",
                "updated_at": "2024-01-07T10:00:00"
            }
        }
    }


class CodeGroupResponse(BaseModel):
    """코드 그룹 조회 응답"""
    code_group: str
    codes: List[CodeItem]
    total_count: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "code_group": "LLM_PROVIDER",
                "codes": [
                    {
                        "code_id": 1,
                        "code_group": "LLM_PROVIDER",
                        "code_value": "openai",
                        "code_name": "OpenAI",
                        "description": "OpenAI LLM 제공자",
                        "metadata": {"default_model": "gpt-4o"},
                        "sort_order": 1,
                        "is_active": True,
                        "is_system": True,
                        "created_at": "2024-01-07T10:00:00",
                        "updated_at": "2024-01-07T10:00:00"
                    }
                ],
                "total_count": 1
            }
        }
    }


# ===================================
# 코드 생성/수정
# ===================================

class CodeCreateRequest(BaseModel):
    """코드 생성 요청"""
    code_group: str = Field(..., min_length=1, max_length=50, description="코드 그룹명")
    code_value: str = Field(..., min_length=1, max_length=100, description="코드 값")
    code_name: str = Field(..., min_length=1, max_length=200, description="표시명")
    description: Optional[str] = Field(None, description="설명")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 속성 (JSON)")
    sort_order: Optional[int] = Field(0, ge=0, description="정렬 순서")
    is_active: Optional[bool] = Field(True, description="활성화 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code_group": "LLM_MODEL_OPENAI",
                "code_value": "gpt-4o-mini",
                "code_name": "GPT-4o Mini",
                "description": "OpenAI GPT-4o Mini 모델 (경량)",
                "metadata": {"max_tokens": 128000},
                "sort_order": 5,
                "is_active": True
            }
        }
    }


class CodeUpdateRequest(BaseModel):
    """코드 수정 요청 (code_group, code_value는 수정 불가)"""
    code_name: Optional[str] = Field(None, min_length=1, max_length=200, description="표시명")
    description: Optional[str] = Field(None, description="설명")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 속성 (JSON)")
    sort_order: Optional[int] = Field(None, ge=0, description="정렬 순서")
    is_active: Optional[bool] = Field(None, description="활성화 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code_name": "GPT-4o Mini (Updated)",
                "description": "업데이트된 설명",
                "metadata": {"max_tokens": 128000, "cost_per_1k": 0.15},
                "sort_order": 10,
                "is_active": False
            }
        }
    }


class CodeReorderRequest(BaseModel):
    """코드 순서 변경 요청"""
    code_ids: List[int] = Field(..., min_length=1, description="코드 ID 목록 (순서대로)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "code_ids": [3, 1, 2, 4]
            }
        }
    }
