"""테넌트 컨텍스트 (요청 범위 tenant_id 전달)

위치: app/core/security/tenant_context.py

Agent 도구(@tool)는 LLM이 호출하므로 파라미터에 tenant_id를 추가할 수 없습니다.
Python contextvars를 사용하여 요청 컨텍스트 내에서 tenant_id를 암묵적으로 전달합니다.

사용 패턴:
    # 라우트 핸들러에서 설정
    from app.core.security.tenant_context import set_tenant_id
    set_tenant_id(current_user.tenant_id)

    # Agent 도구 내부에서 읽기
    from app.core.security.tenant_context import get_tenant_id
    tenant_id = get_tenant_id()
"""
from contextvars import ContextVar
from typing import Optional

_current_tenant_id: ContextVar[Optional[str]] = ContextVar('current_tenant_id', default=None)


def set_tenant_id(tenant_id: Optional[str]) -> None:
    """현재 요청의 tenant_id 설정"""
    _current_tenant_id.set(str(tenant_id) if tenant_id else None)


def get_tenant_id() -> Optional[str]:
    """현재 요청의 tenant_id 조회"""
    return _current_tenant_id.get()
