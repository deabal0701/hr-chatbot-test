"""개인 대시보드 위젯 스키마

위치: app/models/personal_dashboard.py
- 개인 대시보드 위젯 CRUD 요청/응답 모델
- 레이아웃 저장, SQL 실행 모델
"""
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


VALID_WIDGET_TYPES = {"table", "bar", "hbar", "line", "pie", "scatter", "kpi"}


# ===================================
# 내부 구조 모델
# ===================================

class ChartConfig(BaseModel):
    """차트 설정 (chart_config JSONB)"""
    x_column: Optional[str] = None
    y_columns: Optional[List[str]] = None
    pie_top_n: Optional[int] = None
    kpi_column: Optional[str] = None
    kpi_suffix: Optional[str] = None
    color_palette: Optional[str] = "default"
    column_aliases: Optional[Dict[str, str]] = None


class CachedData(BaseModel):
    """캐시된 쿼리 결과 (cached_data JSONB)"""
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    cached_at: Optional[str] = None


class GridPosition(BaseModel):
    """그리드 위치 (grid_position JSONB)"""
    x: int = 0
    y: int = 0
    w: int = 6
    h: int = 10


# ===================================
# 위젯 CRUD
# ===================================

class WidgetCreate(BaseModel):
    """위젯 생성 요청"""
    title: str = Field(..., min_length=1, max_length=200, description="위젯 제목")
    widget_type: str = Field(default="table", description="위젯 유형")
    query: Optional[str] = Field(None, description="원본 자연어 질문")
    sql: Optional[str] = Field(None, description="생성된/수정된 SQL")
    chart_config: Optional[ChartConfig] = Field(None, description="차트 설정")
    cached_data: Optional[CachedData] = Field(None, description="캐시 결과")
    grid_position: Optional[GridPosition] = Field(None, description="그리드 위치")

    @field_validator("widget_type")
    @classmethod
    def validate_widget_type(cls, v: str) -> str:
        if v not in VALID_WIDGET_TYPES:
            raise ValueError(f"유효하지 않은 위젯 유형: {v} (허용: {', '.join(sorted(VALID_WIDGET_TYPES))})")
        return v


class WidgetUpdate(BaseModel):
    """위젯 수정 요청 (변경 필드만 전송)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="위젯 제목")
    widget_type: Optional[str] = Field(None, description="위젯 유형")
    query: Optional[str] = Field(None, description="원본 자연어 질문")
    sql: Optional[str] = Field(None, description="수정된 SQL")
    chart_config: Optional[ChartConfig] = Field(None, description="차트 설정")
    cached_data: Optional[CachedData] = Field(None, description="캐시 결과")

    @field_validator("widget_type")
    @classmethod
    def validate_widget_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_WIDGET_TYPES:
            raise ValueError(f"유효하지 않은 위젯 유형: {v} (허용: {', '.join(sorted(VALID_WIDGET_TYPES))})")
        return v


class WidgetResponse(BaseModel):
    """위젯 응답"""
    widget_id: int
    user_id: int
    tenant_id: Optional[int] = None
    title: str
    widget_type: str
    query: Optional[str] = None
    sql: Optional[str] = None
    chart_config: dict = {}
    cached_data: dict = {}
    grid_position: dict = {}
    sort_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_refreshed_at: Optional[str] = None


# ===================================
# 레이아웃 저장
# ===================================

class LayoutItem(BaseModel):
    """레이아웃 항목"""
    widget_id: int
    x: int
    y: int
    w: int
    h: int


class LayoutSaveRequest(BaseModel):
    """레이아웃 일괄 저장 요청"""
    layout: List[LayoutItem] = Field(..., min_length=1, description="레이아웃 항목 목록")


# ===================================
# SQL 실행
# ===================================

class ExecuteSqlRequest(BaseModel):
    """SQL 테스트 실행 요청"""
    sql: str = Field(..., min_length=1, description="실행할 SQL")
