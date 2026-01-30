"""
데이터베이스 어댑터 패키지

위치: app/core/database/adapters/__init__.py

모듈:
- base: DatabaseAdapter 추상 베이스 클래스
- postgresql: PostgreSQL 어댑터
- oracle: Oracle 어댑터
- factory: 어댑터 팩토리 함수들

사용법:
    from app.core.database.adapters.factory import get_adapter
    adapter = get_adapter("postgresql")
"""
