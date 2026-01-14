"""코드 마스터 관리 서비스 (Phase A: 코드 관리 시스템)

위치: app/api/services/code_service.py
- LLM 제공자, 모델, 임베딩 모델 등 코드성 데이터를 동적으로 관리
- API Route 전용 서비스
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_db_manager = None


def _get_db_manager():
    global _db_manager
    if _db_manager is None:
        from app.core.database.connection import db_manager
        _db_manager = db_manager
    return _db_manager


class CodeService:
    """코드 마스터 CRUD 서비스"""

    @staticmethod
    def get_code_groups() -> List[str]:
        """
        모든 코드 그룹 목록 조회

        Returns:
            코드 그룹 목록 (중복 제거, 정렬됨)
        """
        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT code_group
                    FROM code_master
                    ORDER BY code_group
                """)
                rows = cur.fetchall()
                return [row['code_group'] for row in rows]
        except Exception as e:
            logger.error(f"코드 그룹 조회 실패: {e}")
            raise

    @staticmethod
    def get_codes_by_group(
        code_group: str,
        include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        특정 그룹의 코드 목록 조회

        Args:
            code_group: 코드 그룹명
            include_inactive: 비활성 코드 포함 여부 (기본: False)

        Returns:
            코드 목록 (sort_order 순으로 정렬)
        """
        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                # 활성 여부 필터 추가
                active_filter = "" if include_inactive else "AND is_active = true"

                cur.execute(f"""
                    SELECT
                        code_id,
                        code_group,
                        code_value,
                        code_name,
                        description,
                        metadata,
                        sort_order,
                        is_active,
                        is_system,
                        created_at,
                        updated_at
                    FROM code_master
                    WHERE code_group = %s {active_filter}
                    ORDER BY sort_order, code_value
                """, (code_group,))

                rows = cur.fetchall()

                codes = []
                for row in rows:
                    # row is already a dict thanks to dict_row factory
                    # datetime을 ISO 형식 문자열로 변환
                    if row.get('created_at'):
                        created_at = row['created_at']
                        row['created_at'] = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)
                    if row.get('updated_at'):
                        updated_at = row['updated_at']
                        row['updated_at'] = updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at)
                    codes.append(row)

                logger.info(f"코드 조회 성공: {code_group} - {len(codes)}개")
                return codes

        except Exception as e:
            logger.error(f"코드 조회 실패 (그룹: {code_group}): {e}")
            raise

    @staticmethod
    def get_code_by_id(code_id: int) -> Optional[Dict[str, Any]]:
        """
        코드 ID로 단건 조회

        Args:
            code_id: 코드 ID

        Returns:
            코드 정보 (없으면 None)
        """
        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT
                        code_id,
                        code_group,
                        code_value,
                        code_name,
                        description,
                        metadata,
                        sort_order,
                        is_active,
                        is_system,
                        created_at,
                        updated_at
                    FROM code_master
                    WHERE code_id = %s
                """, (code_id,))

                row = cur.fetchone()
                if not row:
                    return None

                # row is already a dict thanks to dict_row factory
                # datetime 변환
                if row.get('created_at'):
                    created_at = row['created_at']
                    row['created_at'] = created_at.isoformat() if hasattr(created_at, 'isoformat') else str(created_at)
                if row.get('updated_at'):
                    updated_at = row['updated_at']
                    row['updated_at'] = updated_at.isoformat() if hasattr(updated_at, 'isoformat') else str(updated_at)

                return row

        except Exception as e:
            logger.error(f"코드 조회 실패 (ID: {code_id}): {e}")
            raise

    @staticmethod
    def create_code(code_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        코드 생성 (사용자 코드만 생성 가능, is_system=False)

        Args:
            code_data: 코드 정보
                - code_group (필수)
                - code_value (필수)
                - code_name (필수)
                - description (선택)
                - metadata (선택, dict)
                - sort_order (선택, 기본 0)
                - is_active (선택, 기본 True)

        Returns:
            생성된 코드 정보 (code_id 포함)

        Raises:
            ValueError: 중복된 코드 또는 필수 필드 누락
        """
        try:
            # 필수 필드 검증
            required_fields = ['code_group', 'code_value', 'code_name']
            for field in required_fields:
                if not code_data.get(field):
                    raise ValueError(f"필수 필드 누락: {field}")

            # 기본값 설정
            code_group = code_data['code_group']
            code_value = code_data['code_value']
            code_name = code_data['code_name']
            description = code_data.get('description', '')
            metadata = code_data.get('metadata')
            sort_order = code_data.get('sort_order', 0)
            is_active = code_data.get('is_active', True)
            is_system = False  # 사용자 생성 코드는 항상 False

            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                # 중복 체크
                cur.execute("""
                    SELECT code_id FROM code_master
                    WHERE code_group = %s AND code_value = %s
                """, (code_group, code_value))

                if cur.fetchone():
                    raise ValueError(f"중복된 코드: {code_group}.{code_value}")

                # 코드 생성
                cur.execute("""
                    INSERT INTO code_master (
                        code_group, code_value, code_name,
                        description, metadata, sort_order,
                        is_active, is_system
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING code_id
                """, (
                    code_group, code_value, code_name,
                    description, metadata, sort_order,
                    is_active, is_system
                ))

                code_id = cur.fetchone()['code_id']

            # 커밋 완료 후 생성된 코드 조회
            logger.info(f"코드 생성 성공: {code_group}.{code_value} (ID: {code_id})")
            return CodeService.get_code_by_id(code_id)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"코드 생성 실패: {e}")
            raise

    @staticmethod
    def update_code(code_id: int, code_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        코드 수정

        Args:
            code_id: 코드 ID
            code_data: 수정할 필드
                - code_name (선택)
                - description (선택)
                - metadata (선택, dict)
                - sort_order (선택)
                - is_active (선택)

        Returns:
            수정된 코드 정보

        Raises:
            ValueError: 코드 없음, 시스템 코드 수정 시도, code_group/code_value 변경 시도
        """
        try:
            # 기존 코드 확인
            existing_code = CodeService.get_code_by_id(code_id)
            if not existing_code:
                raise ValueError(f"코드를 찾을 수 없습니다: {code_id}")

            # code_group, code_value 변경 시도 시 에러
            if 'code_group' in code_data or 'code_value' in code_data:
                raise ValueError("code_group과 code_value는 수정할 수 없습니다.")

            # 수정 가능한 필드만 추출
            update_fields = {}
            allowed_fields = ['code_name', 'description', 'metadata', 'sort_order', 'is_active']

            for field in allowed_fields:
                if field in code_data:
                    update_fields[field] = code_data[field]

            if not update_fields:
                raise ValueError("수정할 필드가 없습니다.")

            # SQL 동적 생성
            set_clauses = []
            params = []
            for field, value in update_fields.items():
                set_clauses.append(f"{field} = %s")
                params.append(value)

            # updated_at 추가 (트리거 대신 직접 갱신)
            set_clauses.append("updated_at = %s")
            params.append(datetime.now())

            # WHERE 조건 파라미터
            params.append(code_id)

            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                sql = f"""
                    UPDATE code_master
                    SET {', '.join(set_clauses)}
                    WHERE code_id = %s
                """
                cur.execute(sql, params)

                if cur.rowcount == 0:
                    raise ValueError(f"코드 수정 실패: {code_id}")

                logger.info(f"코드 수정 성공: {code_id} - {list(update_fields.keys())}")

                # 수정된 코드 조회 후 반환
                return CodeService.get_code_by_id(code_id)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"코드 수정 실패 (ID: {code_id}): {e}")
            raise

    @staticmethod
    def delete_code(code_id: int) -> bool:
        """
        코드 삭제 (시스템 코드는 삭제 불가)

        Args:
            code_id: 코드 ID

        Returns:
            삭제 성공 여부

        Raises:
            ValueError: 코드 없음 또는 시스템 코드 삭제 시도
        """
        try:
            # 기존 코드 확인
            existing_code = CodeService.get_code_by_id(code_id)
            if not existing_code:
                raise ValueError(f"코드를 찾을 수 없습니다: {code_id}")

            # 시스템 코드 삭제 차단
            if existing_code['is_system']:
                raise ValueError(
                    f"시스템 코드는 삭제할 수 없습니다: "
                    f"{existing_code['code_group']}.{existing_code['code_value']}"
                )

            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("""
                    DELETE FROM code_master
                    WHERE code_id = %s AND is_system = false
                """, (code_id,))

                if cur.rowcount == 0:
                    raise ValueError(f"코드 삭제 실패: {code_id}")

                logger.info(
                    f"코드 삭제 성공: {existing_code['code_group']}.{existing_code['code_value']} "
                    f"(ID: {code_id})"
                )
                return True

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"코드 삭제 실패 (ID: {code_id}): {e}")
            raise

    @staticmethod
    def reorder_codes(code_group: str, code_id_order: List[int]) -> bool:
        """
        코드 순서 변경 (일괄 업데이트)

        Args:
            code_group: 코드 그룹명
            code_id_order: 코드 ID 목록 (순서대로)

        Returns:
            성공 여부

        Raises:
            ValueError: 그룹 불일치, 코드 누락 등
        """
        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor(commit=True) as cur:
                # 해당 그룹의 모든 코드 조회
                cur.execute("""
                    SELECT code_id FROM code_master
                    WHERE code_group = %s
                    ORDER BY sort_order
                """, (code_group,))

                existing_ids = {row['code_id'] for row in cur.fetchall()}

                # 입력된 ID 검증
                input_ids = set(code_id_order)
                if input_ids != existing_ids:
                    missing = existing_ids - input_ids
                    extra = input_ids - existing_ids
                    error_msg = []
                    if missing:
                        error_msg.append(f"누락된 코드 ID: {missing}")
                    if extra:
                        error_msg.append(f"존재하지 않는 코드 ID: {extra}")
                    raise ValueError(", ".join(error_msg))

                # 순서대로 sort_order 업데이트
                now = datetime.now()
                for idx, code_id in enumerate(code_id_order, start=1):
                    cur.execute("""
                        UPDATE code_master
                        SET sort_order = %s, updated_at = %s
                        WHERE code_id = %s
                    """, (idx, now, code_id))

                logger.info(f"코드 순서 변경 성공: {code_group} - {len(code_id_order)}개")
                return True

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"코드 순서 변경 실패 (그룹: {code_group}): {e}")
            raise


# 싱글톤 인스턴스
code_service = CodeService()
