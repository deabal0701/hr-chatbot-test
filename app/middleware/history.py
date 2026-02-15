"""
HistoryMiddleware - API 요청 이력 저장 Middleware

요청/응답을 파싱하여 히스토리 DB에 저장합니다.
"""
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from starlette.requests import Request
from starlette.responses import Response, StreamingResponse

from app.middleware.base import BaseMiddleware
from app.api.services.history_service import history_service
from app.core.security.jwt import verify_token
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class HistoryMiddleware(BaseMiddleware):
    """
    API 요청 이력 저장 Middleware

    기능:
        - Agent, NL2SQL, RAG 요청 자동 감지
        - 요청/응답 JSON 파싱하여 이력 저장
        - 비동기 백그라운드 저장 (논블로킹)

    Usage:
        app.add_middleware(HistoryMiddleware)
    """

    # 이력을 저장할 엔드포인트 패턴
    HISTORY_ENDPOINTS = {
        "/api/v1/agent/search": "agent",
        "/api/v1/agent/search/stream": "agent",
        "/api/v1/search": "auto",  # RAG 또는 NL2SQL (응답에서 판단)
        "/api/v1/search/stream": "nl2sql",
    }

    # 제외할 경로 (BaseMiddleware 기본값 + 추가)
    EXCLUDE_PATHS = {
        "/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico",
        "/api/v1/history",  # 이력 조회 API는 제외
    }

    EXCLUDE_PREFIXES = {
        "/api/v1/history/",  # 이력 관련 모든 API 제외
        "/api/admin/",       # Admin API 제외
    }

    async def process_request(self, request: Request, call_next) -> Response:
        """요청/응답 처리 및 이력 저장"""
        path = request.url.path
        method = request.method

        # POST 요청이 아니거나 이력 대상이 아니면 패스
        if method != "POST" or not self._is_history_target(path):
            return await call_next(request)

        start_time = time.time()
        requested_at = datetime.now()  # 요청 시작 시간
        request_id = getattr(request.state, "request_id", "unknown")

        # 요청 바디 읽기
        request_data = await self._parse_request_body(request)
        question = request_data.get("question") or request_data.get("query", "")
        session_id_from_request = request_data.get("session_id")

        # 클라이언트 정보
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # 멀티테넌트/사용자 정보 (JWT 토큰에서 추출)
        tenant_id, user_id, user_name = self._extract_user_from_token(request)

        # 실제 요청 처리
        response = await call_next(request)

        # SSE Streaming 응답: 래핑하여 complete 이벤트에서 이력 저장
        if self._is_streaming_response(response):
            return self._wrap_streaming_response(
                response=response,
                path=path,
                request_id=request_id,
                question=question,
                session_id_from_request=session_id_from_request,
                start_time=start_time,
                requested_at=requested_at,
                tenant_id=tenant_id,
                user_id=user_id,
                user_name=user_name,
                client_ip=client_ip,
                user_agent=user_agent,
            )

        # 응답 바디 읽기
        response_body_bytes = await self._consume_response_body(response)
        response_time_ms = int((time.time() - start_time) * 1000)

        # 응답 파싱 및 이력 저장 (비동기, 논블로킹)
        completed_at = datetime.now()  # 요청 완료 시간
        try:
            self._save_history(
                path=path,
                request_id=request_id,
                question=question,
                session_id_from_request=session_id_from_request,
                response_body=response_body_bytes,
                response_code=response.status_code,
                response_time_ms=response_time_ms,
                tenant_id=tenant_id,
                user_id=user_id,
                user_name=user_name,
                client_ip=client_ip,
                user_agent=user_agent,
                requested_at=requested_at,
                completed_at=completed_at,
            )
        except Exception as e:
            logger.error(f"[{request_id}] [HISTORY] Failed to save history: {e}")

        # 새 Response 생성 (body_iterator는 한번만 읽을 수 있으므로)
        return Response(
            content=response_body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type
        )

    def _extract_user_from_token(self, request: Request) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Authorization 헤더의 JWT 토큰에서 사용자 정보 추출 (tenant_id, user_id, user_name)"""
        try:
            auth_header = request.headers.get("authorization", "")
            if not auth_header.startswith("Bearer "):
                return None, None, None
            token = auth_header[7:]
            payload = verify_token(token)
            return str(payload.tenant_id) if payload.tenant_id else None, payload.sub, payload.display_name
        except Exception:
            return None, None, None

    def _is_history_target(self, path: str) -> bool:
        """이력 저장 대상 엔드포인트인지 확인"""
        return path in self.HISTORY_ENDPOINTS

    def _is_streaming_response(self, response: Response) -> bool:
        """Streaming 응답 여부 확인"""
        content_type = response.headers.get("content-type", "")
        return (
            isinstance(response, StreamingResponse) or
            "text/event-stream" in content_type or
            "application/x-ndjson" in content_type
        )

    async def _parse_request_body(self, request: Request) -> Dict[str, Any]:
        """요청 바디 JSON 파싱"""
        try:
            body = await request.body()
            if body:
                return json.loads(body.decode("utf-8"))
        except Exception as e:
            logger.debug(f"[HISTORY] Failed to parse request body: {e}")
        return {}

    async def _consume_response_body(self, response: StreamingResponse) -> bytes:
        """응답 body_iterator를 소비하여 바디 읽기"""
        body = b""
        try:
            async for chunk in response.body_iterator:
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")
                body += chunk
        except Exception as e:
            logger.debug(f"[HISTORY] Failed to read response body: {e}")
        return body

    def _save_history(
        self,
        path: str,
        request_id: str,
        question: str,
        session_id_from_request: Optional[str],
        response_body: bytes,
        response_code: int,
        response_time_ms: int,
        tenant_id: Optional[str],
        user_id: Optional[str],
        user_name: Optional[str],
        client_ip: Optional[str],
        user_agent: Optional[str],
        requested_at: datetime,
        completed_at: datetime,
    ) -> None:
        """응답 파싱 및 이력 저장"""
        # 응답 JSON 파싱
        response_data = {}
        try:
            if response_body:
                response_data = json.loads(response_body.decode("utf-8"))
        except Exception as e:
            logger.debug(f"[{request_id}] [HISTORY] Failed to parse response: {e}")

        # success 여부 판단
        success = response_data.get("success", response_code == 200)
        data = response_data.get("data", {}) or {}
        error_info = response_data.get("error", {}) or {}
        error_message = error_info.get("message") if not success else None

        # request_type 결정
        request_type = self._determine_request_type(path, data)

        # 응답 데이터에서 공통 필드 추출
        answer = data.get("answer", "")
        session_id = data.get("session_id") or session_id_from_request

        # 타입별 저장
        if request_type == "agent":
            self._save_agent_history(
                request_id, question, answer, data, session_id,
                response_code, response_time_ms, success, error_message,
                tenant_id, user_id, user_name, client_ip,
                requested_at, completed_at
            )
        elif request_type == "nl2sql":
            self._save_nl2sql_history(
                request_id, question, answer, data, session_id,
                response_code, response_time_ms, success, error_message,
                tenant_id, user_id, user_name, client_ip,
                requested_at, completed_at
            )
        elif request_type == "rag":
            self._save_rag_history(
                request_id, question, answer, data,
                response_code, response_time_ms, success, error_message,
                tenant_id, user_id, user_name, client_ip,
                requested_at, completed_at
            )

    def _determine_request_type(self, path: str, data: Dict) -> str:
        """request_type 결정"""
        endpoint_type = self.HISTORY_ENDPOINTS.get(path, "unknown")

        if endpoint_type == "agent":
            return "agent"
        elif endpoint_type == "auto":
            # /api/v1/search의 경우 응답의 query_type으로 판단
            query_type = data.get("query_type", "")
            if query_type == "nl2sql":
                return "nl2sql"
            elif query_type == "rag":
                return "rag"
            # query_type이 없으면 sql 필드 유무로 판단
            if data.get("sql"):
                return "nl2sql"
            return "rag"
        return "unknown"

    def _save_agent_history(
        self,
        request_id: str,
        question: str,
        answer: str,
        data: Dict,
        session_id: Optional[str],
        response_code: int,
        response_time_ms: int,
        success: bool,
        error_message: Optional[str],
        tenant_id: Optional[str],
        user_id: Optional[str],
        user_name: Optional[str],
        client_ip: Optional[str],
        requested_at: datetime,
        completed_at: datetime,
    ) -> None:
        """Agent 이력 저장"""
        steps = data.get("steps", [])
        tools_used = data.get("tools_used", [])
        iteration_count = data.get("total_iterations", 0)
        metadata = data.get("metadata", {})

        history_service.save_agent_request(
            request_id=request_id,
            question=question,
            answer=answer,
            steps=steps,
            tools_used=tools_used,
            iteration_count=iteration_count,
            response_time_ms=response_time_ms,
            session_id=session_id,
            success=success,
            error_message=error_message,
            metadata=metadata,
            tenant_id=tenant_id,
            user_id=user_id,
            user_name=user_name,
            client_ip=client_ip,
            requested_at=requested_at,
            completed_at=completed_at,
        )

    def _save_nl2sql_history(
        self,
        request_id: str,
        question: str,
        answer: str,
        data: Dict,
        session_id: Optional[str],
        response_code: int,
        response_time_ms: int,
        success: bool,
        error_message: Optional[str],
        tenant_id: Optional[str],
        user_id: Optional[str],
        user_name: Optional[str],
        client_ip: Optional[str],
        requested_at: datetime,
        completed_at: datetime,
    ) -> None:
        """NL2SQL 이력 저장"""
        sql = data.get("sql", "")
        sql_result = data.get("sql_result")
        metadata = data.get("metadata", {})
        current_turn = metadata.get("current_turn", 1) if metadata else 1

        history_service.save_nl2sql_request(
            request_id=request_id,
            question=question,
            answer=answer,
            sql=sql,
            sql_result=sql_result,
            current_turn=current_turn,
            response_time_ms=response_time_ms,
            session_id=session_id,
            success=success,
            error_message=error_message,
            metadata=metadata,
            tenant_id=tenant_id,
            user_id=user_id,
            user_name=user_name,
            client_ip=client_ip,
            requested_at=requested_at,
            completed_at=completed_at,
        )

    def _save_rag_history(
        self,
        request_id: str,
        question: str,
        answer: str,
        data: Dict,
        response_code: int,
        response_time_ms: int,
        success: bool,
        error_message: Optional[str],
        tenant_id: Optional[str],
        user_id: Optional[str],
        user_name: Optional[str],
        client_ip: Optional[str],
        requested_at: datetime,
        completed_at: datetime,
    ) -> None:
        """RAG 이력 저장"""
        sources = data.get("sources", [])

        history_service.save_rag_request(
            request_id=request_id,
            question=question,
            answer=answer,
            sources=sources,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message,
            tenant_id=tenant_id,
            user_id=user_id,
            user_name=user_name,
            client_ip=client_ip,
            requested_at=requested_at,
            completed_at=completed_at,
        )

    # =========================================================================
    # SSE Streaming 이력 저장
    # =========================================================================

    def _wrap_streaming_response(
        self,
        response: StreamingResponse,
        path: str,
        request_id: str,
        question: str,
        session_id_from_request: Optional[str],
        start_time: float,
        requested_at: datetime,
        tenant_id: Optional[str],
        user_id: Optional[str],
        user_name: Optional[str],
        client_ip: Optional[str],
        user_agent: Optional[str],  # noqa: ARG002 - 향후 확장용
    ) -> StreamingResponse:
        """SSE 스트리밍 응답을 래핑하여 complete 이벤트에서 이력 저장

        원본 SSE 청크를 클라이언트에 그대로 전달하면서,
        complete/error 이벤트를 캡처하여 스트림 종료 후 이력을 저장합니다.
        """
        original_body_iterator = response.body_iterator
        middleware = self

        async def wrapped_iterator():
            complete_data = None
            error_data = None

            async for chunk in original_body_iterator:
                yield chunk

                # SSE 이벤트 파싱 (complete/error 캡처)
                chunk_str = chunk.decode("utf-8") if isinstance(chunk, bytes) else str(chunk)
                event_type, event_data = middleware._parse_sse_event(chunk_str)

                if event_type == "complete":
                    complete_data = event_data
                elif event_type == "error":
                    error_data = event_data

            # 스트림 종료 후 이력 저장
            completed_at = datetime.now()
            response_time_ms = int((time.time() - start_time) * 1000)

            try:
                if complete_data:
                    middleware._save_stream_history(
                        path=path, request_id=request_id, question=question,
                        session_id_from_request=session_id_from_request,
                        response_data=complete_data.get("data", {}),
                        response_time_ms=response_time_ms, success=True, error_message=None,
                        tenant_id=tenant_id, user_id=user_id, user_name=user_name,
                        client_ip=client_ip, requested_at=requested_at, completed_at=completed_at,
                    )
                elif error_data:
                    middleware._save_stream_history(
                        path=path, request_id=request_id, question=question,
                        session_id_from_request=session_id_from_request,
                        response_data={},
                        response_time_ms=response_time_ms, success=False,
                        error_message=error_data.get("message", "SSE stream error"),
                        tenant_id=tenant_id, user_id=user_id, user_name=user_name,
                        client_ip=client_ip, requested_at=requested_at, completed_at=completed_at,
                    )
            except Exception as e:
                logger.error(f"[{request_id}] [HISTORY] SSE 이력 저장 실패: {e}")

        return StreamingResponse(
            wrapped_iterator(),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )

    def _parse_sse_event(self, chunk: str) -> Tuple[Optional[str], Optional[Dict]]:
        """SSE 이벤트 파싱 (event type과 data 추출)

        SSE 형식: "event: {type}\\ndata: {json}\\n\\n"
        complete/error 이벤트만 캡처하여 반환합니다.
        """
        event_type = None
        event_data = None

        for line in chunk.strip().split("\n"):
            if line.startswith("event: "):
                event_type = line[7:].strip()
            elif line.startswith("data: "):
                try:
                    event_data = json.loads(line[6:])
                except json.JSONDecodeError:
                    pass

        # complete/error 이벤트만 반환 (node_start, node_complete는 무시)
        if event_type not in ("complete", "error"):
            return None, None

        return event_type, event_data

    def _save_stream_history(
        self,
        path: str,
        request_id: str,
        question: str,
        session_id_from_request: Optional[str],
        response_data: Dict[str, Any],
        response_time_ms: int,
        success: bool,
        error_message: Optional[str],
        tenant_id: Optional[str],
        user_id: Optional[str],
        user_name: Optional[str],
        client_ip: Optional[str],
        requested_at: datetime,
        completed_at: datetime,
    ) -> None:
        """SSE 스트림 complete 이벤트 데이터로 이력 저장"""
        request_type = self.HISTORY_ENDPOINTS.get(path, "unknown")

        answer = response_data.get("answer", "")
        session_id = response_data.get("session_id") or session_id_from_request

        if request_type == "agent":
            self._save_agent_history(
                request_id, question, answer, response_data, session_id,
                200 if success else 500, response_time_ms, success, error_message,
                tenant_id, user_id, user_name, client_ip, requested_at, completed_at,
            )
        elif request_type == "nl2sql":
            self._save_nl2sql_history(
                request_id, question, answer, response_data, session_id,
                200 if success else 500, response_time_ms, success, error_message,
                tenant_id, user_id, user_name, client_ip, requested_at, completed_at,
            )
        else:
            logger.warning(f"[{request_id}] [HISTORY] SSE 이력 저장: 알 수 없는 request_type={request_type}")
