"""테넌트 관리 서비스

위치: app/api/services/tenant_service.py
테넌트 CRUD 비즈니스 로직
"""
import json
from typing import Any, Dict, Optional

from app.core.database.connection import db_manager
from app.core.errors import APIException, ErrorCode
from app.models.auth import UserContext
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class TenantService:
    """테넌트 관리 비즈니스 로직"""

    def list_tenants(self, request_id: str = "") -> Dict[str, Any]:
        """테넌트 목록 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT t.tenant_id, t.tenant_code, t.tenant_name, t.is_active, "
                "t.metadata, t.created_at, t.updated_at, "
                "(SELECT COUNT(*) FROM tb_user u WHERE u.tenant_id = t.tenant_id) as user_count "
                "FROM tb_tenant t ORDER BY t.tenant_id"
            )
            rows = cur.fetchall()

        items = [dict(row) for row in rows]
        log_step(logger, request_id, "TENANT", "1", "LIST", "테넌트 목록 조회", total=len(items))
        return {"total": len(items), "items": items}

    def get_tenant(self, tenant_id: int, request_id: str = "") -> Dict[str, Any]:
        """테넌트 상세 조회"""
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT t.tenant_id, t.tenant_code, t.tenant_name, t.is_active, "
                "t.metadata, t.created_at, t.updated_at, "
                "(SELECT COUNT(*) FROM tb_user u WHERE u.tenant_id = t.tenant_id) as user_count "
                "FROM tb_tenant t WHERE t.tenant_id = %s",
                (tenant_id,),
            )
            row = cur.fetchone()

        if not row:
            raise APIException(ErrorCode.NOT_FOUND, "테넌트를 찾을 수 없습니다")

        log_step(logger, request_id, "TENANT", "2", "GET", "테넌트 상세 조회", tenant_id=tenant_id)
        return dict(row)

    def create_tenant(self, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """테넌트 생성"""
        metadata_json = json.dumps(data.get("metadata")) if data.get("metadata") else None

        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(
                    "INSERT INTO tb_tenant (tenant_code, tenant_name, is_active, metadata) "
                    "VALUES (%s, %s, %s, %s::jsonb) RETURNING tenant_id",
                    (data["tenant_code"], data["tenant_name"], data.get("is_active", True), metadata_json),
                )
                new_id = cur.fetchone()["tenant_id"]
        except Exception as e:
            if "unique" in str(e).lower() or "duplicate" in str(e).lower():
                raise APIException(ErrorCode.DUPLICATE_ERROR, "이미 존재하는 테넌트 코드입니다")
            raise

        log_step(logger, request_id, "TENANT", "3", "CREATE", "테넌트 생성", tenant_id=new_id, tenant_code=data["tenant_code"])
        return self.get_tenant(new_id, request_id)

    def update_tenant(self, tenant_id: int, data: Dict[str, Any], current_user: UserContext, request_id: str = "") -> Dict[str, Any]:
        """테넌트 수정"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT tenant_id FROM tb_tenant WHERE tenant_id = %s", (tenant_id,))
            if not cur.fetchone():
                raise APIException(ErrorCode.NOT_FOUND, "테넌트를 찾을 수 없습니다")

        fields = []
        params: list = []

        if "tenant_name" in data and data["tenant_name"] is not None:
            fields.append("tenant_name = %s")
            params.append(data["tenant_name"])
        if "is_active" in data and data["is_active"] is not None:
            fields.append("is_active = %s")
            params.append(data["is_active"])
        if "metadata" in data:
            fields.append("metadata = %s::jsonb")
            params.append(json.dumps(data["metadata"]) if data["metadata"] else None)

        if not fields:
            raise APIException(ErrorCode.BAD_REQUEST, "수정할 필드가 없습니다")

        fields.append("updated_at = NOW()")
        params.append(tenant_id)

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(f"UPDATE tb_tenant SET {', '.join(fields)} WHERE tenant_id = %s", params)

        log_step(logger, request_id, "TENANT", "4", "UPDATE", "테넌트 수정", tenant_id=tenant_id)
        return self.get_tenant(tenant_id, request_id)

    def delete_tenant(self, tenant_id: int, current_user: UserContext, request_id: str = "") -> bool:
        """테넌트 삭제 (소속 사용자 있으면 비활성화, 없으면 삭제)"""
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT tenant_id, tenant_code FROM tb_tenant WHERE tenant_id = %s", (tenant_id,))
            existing = cur.fetchone()

        if not existing:
            raise APIException(ErrorCode.NOT_FOUND, "테넌트를 찾을 수 없습니다")

        # 소속 사용자 존재 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_user WHERE tenant_id = %s", (tenant_id,))
            user_count = cur.fetchone()["cnt"]

        if user_count > 0:
            # 소속 사용자가 있으면 비활성화
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("UPDATE tb_tenant SET is_active = false, updated_at = NOW() WHERE tenant_id = %s", (tenant_id,))
            log_step(logger, request_id, "TENANT", "5", "DEACTIVATE", "테넌트 비활성화 (사용자 존재)", tenant_id=tenant_id, user_count=user_count)
        else:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("DELETE FROM tb_tenant WHERE tenant_id = %s", (tenant_id,))
            log_step(logger, request_id, "TENANT", "5", "DELETE", "테넌트 삭제", tenant_id=tenant_id)

        return True


# 싱글톤 인스턴스
tenant_service = TenantService()
