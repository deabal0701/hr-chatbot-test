"""도구 설정 확인 스크립트"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database.connection import db_manager
from app.core.config.settings_config import settings_config

def check_tools_config():
    print("=" * 60)
    print("도구 설정 확인")
    print("=" * 60)

    # 1. DB 직접 조회 (캐시 무시)
    print("\n[1] DB 직접 조회 (enabled_tools):")
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT value FROM tb_app_settings WHERE category = 'agent' AND key = 'enabled_tools'")
        row = cur.fetchone()
        if row:
            value = row.get('value') if isinstance(row, dict) else row[0]
            print(f"  DB 값: {value}")
            tools = [t.strip() for t in value.split(",")]
            print(f"  도구 수: {len(tools)}")
            for i, t in enumerate(tools, 1):
                print(f"    {i}. {t}")
            print(f"  context_search_tool 포함: {'context_search_tool' in value}")

    # 2. settings_config 캐시 조회
    print("\n[2] settings_config 캐시 조회:")
    cached_value = settings_config.get_value("agent", "enabled_tools", "기본값")
    print(f"  캐시 값: {cached_value}")
    print(f"  context_search_tool 포함: {'context_search_tool' in cached_value}")

    # 3. use_cache=False로 조회
    print("\n[3] DB 강제 조회 (use_cache=False):")
    direct_value = settings_config.get_value("agent", "enabled_tools", "기본값", use_cache=False)
    print(f"  직접 조회 값: {direct_value}")
    print(f"  context_search_tool 포함: {'context_search_tool' in direct_value}")

    # 4. LLM 모델 확인
    print("\n[4] LLM 모델 설정:")
    model = settings_config.get_value("llm", "model", "미설정")
    print(f"  현재 모델: {model}")


if __name__ == "__main__":
    check_tools_config()
