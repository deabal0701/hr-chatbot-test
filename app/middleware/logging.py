"""
LoggingMiddleware - HTTP 요청/응답 로깅 Middleware

Java Filter 패턴, 요청 전처리와 응답 후처리를 수행합니다.
Streaming 응답도 지원합니다.
"""

import logging
import time
import uuid
from typing import Optional

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from app.middleware.base import BaseMiddleware
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """
    HTTP 요청/응답 로깅 Middleware

    기능:
        - 요청 헤더/바디 로깅
        - 응답 헤더/바디 로깅 (Streaming 지원)
        - Request ID 자동 부여 (X-Request-ID 헤더)
        - 처리 시간 측정 (X-Process-Time 헤더)

    Usage:
        from fastapi import FastAPI
        from app.middleware.logging import LoggingMiddleware

        app = FastAPI()
        app.add_middleware(LoggingMiddleware)
    """

    # 로깅 설정
    MAX_BODY_LOG_SIZE: int = 1000  # 최대 로깅할 바디 크기 (bytes)
    LOG_REQUEST_BODY: bool = True  # 요청 바디 로깅 여부
    LOG_RESPONSE_BODY: bool = True  # 응답 바디 로깅 여부 (Streaming 포함)

    # 바디 로깅을 건너뛸 Content-Type
    SKIP_BODY_CONTENT_TYPES = {
        "multipart/form-data",
        "application/octet-stream",
        "image/",
        "video/",
        "audio/",
    }

    # 요청 시작/종료 구분 표시
    REQUEST_SEPARATOR = "=" * 60

    async def process_request(self, request: Request, call_next) -> Response:
        """
        요청/응답 로깅 처리

        Java Filter 패턴:
            // 전처리 (Before)
            chain.doFilter(request, response);  // → await call_next(request)
            // 후처리 (After)
        """
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # ===== 요청 시작 표시 =====
        logger.info(f"[{request_id}] {self.REQUEST_SEPARATOR}")
        logger.info(f"[{request_id}] >>> HTTP 요청 시작 | {request.method} {request.url.path}")
        logger.info(f"[{request_id}] {self.REQUEST_SEPARATOR}")

        # ===== 전처리 (Before Filter) =====
        await self._log_request(request, request_id)

        # request.state에 저장 (다른 코드에서 사용 가능)
        request.state.request_id = request_id
        request.state.start_time = start_time

        # ===== 실제 요청 처리 (chain.doFilter) =====
        response = await call_next(request)

        # ===== 후처리 (After Filter) =====
        process_time = time.time() - start_time

        # 응답 헤더 추가
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        # Streaming SSE 응답 여부 확인
        if self._is_streaming_response(response):
            return self._wrap_streaming_response(response, request, request_id, start_time)

        # 일반 응답: body_iterator를 소비하여 바디 읽기
        response_body_bytes = await self._consume_response_body(response)

        # DEBUG 레벨일 때 바디 로깅
        body_for_log: Optional[str] = None
        if self.LOG_RESPONSE_BODY and logger.isEnabledFor(logging.DEBUG) and response_body_bytes:
            body_for_log = response_body_bytes.decode("utf-8", errors="ignore")[:self.MAX_BODY_LOG_SIZE]

        self._log_response(request, response, request_id, process_time, body_for_log)

        # ===== 요청 종료 표시 =====
        logger.info(f"[{request_id}] {self.REQUEST_SEPARATOR}")
        logger.info(f"[{request_id}] <<< HTTP 요청 완료 | {request.method} {request.url.path} | status={response.status_code} | {process_time:.4f}s")
        logger.info(f"[{request_id}] {self.REQUEST_SEPARATOR}")

        # 새 Response 생성 (body_iterator는 한번만 읽을 수 있으므로)
        return Response(
            content=response_body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

    async def _log_request(self, request: Request, request_id: str) -> None:
        """요청 로깅"""
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        client_ip = request.client.host if request.client else "unknown"

        # 기본 요청 정보
        log_parts = [
            f"[{request_id}]",
            "[HTTP-REQ]",
            f"{method} {path}",
        ]

        if query:
            log_parts.append(f"| query={query}")

        log_parts.append(f"| client={client_ip}")

        # 주요 헤더 로깅
        headers_to_log = ["Content-Type", "Authorization", "User-Agent"]
        for header in headers_to_log:
            value = request.headers.get(header)
            if value:
                # Authorization은 마스킹
                if header == "Authorization":
                    value = self._mask_sensitive(value)
                log_parts.append(f"| {header}={value}")

        logger.info(" ".join(log_parts))

        # 요청 바디 로깅 (설정 시)
        if self.LOG_REQUEST_BODY and self._should_log_body(request.headers.get("content-type")):
            await self._log_request_body(request, request_id)

    async def _log_request_body(self, request: Request, request_id: str) -> None:
        """요청 바디 로깅"""
        try:
            body = await request.body()
            if body:
                body_str = body.decode("utf-8", errors="ignore")
                body_preview = body_str[:self.MAX_BODY_LOG_SIZE]
                truncated = "..." if len(body_str) > self.MAX_BODY_LOG_SIZE else ""
                logger.debug(f"[{request_id}] [HTTP-REQ-BODY] {body_preview}{truncated}")
        except Exception as e:
            logger.debug(f"[{request_id}] [HTTP-REQ-BODY] Failed to read body: {e}")

    def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        process_time: float,
        response_body: Optional[str] = None
    ) -> None:
        """응답 로깅"""
        method = request.method
        path = request.url.path
        status_code = response.status_code
        content_type = response.headers.get("content-type", "")

        # 기본 응답 정보
        log_parts = [
            f"[{request_id}]",
            "[HTTP-RES]",
            f"{method} {path}",
            f"| status={status_code}",
            f"| time={process_time:.4f}s",
        ]

        if content_type:
            log_parts.append(f"| content-type={content_type}")

        logger.info(" ".join(log_parts))

        # 응답 바디 로깅 (DEBUG 레벨일 때)
        if self.LOG_RESPONSE_BODY and response_body:
            body_preview = response_body[:self.MAX_BODY_LOG_SIZE]
            truncated = "..." if len(response_body) > self.MAX_BODY_LOG_SIZE else ""
            logger.debug(f"[{request_id}] [HTTP-RES-BODY] {body_preview}{truncated}")

    def _is_streaming_response(self, response: Response) -> bool:
        """Streaming 응답 여부 확인"""
        content_type = response.headers.get("content-type", "")
        return (
            isinstance(response, StreamingResponse) or
            "text/event-stream" in content_type or
            "application/x-ndjson" in content_type
        )

    def _wrap_streaming_response(
        self,
        response: StreamingResponse,
        request: Request,
        request_id: str,
        start_time: float
    ) -> StreamingResponse:
        """
        Streaming 응답을 감싸서 로깅 추가

        Streaming을 유지하면서 완료 시점에 로깅합니다.
        바디 내용도 최대 MAX_BODY_LOG_SIZE까지 수집하여 로깅합니다.
        """
        original_iterator = response.body_iterator
        max_collect = self.MAX_BODY_LOG_SIZE

        async def logging_iterator():
            collected = b""
            chunk_count = 0
            total_bytes = 0

            try:
                async for chunk in original_iterator:
                    chunk_count += 1
                    chunk_bytes = chunk if isinstance(chunk, bytes) else chunk.encode("utf-8")
                    total_bytes += len(chunk_bytes)

                    # 최대치까지만 수집 (메모리 보호)
                    if self.LOG_RESPONSE_BODY and len(collected) < max_collect:
                        collected += chunk_bytes[:max_collect - len(collected)]

                    yield chunk  # Streaming 유지!

            finally:
                # Streaming 완료 후 로깅
                total_time = time.time() - start_time
                body_preview = collected.decode("utf-8", errors="ignore") if collected else ""
                truncated = "..." if total_bytes > max_collect else ""

                log_parts = [
                    f"[{request_id}]",
                    "[HTTP-RES-STREAM]",
                    f"{request.method} {request.url.path}",
                    f"| status={response.status_code}",
                    f"| chunks={chunk_count}",
                    f"| bytes={total_bytes}",
                    f"| time={total_time:.4f}s",
                ]
                logger.info(" ".join(log_parts))

                # 바디 미리보기 (DEBUG 레벨)
                if body_preview:
                    logger.debug(f"[{request_id}] [HTTP-RES-STREAM-BODY] {body_preview}{truncated}")

                # ===== 요청 종료 표시 (Streaming) =====
                separator = "=" * 60
                logger.info(f"[{request_id}] {separator}")
                logger.info(f"[{request_id}] <<< HTTP 요청 완료 (Stream) | {request.method} {request.url.path} | status={response.status_code} | {total_time:.4f}s")
                logger.info(f"[{request_id}] {separator}")

        return StreamingResponse(
            content=logging_iterator(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

    def _should_log_body(self, content_type: Optional[str]) -> bool:
        """바디 로깅 여부 결정"""
        if not content_type:
            return True

        content_type_lower = content_type.lower()
        for skip_type in self.SKIP_BODY_CONTENT_TYPES:
            if skip_type in content_type_lower:
                return False

        return True

    async def _consume_response_body(self, response: StreamingResponse) -> bytes:
        """응답 body_iterator를 소비하여 바디 읽기"""
        body = b""
        try:
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")
                body += chunk
        except Exception as e:
            logger.debug(f"[HTTP] Failed to read response body: {e}")
        return body

    def _mask_sensitive(self, value: str, visible_chars: int = 10) -> str:
        """민감 정보 마스킹"""
        if len(value) <= visible_chars:
            return "*" * len(value)
        return value[:visible_chars] + "..." + "*" * 10
