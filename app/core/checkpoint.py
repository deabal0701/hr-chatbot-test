"""
BoundedInMemorySaver - TTL + 최대 세션 수 제한이 있는 InMemorySaver

InMemorySaver는 세션 데이터를 무한히 축적하여 메모리 누수를 유발합니다.
BoundedInMemorySaver는 다음 메커니즘으로 메모리를 관리합니다:

1. TTL (Time-To-Live): 마지막 접근 후 일정 시간이 지나면 자동 정리
2. max_sessions: 최대 세션 수 초과 시 가장 오래된 세션부터 제거 (LRU)
3. cleanup_interval: 주기적 정리 실행 (put 호출 시 트리거)
"""

import time
import threading
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.runnables import RunnableConfig

from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class BoundedInMemorySaver(InMemorySaver):
    """TTL + 최대 세션 수 제한이 있는 InMemorySaver

    Args:
        ttl_seconds: 세션 TTL (기본 24시간)
        max_sessions: 최대 세션 수 (기본 1000)
        cleanup_interval: 정리 주기 (기본 5분)
    """

    def __init__(
        self,
        *,
        ttl_seconds: int = 86400,
        max_sessions: int = 1000,
        cleanup_interval: int = 300,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.ttl_seconds = ttl_seconds
        self.max_sessions = max_sessions
        self.cleanup_interval = cleanup_interval
        self._last_access: dict[str, float] = {}
        self._last_cleanup: float = time.time()
        self._lock = threading.Lock()

        log_step(logger, "SYSTEM", "CHECKPOINT", "INIT", "SETUP", "BoundedInMemorySaver 초기화", ttl=ttl_seconds, max_sessions=max_sessions)

    def put(self, config: RunnableConfig, checkpoint: dict, metadata: dict, new_versions: dict) -> RunnableConfig:
        """체크포인트 저장 + TTL 갱신 + 정리 트리거"""
        thread_id = config["configurable"]["thread_id"]

        with self._lock:
            self._last_access[thread_id] = time.time()

        # 정리 실행 (주기적)
        now = time.time()
        if now - self._last_cleanup > self.cleanup_interval:
            self._cleanup()

        return super().put(config, checkpoint, metadata, new_versions)

    def get_tuple(self, config: RunnableConfig):
        """체크포인트 조회 + TTL 갱신"""
        thread_id = config["configurable"]["thread_id"]

        with self._lock:
            self._last_access[thread_id] = time.time()

        return super().get_tuple(config)

    async def aget_tuple(self, config: RunnableConfig):
        """비동기 체크포인트 조회 + TTL 갱신"""
        thread_id = config["configurable"]["thread_id"]

        with self._lock:
            self._last_access[thread_id] = time.time()

        return await super().aget_tuple(config)

    def get(self, config: RunnableConfig):
        """체크포인트 조회 (get_tuple 래퍼) + TTL 갱신"""
        thread_id = config["configurable"]["thread_id"]

        with self._lock:
            self._last_access[thread_id] = time.time()

        return super().get(config)

    def _cleanup(self) -> None:
        """만료된 세션 정리 + 최대 세션 수 초과 시 LRU 제거"""
        now = time.time()
        self._last_cleanup = now
        evict_count = 0

        with self._lock:
            access_copy = dict(self._last_access)

        if not access_copy:
            return

        # 1. TTL 만료 세션 제거
        expired = [tid for tid, last in access_copy.items() if now - last > self.ttl_seconds]
        for tid in expired:
            self._evict_thread(tid)

        # 2. 최대 세션 수 초과 시 가장 오래된 세션부터 제거
        with self._lock:
            remaining = dict(self._last_access)

        if len(remaining) > self.max_sessions:
            sorted_by_access = sorted(remaining.items(), key=lambda x: x[1])
            evict_count = len(remaining) - self.max_sessions
            for tid, _ in sorted_by_access[:evict_count]:
                self._evict_thread(tid)

        if expired or evict_count > 0:
            with self._lock:
                active_count = len(self._last_access)
            log_step(logger, "SYSTEM", "CHECKPOINT", "CLEANUP", "DONE", "세션 정리 완료", expired=len(expired), evicted=evict_count, active=active_count)

    def _evict_thread(self, thread_id: str) -> None:
        """특정 thread의 모든 데이터 제거"""
        try:
            # InMemorySaver.delete_thread 사용
            self.delete_thread(thread_id)
        except Exception:
            # storage에서 직접 삭제 (fallback)
            self.storage.pop(thread_id, None)

            keys_to_delete = [k for k in self.writes if k[0] == thread_id]
            for k in keys_to_delete:
                del self.writes[k]

            keys_to_delete = [k for k in self.blobs if k[0] == thread_id]
            for k in keys_to_delete:
                del self.blobs[k]

        with self._lock:
            self._last_access.pop(thread_id, None)

    def get_stats(self) -> dict:
        """현재 상태 통계 반환"""
        with self._lock:
            access_copy = dict(self._last_access)

        now = time.time()
        active = len(access_copy)
        expired = sum(1 for t in access_copy.values() if now - t > self.ttl_seconds)

        return {
            "active_sessions": active,
            "expired_pending": expired,
            "max_sessions": self.max_sessions,
            "ttl_seconds": self.ttl_seconds,
            "storage_threads": len(self.storage),
        }
