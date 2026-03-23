"""API 요청 이력 서비스

위치: app/api/services/history_service.py
- API 요청 이력 저장 및 조회
- 비동기 백그라운드 저장 지원
- 멀티테넌트 및 사용자별 조회 지원
"""
import json
import threading
from datetime import datetime, timedelta
from queue import Queue, Empty
from typing import Any, Dict, List, Optional

from app.core.database.connection import db_manager
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class HistoryService:
    """API 요청 이력 서비스 (비동기 저장 지원)"""

    def __init__(self, async_save: bool = True, batch_size: int = 10, flush_interval: float = 1.0):
        """
        Args:
            async_save: True면 백그라운드 스레드에서 저장
            batch_size: 배치 저장 시 한번에 저장할 항목 수
            flush_interval: 배치 대기 타임아웃 (초)
        """
        self._async_save = async_save
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._queue: Queue = Queue()
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False

        if self._async_save:
            self._start_worker()

    def _start_worker(self) -> None:
        """백그라운드 워커 스레드 시작"""
        self._running = True

        def worker():
            while self._running:
                try:
                    batch = []
                    # 배치 수집 (최대 batch_size 또는 flush_interval 대기)
                    while len(batch) < self._batch_size:
                        try:
                            item = self._queue.get(timeout=self._flush_interval)
                            batch.append(item)
                            self._queue.task_done()
                        except Empty:
                            break

                    if batch:
                        self._save_batch(batch)
                except Exception as e:
                    logger.error(f"[HISTORY] Worker error: {e}")

        self._worker_thread = threading.Thread(target=worker, daemon=True, name="HistoryWorker")
        self._worker_thread.start()
        logger.info("[HISTORY] Background worker started")

    def stop_worker(self) -> None:
        """백그라운드 워커 중지"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
            logger.info("[HISTORY] Background worker stopped")

    def _save_batch(self, batch: List[Dict]) -> None:
        """배치 저장"""
        try:
            with db_manager.get_cursor(commit=True) as cur:
                for record in batch:
                    self._insert_record(cur, record)
            log_step(logger, "system", "HISTORY", "BATCH", "SAVE", f"Batch saved", count=len(batch))
        except Exception as e:
            logger.error(f"[HISTORY] Batch save failed: {e}")

    def _insert_record(self, cur, record: Dict) -> None:
        """단일 레코드 삽입 (created_at은 DB DEFAULT NOW() 자동생성)"""
        cur.execute("""
            INSERT INTO tb_api_history (
                tenant_id, user_id, user_name,
                request_id, session_id,
                request_type, endpoint,
                question, answer, response_code, success, error_message,
                trace_data, response_time_ms, llm_calls_count, tokens_used,
                client_ip, user_agent,
                requested_at, completed_at
            ) VALUES (
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s,
                %s, %s
            )
        """, (
            record.get('tenant_id'),
            record.get('user_id'),
            record.get('user_name'),
            record.get('request_id'),
            record.get('session_id'),
            record.get('request_type'),
            record.get('endpoint'),
            record.get('question'),
            record.get('answer'),
            record.get('response_code', 200),
            record.get('success', True),
            record.get('error_message'),
            json.dumps(record.get('trace_data'), ensure_ascii=False) if record.get('trace_data') else None,
            record.get('response_time_ms', 0),
            record.get('llm_calls_count'),
            record.get('tokens_used'),
            record.get('client_ip'),
            record.get('user_agent'),
            record.get('requested_at', datetime.now()),
            record.get('completed_at'),
        ))

    # =========================================================================
    # 저장 메서드
    # =========================================================================

    def save_request(self, record: Dict[str, Any]) -> None:
        """
        요청 이력 저장 (비동기 또는 동기)

        Args:
            record: 저장할 이력 데이터
        """
        if self._async_save:
            self._queue.put(record)
        else:
            try:
                with db_manager.get_cursor(commit=True) as cur:
                    self._insert_record(cur, record)
            except Exception as e:
                logger.error(f"[HISTORY] Save failed: {e}")

    def save_agent_request(
        self,
        request_id: str,
        question: str,
        answer: str,
        steps: List[Dict],
        tools_used: List[str],
        iteration_count: int,
        response_time_ms: int,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        client_ip: Optional[str] = None,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """Agent 요청 이력 저장"""
        trace_data = {
            "steps": steps,
            "tools_used": tools_used,
            "iteration_count": iteration_count,
        }
        if metadata:
            trace_data["metadata"] = metadata

        self.save_request({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "user_name": user_name,
            "request_id": request_id,
            "session_id": session_id,
            "request_type": "agent",
            "endpoint": "/api/v1/agent/search",
            "question": question,
            "answer": answer,
            "response_code": 200 if success else 500,
            "success": success,
            "error_message": error_message,
            "trace_data": trace_data,
            "response_time_ms": response_time_ms,
            "client_ip": client_ip,
            "requested_at": requested_at or datetime.now(),
            "completed_at": completed_at or datetime.now(),
        })

    def save_nl2sql_request(
        self,
        request_id: str,
        question: str,
        answer: str,
        sql: str,
        sql_result: Optional[Dict],
        current_turn: int,
        response_time_ms: int,
        session_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        client_ip: Optional[str] = None,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """NL2SQL 요청 이력 저장"""
        trace_data = {
            "sql": sql,
            "sql_result": sql_result,
            "current_turn": current_turn,
            "validation_passed": success,
        }
        if metadata:
            trace_data["metadata"] = metadata

        self.save_request({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "user_name": user_name,
            "request_id": request_id,
            "session_id": session_id,
            "request_type": "nl2sql",
            "endpoint": "/api/v1/search",
            "question": question,
            "answer": answer,
            "response_code": 200 if success else 500,
            "success": success,
            "error_message": error_message,
            "trace_data": trace_data,
            "response_time_ms": response_time_ms,
            "client_ip": client_ip,
            "requested_at": requested_at or datetime.now(),
            "completed_at": completed_at or datetime.now(),
        })

    def save_rag_request(
        self,
        request_id: str,
        question: str,
        answer: str,
        sources: List[Dict],
        response_time_ms: int,
        success: bool = True,
        error_message: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        client_ip: Optional[str] = None,
        requested_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> None:
        """RAG 요청 이력 저장"""
        # 소스에서 유사도 추출
        top_similarity = None
        if sources:
            similarities = [s.get('similarity_score') or s.get('similarity') for s in sources if s.get('similarity_score') or s.get('similarity')]
            if similarities:
                top_similarity = max(similarities)

        trace_data = {
            "sources": sources,
            "sources_count": len(sources),
            "top_similarity": top_similarity,
        }

        self.save_request({
            "tenant_id": tenant_id,
            "user_id": user_id,
            "user_name": user_name,
            "request_id": request_id,
            "session_id": None,
            "request_type": "rag",
            "endpoint": "/api/v1/search",
            "question": question,
            "answer": answer,
            "response_code": 200 if success else 500,
            "success": success,
            "error_message": error_message,
            "trace_data": trace_data,
            "response_time_ms": response_time_ms,
            "client_ip": client_ip,
            "requested_at": requested_at or datetime.now(),
            "completed_at": completed_at or datetime.now(),
        })

    # =========================================================================
    # 조회 메서드
    # =========================================================================

    def get_history(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_type: Optional[str] = None,
        title: Optional[str] = None,
        success_only: Optional[bool] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        이력 조회 (필터 지원)

        Args:
            tenant_id: 테넌트 ID 필터 (멀티테넌트)
            user_id: 사용자 ID 필터 (내 이력)
            request_type: 요청 타입 필터 (agent/nl2sql/rag)
            title: 제목(질문) 검색 (ILIKE 부분 일치)
            success_only: 성공만 조회
            from_date: 시작일
            to_date: 종료일
            limit: 조회 개수
            offset: 오프셋

        Returns:
            이력 레코드 목록
        """
        conditions = []
        params = []

        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(tenant_id)

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

        if request_type:
            conditions.append("request_type = %s")
            params.append(request_type)

        if title:
            conditions.append("question ILIKE %s")
            params.append(f"%{title}%")

        if success_only is not None:
            conditions.append("success = %s")
            params.append(success_only)

        if from_date:
            conditions.append("created_at >= %s")
            params.append(from_date)

        if to_date:
            conditions.append("created_at <= %s")
            params.append(to_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        params.extend([limit, offset])

        try:
            with db_manager.get_cursor() as cur:
                cur.execute(f"""
                    SELECT * FROM tb_api_history
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"[HISTORY] Query failed: {e}")
            return []

    def get_history_count(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        request_type: Optional[str] = None,
        title: Optional[str] = None,
        success_only: Optional[bool] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> int:
        """전체 레코드 수 조회 (페이징용)"""
        conditions = []
        params = []

        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(tenant_id)

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

        if request_type:
            conditions.append("request_type = %s")
            params.append(request_type)

        if title:
            conditions.append("question ILIKE %s")
            params.append(f"%{title}%")

        if success_only is not None:
            conditions.append("success = %s")
            params.append(success_only)

        if from_date:
            conditions.append("created_at >= %s")
            params.append(from_date)

        if to_date:
            conditions.append("created_at <= %s")
            params.append(to_date)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        try:
            with db_manager.get_cursor() as cur:
                cur.execute(f"SELECT COUNT(*) as cnt FROM tb_api_history WHERE {where_clause}", params)
                row = cur.fetchone()
                return row['cnt'] if row else 0
        except Exception as e:
            logger.error(f"[HISTORY] Count failed: {e}")
            return 0

    def get_by_request_id(self, request_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """단일 요청 조회 (테넌트/사용자 필터 지원)"""
        try:
            conditions = ["request_id = %s"]
            params = [request_id]

            if tenant_id:
                conditions.append("tenant_id = %s")
                params.append(tenant_id)
            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)

            where_clause = " AND ".join(conditions)
            with db_manager.get_cursor() as cur:
                cur.execute(f"SELECT * FROM tb_api_history WHERE {where_clause}", params)
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"[HISTORY] Lookup failed: {e}")
            return None

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """세션별 이력 조회"""
        return self.get_history(session_id=session_id, limit=1000)

    def get_user_history(self, user_id: str, tenant_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """사용자별 이력 조회 (내 이력)"""
        return self.get_history(tenant_id=tenant_id, user_id=user_id, limit=limit)

    def get_statistics(
        self,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """통계 조회"""
        conditions = []
        params = []

        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(tenant_id)

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

        if from_date:
            conditions.append("created_at >= %s")
            params.append(from_date)

        if to_date:
            conditions.append("created_at <= %s")
            params.append(to_date)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        try:
            with db_manager.get_cursor() as cur:
                cur.execute(f"""
                    SELECT
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN success THEN 1 END) as success_count,
                        COUNT(CASE WHEN NOT success THEN 1 END) as error_count,
                        COALESCE(AVG(response_time_ms), 0) as avg_response_time_ms,
                        MIN(response_time_ms) as min_response_time_ms,
                        MAX(response_time_ms) as max_response_time_ms,
                        COUNT(CASE WHEN request_type = 'agent' THEN 1 END) as agent_count,
                        COUNT(CASE WHEN request_type = 'nl2sql' THEN 1 END) as nl2sql_count,
                        COUNT(CASE WHEN request_type = 'rag' THEN 1 END) as rag_count
                    FROM tb_api_history
                    {where_clause}
                """, params)
                row = cur.fetchone()
                if row:
                    result = dict(row)
                    total = result.get('total_requests', 0)
                    success = result.get('success_count', 0)
                    result['success_rate'] = round((success / total * 100), 2) if total > 0 else 0.0
                    result['from_date'] = from_date
                    result['to_date'] = to_date
                    return result
                return {}
        except Exception as e:
            logger.error(f"[HISTORY] Statistics failed: {e}")
            return {}

    def get_user_summary(self, user_id: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """사용자별 요약 (내 이력 요약)"""
        try:
            with db_manager.get_cursor() as cur:
                conditions = ["user_id = %s"]
                params = [user_id]

                if tenant_id:
                    conditions.append("tenant_id = %s")
                    params.append(tenant_id)

                where_clause = " AND ".join(conditions)

                # 기본 통계
                cur.execute(f"""
                    SELECT
                        COUNT(*) as total_requests,
                        COUNT(CASE WHEN request_type = 'agent' THEN 1 END) as agent_count,
                        COUNT(CASE WHEN request_type = 'nl2sql' THEN 1 END) as nl2sql_count,
                        COUNT(CASE WHEN request_type = 'rag' THEN 1 END) as rag_count,
                        MIN(created_at) as first_request_at,
                        MAX(created_at) as last_request_at,
                        MAX(user_name) as user_name
                    FROM tb_api_history
                    WHERE {where_clause}
                """, params)
                stats = cur.fetchone()

                # 최근 요청 (10개)
                cur.execute(f"""
                    SELECT * FROM tb_api_history
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT 10
                """, params)
                recent = [dict(row) for row in cur.fetchall()]

                return {
                    "user_id": user_id,
                    "user_name": stats['user_name'] if stats else None,
                    "total_requests": stats['total_requests'] if stats else 0,
                    "agent_count": stats['agent_count'] if stats else 0,
                    "nl2sql_count": stats['nl2sql_count'] if stats else 0,
                    "rag_count": stats['rag_count'] if stats else 0,
                    "first_request_at": stats['first_request_at'] if stats else None,
                    "last_request_at": stats['last_request_at'] if stats else None,
                    "recent_requests": recent,
                }
        except Exception as e:
            logger.error(f"[HISTORY] User summary failed: {e}")
            return {"user_id": user_id, "total_requests": 0, "recent_requests": []}

    # 사이드바 이력 표시 기간 (일) - 추후 변경 가능
    SIDEBAR_HISTORY_DAYS = 30

    def get_session_list(
        self,
        search_query: Optional[str] = None,
        request_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """세션 단위 이력 목록 조회 (사이드바용, 테넌트/사용자 필터 지원)

        session_id가 있는 레코드는 session_id로 그룹핑하고,
        session_id가 NULL인 레코드(RAG 등)는 request_id를 session_key로 사용한다.
        """
        conditions = ["success = true", f"created_at >= NOW() - INTERVAL '{self.SIDEBAR_HISTORY_DAYS} days'"]
        params = []

        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(tenant_id)

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

        if search_query:
            conditions.append("question ILIKE %s")
            params.append(f"%{search_query}%")

        if request_type:
            conditions.append("request_type = %s")
            params.append(request_type)

        where_clause = " AND ".join(conditions)
        params.extend([limit, offset])

        try:
            with db_manager.get_cursor() as cur:
                cur.execute(f"""
                    SELECT
                        COALESCE(session_id, request_id) as session_key,
                        (ARRAY_AGG(question ORDER BY created_at ASC))[1] as title,
                        MAX(request_type) as request_type,
                        COUNT(*) as message_count,
                        MIN(created_at) as created_at,
                        MAX(created_at) as last_activity
                    FROM tb_api_history
                    WHERE {where_clause}
                    GROUP BY COALESCE(session_id, request_id)
                    ORDER BY last_activity DESC
                    LIMIT %s OFFSET %s
                """, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"[HISTORY] Session list failed: {e}")
            return []

    def get_session_list_count(
        self,
        search_query: Optional[str] = None,
        request_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> int:
        """세션 단위 이력 총 개수 조회 (테넌트/사용자 필터 지원)"""
        conditions = ["success = true", f"created_at >= NOW() - INTERVAL '{self.SIDEBAR_HISTORY_DAYS} days'"]
        params = []

        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(tenant_id)

        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

        if search_query:
            conditions.append("question ILIKE %s")
            params.append(f"%{search_query}%")

        if request_type:
            conditions.append("request_type = %s")
            params.append(request_type)

        where_clause = " AND ".join(conditions)

        try:
            with db_manager.get_cursor() as cur:
                cur.execute(f"""
                    SELECT COUNT(DISTINCT COALESCE(session_id, request_id)) as cnt
                    FROM tb_api_history
                    WHERE {where_clause}
                """, params)
                row = cur.fetchone()
                return row['cnt'] if row else 0
        except Exception as e:
            logger.error(f"[HISTORY] Session list count failed: {e}")
            return 0

    def delete_session(self, session_key: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> int:
        """세션 단위 이력 삭제 (session_id 또는 request_id로 삭제, 테넌트/사용자 필터 지원)"""
        try:
            conditions = ["(session_id = %s OR request_id = %s)"]
            params = [session_key, session_key]

            if tenant_id:
                conditions.append("tenant_id = %s")
                params.append(tenant_id)
            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)

            where_clause = " AND ".join(conditions)
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(f"DELETE FROM tb_api_history WHERE {where_clause}", params)
                deleted = cur.rowcount
                log_step(logger, "system", "HISTORY", "DELETE_SESSION", "COMPLETE", f"Session deleted | session_key={session_key}, deleted={deleted}")
                return deleted
        except Exception as e:
            logger.error(f"[HISTORY] Session delete failed: {e}")
            return 0

    def get_session_detail(self, session_key: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """세션 키로 이력 상세 조회 (session_id 또는 request_id, 테넌트/사용자 필터 지원)"""
        try:
            conditions = ["(session_id = %s OR request_id = %s)"]
            params = [session_key, session_key]

            if tenant_id:
                conditions.append("tenant_id = %s")
                params.append(tenant_id)
            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)

            where_clause = " AND ".join(conditions)
            with db_manager.get_cursor() as cur:
                cur.execute(f"SELECT * FROM tb_api_history WHERE {where_clause} ORDER BY created_at ASC", params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"[HISTORY] Session detail failed: {e}")
            return []

    def delete_by_request_id(self, request_id: str, tenant_id: Optional[str] = None, user_id: Optional[str] = None) -> bool:
        """단일 요청 이력 삭제 (테넌트/사용자 필터 지원)

        Args:
            request_id: 삭제할 요청 ID
            tenant_id: 테넌트 ID 필터
            user_id: 사용자 ID 필터

        Returns:
            삭제 성공 여부
        """
        try:
            conditions = ["request_id = %s"]
            params = [request_id]

            if tenant_id:
                conditions.append("tenant_id = %s")
                params.append(tenant_id)
            if user_id:
                conditions.append("user_id = %s")
                params.append(user_id)

            where_clause = " AND ".join(conditions)
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(f"DELETE FROM tb_api_history WHERE {where_clause}", params)
                deleted = cur.rowcount > 0
                log_step(logger, "system", "HISTORY", "DELETE", "COMPLETE", f"Record deleted | request_id={request_id}, success={deleted}")
                return deleted
        except Exception as e:
            logger.error(f"[HISTORY] Delete failed: {e}")
            return False

    def cleanup_old_records(self, days: int = 90, tenant_id: Optional[str] = None) -> int:
        """
        오래된 이력 정리

        Args:
            days: 보관 기간 (일)
            tenant_id: 테넌트 ID (지정 시 해당 테넌트만 정리)

        Returns:
            삭제된 레코드 수
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        conditions = ["created_at < %s"]
        params = [cutoff_date]

        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(tenant_id)

        where_clause = " AND ".join(conditions)

        try:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute(f"DELETE FROM tb_api_history WHERE {where_clause}", params)
                deleted = cur.rowcount
                log_step(logger, "system", "HISTORY", "CLEANUP", "COMPLETE", f"Old records deleted", days=days, deleted=deleted)
                return deleted
        except Exception as e:
            logger.error(f"[HISTORY] Cleanup failed: {e}")
            return 0


# 싱글톤 인스턴스
history_service = HistoryService(async_save=True, batch_size=10, flush_interval=1.0)
