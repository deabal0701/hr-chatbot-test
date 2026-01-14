"""
Config 모듈 - 동적 설정 관리

- settings_service: DB 설정 조회 (get_value 등)
"""
from app.core.config.settings_service import settings_service, SettingsService

__all__ = ["settings_service", "SettingsService"]
