"""시스템 설정 API 서비스

위치: app/api/services/settings_service.py
- 설정 CRUD 비즈니스 로직
- API Route 전용 서비스
- Core의 settings_config를 활용하여 캐싱/마스킹 처리
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import httpx

from app.core.config.settings_config import settings_config
# psycopg import 제거 - 어댑터 패턴으로 대체
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_db_manager = None
_external_db_manager = None


def _get_db_manager():
    """DB 매니저 지연 로딩"""
    global _db_manager
    if _db_manager is None:
        from app.core.database.connection import db_manager
        _db_manager = db_manager
    return _db_manager


def _get_external_db_manager():
    """외부 DB 매니저 지연 로딩"""
    global _external_db_manager
    if _external_db_manager is None:
        from app.core.database.external import external_db_manager
        _external_db_manager = external_db_manager
    return _external_db_manager


class SettingsService:
    """시스템 설정 API 서비스 (CRUD + 검증)"""

    # ============================================================================
    # 설정 조회 (Core settings_config 활용)
    # ============================================================================

    def get_all_settings_masked(self) -> Dict[str, List[Dict[str, Any]]]:
        """전체 설정 조회 (마스킹 적용)"""
        return settings_config.get_all_masked_settings()

    def get_category_settings_masked(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 설정 조회 (마스킹 적용)"""
        return settings_config.get_masked_settings(category)

    def get_setting(self, category: str, key: str, masked: bool = True) -> Optional[Dict[str, Any]]:
        """
        단일 설정 조회

        Args:
            category: 카테고리
            key: 설정 키
            masked: 마스킹 여부 (기본 True)
        """
        setting = settings_config.get_setting(category, key)
        if not setting:
            return None

        result = {
            'category': category,
            'key': key,
            **setting
        }

        if masked and setting.get('is_secret') and setting.get('value'):
            result['value'] = settings_config.mask_secret_value(setting['value'])

        return result

    def is_valid_category(self, category: str) -> bool:
        """유효한 카테고리인지 확인"""
        return category in settings_config.DEFAULTS

    def is_valid_key(self, category: str, key: str) -> bool:
        """유효한 설정 키인지 확인"""
        return (category in settings_config.DEFAULTS and key in settings_config.DEFAULTS[category])

    def get_category_key_count(self, category: str) -> int:
        """카테고리의 설정 키 개수 반환"""
        if category in settings_config.DEFAULTS:
            return len(settings_config.DEFAULTS[category])
        return 0

    # ============================================================================
    # 설정 수정
    # ============================================================================

    def update_setting(self, category: str, key: str, value: str, changed_by: str = 'admin', change_reason: str = None) -> bool:
        """
        단일 설정 수정

        Args:
            category: 카테고리
            key: 설정 키
            value: 새 값
            changed_by: 변경자
            change_reason: 변경 사유

        Returns:
            성공 여부
        """
        default = settings_config._get_default_value(category, key)
        if not default:
            logger.warning(f"알 수 없는 설정: {category}.{key}")
            return False

        # is_secret 필드이고 마스킹된 값(* 포함)이면 저장 스킵 (기존 값 유지)
        is_secret = default[3]
        if is_secret and value and '*' in value:
            logger.info(f"마스킹된 secret 값 저장 스킵: {category}.{key}")
            return True

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                # 프롬프트 카테고리인 경우 기존 값 조회 (이력 저장용)
                old_value = None
                if category == 'prompt':
                    cur.execute("SELECT value FROM tb_app_settings WHERE category = %s AND key = %s", (category, key))
                    row = cur.fetchone()
                    if row:
                        old_value = row['value']

                # 설정 저장 (UPSERT)
                cur.execute("""
                    INSERT INTO tb_app_settings (category, key, value, value_type, description, is_secret, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (category, key)
                    DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                    RETURNING updated_at
                """, (category, key, value, default[1], default[2], default[3]))

                row = cur.fetchone()
                updated_at = row['updated_at'] if row else datetime.now()

                # 프롬프트 카테고리인 경우 이력 저장
                if category == 'prompt' and old_value != value:
                    try:
                        cur.execute("""
                            INSERT INTO tb_prompt_history (category, key, old_value, new_value, changed_by, change_reason)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (category, key, old_value, value, changed_by, change_reason or 'Manual update'))
                        logger.info(f"프롬프트 이력 저장: {category}.{key}")
                    except Exception as hist_err:
                        logger.error(f"프롬프트 이력 저장 실패 (무시): {hist_err}")

                # 캐시 갱신 (settings_config에서 통합 관리)
                settings_config._update_cache(category, key, value, default[1], default[2], default[3], updated_at)

                # external_database 카테고리인 경우 external_db_manager 캐시도 갱신
                if category == 'external_database':
                    try:
                        ext_db_manager = _get_external_db_manager()
                        ext_db_manager.reload_config()
                        logger.info(f"외부 DB 설정 캐시 갱신 완료: {key}")
                    except Exception as reload_err:
                        logger.warning(f"외부 DB 캐시 갱신 실패 (무시): {reload_err}")

                logger.info(f"설정 저장: {category}.{key}")
                return True

        except Exception as e:
            logger.error(f"설정 저장 실패: {category}.{key} - {e}")
            return False

    def update_category_settings(self, category: str, settings_dict: Dict[str, str]) -> Tuple[int, List[str]]:
        """
        카테고리별 설정 일괄 수정

        Returns:
            (성공 개수, 실패한 키 목록)
        """
        success_count = 0
        failed_keys = []

        for key, value in settings_dict.items():
            # update_setting 내부에서 개별 키마다 reload_config 호출되므로 일단 저장
            if self._update_setting_without_reload(category, key, value):
                success_count += 1
            else:
                failed_keys.append(key)

        # external_database 카테고리인 경우 마지막에 한 번만 reload
        if category == 'external_database' and success_count > 0:
            try:
                ext_db_manager = _get_external_db_manager()
                ext_db_manager.reload_config()
                logger.info(f"외부 DB 설정 일괄 갱신 후 캐시 갱신 완료")
            except Exception as reload_err:
                logger.warning(f"외부 DB 캐시 갱신 실패 (무시): {reload_err}")

        # pii 카테고리인 경우 pii_service reload (전략/활성화 즉시 반영)
        if category == 'pii' and success_count > 0:
            try:
                from app.core.pii.pii_service import pii_service
                pii_service.reload()
                logger.info("PII 서비스 설정 갱신 완료")
            except Exception as reload_err:
                logger.warning(f"PII 서비스 갱신 실패 (무시): {reload_err}")

        return success_count, failed_keys

    def _update_setting_without_reload(self, category: str, key: str, value: str, changed_by: str = 'admin', change_reason: Optional[str] = None) -> bool:
        """단일 설정 수정 (external_db_manager reload 없이 - 일괄 수정용)"""
        default = settings_config._get_default_value(category, key)
        if not default:
            logger.warning(f"알 수 없는 설정: {category}.{key}")
            return False

        is_secret = default[3]
        if is_secret and value and '*' in value:
            logger.info(f"마스킹된 secret 값 저장 스킵: {category}.{key}")
            return True

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                old_value = None
                if category == 'prompt':
                    cur.execute("SELECT value FROM tb_app_settings WHERE category = %s AND key = %s", (category, key))
                    row = cur.fetchone()
                    if row:
                        old_value = row['value']

                cur.execute("""
                    INSERT INTO tb_app_settings (category, key, value, value_type, description, is_secret, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (category, key)
                    DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                    RETURNING updated_at
                """, (category, key, value, default[1], default[2], default[3]))

                row = cur.fetchone()
                updated_at = row['updated_at'] if row else datetime.now()

                if category == 'prompt' and old_value != value:
                    try:
                        cur.execute("""
                            INSERT INTO tb_prompt_history (category, key, old_value, new_value, changed_by, change_reason)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (category, key, old_value, value, changed_by, change_reason or 'Manual update'))
                    except Exception:
                        pass

                settings_config._update_cache(category, key, value, default[1], default[2], default[3], updated_at)
                return True

        except Exception as e:
            logger.error(f"설정 저장 실패: {category}.{key} - {e}")
            return False

    def reset_category(self, category: str) -> bool:
        """카테고리 설정을 기본값으로 초기화"""
        if category not in settings_config.DEFAULTS:
            return False

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                for key, (value, value_type, desc, is_secret) in settings_config.DEFAULTS[category].items():
                    cur.execute("""
                        UPDATE tb_app_settings SET value = %s, updated_at = NOW()
                        WHERE category = %s AND key = %s
                    """, (value, category, key))

                # 캐시 무효화 (settings_config에서 통합 관리)
                settings_config.refresh_cache()

                # external_database 카테고리인 경우 external_db_manager 캐시도 갱신
                if category == 'external_database':
                    try:
                        ext_db_manager = _get_external_db_manager()
                        ext_db_manager.reload_config()
                        logger.info("외부 DB 설정 초기화 후 캐시 갱신 완료")
                    except Exception as reload_err:
                        logger.warning(f"외부 DB 캐시 갱신 실패 (무시): {reload_err}")

                logger.info(f"카테고리 초기화: {category}")
                return True

        except Exception as e:
            logger.error(f"카테고리 초기화 실패: {category} - {e}")
            return False

    # ============================================================================
    # API 키 검증
    # ============================================================================

    async def validate_openai_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        OpenAI API 키 검증

        Returns:
            {"valid": bool, "message": str, "models": List[str] (유효한 경우)}
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    data = response.json()
                    models = [m["id"] for m in data.get("data", [])]
                    important_models = [m for m in models if any(key in m for key in ["gpt-4", "gpt-3.5", "text-embedding"])]
                    return {"valid": True, "message": "API 키가 유효합니다.", "models": sorted(important_models)}
                elif response.status_code == 401:
                    return {"valid": False, "message": "API 키가 유효하지 않습니다."}
                else:
                    return {"valid": False, "message": f"API 검증 실패: {response.status_code}"}

        except httpx.TimeoutException:
            return {"valid": False, "message": "API 서버 응답 시간 초과"}
        except Exception as e:
            logger.error(f"API 키 검증 실패: {e}", exc_info=True)
            return {"valid": False, "message": f"검증 중 오류 발생: {str(e)}"}

    # ============================================================================
    # 외부 DB 연결 테스트
    # ============================================================================

    def test_external_db_connection(self, db_type: str, host: str, port: int, database: str, username: str, password: str, schema: str) -> Dict[str, Any]:
        """
        외부 비즈니스 데이터베이스 연결 테스트

        비밀번호가 마스킹되어 있으면 DB에서 실제 비밀번호를 조회하여 사용
        """
        # 비밀번호가 마스킹되어 있으면 DB에서 실제 비밀번호 조회
        if password and '*' in password:
            setting = settings_config.get_setting('external_database', 'password')
            if setting and setting.get('value'):
                password = setting['value']
                logger.info("마스킹된 비밀번호를 DB에서 조회하여 사용")
            else:
                return {"success": False, "message": "저장된 비밀번호가 없습니다. 비밀번호를 입력해주세요."}

        # 필수 파라미터 검증
        if not all([host, database, username]):
            return {"success": False, "message": "호스트, 데이터베이스, 사용자명은 필수입니다."}

        # 어댑터 기반 연결 테스트
        try:
            from app.core.database.adapters.factory import get_adapter
            adapter = get_adapter(db_type)

            config = {
                'host': host,
                'port': port,
                'database': database,
                'username': username,
                'password': password,
                'schema': schema,
                'connection_timeout': 5
            }

            # 연결 테스트
            success, error_msg = adapter.test_connection(config)
            if not success:
                return {"success": False, "message": error_msg}

            # 스키마 및 테이블 확인
            url = adapter.build_connection_url(config)
            pool = adapter.create_pool(url, config)
            try:
                with adapter.get_connection(pool, schema) as conn:
                    with adapter.get_cursor(conn) as cur:
                        # 테이블 목록 조회
                        query, params = adapter.get_tables_query(schema)
                        cur.execute(query, params)
                        tables = cur.fetchall()
                        table_count = len(tables)

                return {"success": True, "message": f"연결 성공! (스키마: {schema}, 테이블 수: {table_count})"}
            finally:
                adapter.close_pool(pool)

        except ValueError as e:
            return {"success": False, "message": str(e)}
        except Exception as e:
            logger.error(f"외부 DB 연결 테스트 중 예외 발생: {e}", exc_info=True)
            return {"success": False, "message": f"연결 테스트 실패: {str(e)}"}

    # ============================================================================
    # 프롬프트 이력 관리
    # ============================================================================

    def get_prompt_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """프롬프트 변경 이력 조회"""
        limit = min(limit, 1000)

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT id, category, key, old_value, new_value, changed_by, changed_at, change_reason
                    FROM tb_prompt_history ORDER BY changed_at DESC LIMIT %s
                """, (limit,))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"프롬프트 이력 조회 실패: {e}")
            return []

    def get_prompt_history_by_key(self, category: str, key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """특정 프롬프트의 변경 이력 조회"""
        limit = min(limit, 500)

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT id, category, key, old_value, new_value, changed_by, changed_at, change_reason
                    FROM tb_prompt_history WHERE category = %s AND key = %s
                    ORDER BY changed_at DESC LIMIT %s
                """, (category, key, limit))
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"프롬프트 이력 조회 실패 ({category}.{key}): {e}")
            return []

    def restore_prompt_from_history(self, history_id: int, changed_by: str = 'admin') -> bool:
        """특정 이력으로 프롬프트 복원"""
        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("SELECT category, key, old_value, changed_at FROM tb_prompt_history WHERE id = %s", (history_id,))
                history = cur.fetchone()
                if not history:
                    logger.error(f"이력을 찾을 수 없습니다: {history_id}")
                    return False

                category = history['category']
                key = history['key']
                restore_value = history['old_value']

                if restore_value is None:
                    logger.error(f"복원할 값이 없습니다 (최초 생성 이력): {history_id}")
                    return False

                # 현재 값 조회
                cur.execute("SELECT value FROM tb_app_settings WHERE category = %s AND key = %s", (category, key))
                current_row = cur.fetchone()
                current_value = current_row['value'] if current_row else None

                # 프롬프트 값 업데이트
                cur.execute("UPDATE tb_app_settings SET value = %s, updated_at = NOW() WHERE category = %s AND key = %s", (restore_value, category, key))

                # 복원 이력 기록
                cur.execute("""
                    INSERT INTO tb_prompt_history (category, key, old_value, new_value, changed_by, change_reason)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (category, key, current_value, restore_value, changed_by, f'Restored from history #{history_id} ({history["changed_at"]})'))

                # 캐시 무효화 (settings_config에서 통합 관리)
                settings_config.refresh_cache()

                logger.info(f"프롬프트 복원 완료: {category}.{key} (history_id={history_id})")
                return True

        except Exception as e:
            logger.error(f"프롬프트 복원 실패: {e}")
            return False

    # ============================================================================
    # 캐시 관리
    # ============================================================================

    def refresh_cache(self) -> None:
        """설정 캐시 새로고침"""
        settings_config.refresh_cache()


# 싱글톤 인스턴스
settings_service = SettingsService()
