"""LOT08.2-B: opt-in local-only ASGI HTTP + authenticated SSE transport.

No process launches, listening socket, installer, remote deployment, device
identity or clinical model import. The caller must provide an initialized
AuthorizedLocalQueue with separate, protected local SQLite files.

This transport uses ONLY an Authorization Bearer header. Do not put credentials
in URLs, cookies, EventSource query strings, SSE frames or application logs.
Browser SSE clients should use fetch streaming with Authorization, not native
EventSource (which cannot supply a custom Authorization header).
"""
from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from dataclasses import asdict
from ipaddress import ip_address
import json
import re

import anyio
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from starlette.concurrency import run_in_threadpool
from starlette.middleware.trustedhost import TrustedHostMiddleware

from queue_core.domain import QueueDomainError
from queue_core.security.rbac import AuthorizationError
from queue_core.service.authorized_queue import (
    AuthorizedLocalQueue, HumanCommand, QueueEventView,
)


class HumanCommandBody(BaseModel):
    """No client-supplied tenant, actor, principal or authorization flag."""

    model_config = ConfigDict(extra="forbid")
    command: HumanCommand
    expected_version: StrictInt = Field(ge=0)
    resource_id: str | None = Field(default=None, min_length=1, max_length=128)
    reason_code: str | None = Field(default=None, min_length=1, max_length=64)


def _token(request: Request) -> str:
    # Explicitly reject URL credentials even if a valid header is present.
    if any(
        key.lower() in {"token", "access_token", "authorization"}
        for key in request.query_params
    ):
        raise AuthorizationError("AUTH_REQUIRED", 401)
    header = request.headers.get("authorization")
    if not isinstance(header, str):
        raise AuthorizationError("AUTH_REQUIRED", 401)
    scheme, separator, token = header.partition(" ")
    if (
        not separator or scheme.lower() != "bearer"
        or re.fullmatch(r"[A-Za-z0-9_-]{30,256}", token) is None
    ):
        raise AuthorizationError("AUTH_REQUIRED", 401)
    return token


def _frame(event: QueueEventView) -> str:
    """One bounded, safe SSE message; contains no names, token or clinical data."""
    if re.fullmatch(r"[0-9a-f]{32}", event.id) is None:
        # An invalid persisted ID must not inject another SSE field/line.
        raise AuthorizationError("AUTHZ_DENIED", 403)
    payload = {
        "visit_ref": event.visit_ref,
        "type": event.event_type,
        "version": event.aggregate_version,
        "occurred_at_utc": event.occurred_at_utc.isoformat(),
    }
    return (
        f"id: {event.id}\n"
        "event: queue\n"
        "data: " + json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n\n"
    )


async def authenticated_event_frames(
    service: AuthorizedLocalQueue,
    token: str,
    queue_id: str,
    *,
    after_event_id: str | None = None,
    poll_interval: float = 0.5,
    max_frames: int | None = None,
    is_disconnected: Callable[[], object] | None = None,
) -> AsyncIterator[str]:
    """Polling-to-SSE adapter with live RBAC recheck immediately per frame.

    The endpoint validates session/queue/cursor *before* opening the SSE
    response. Every polled page independently authenticates via the isolated
    Queue Core adapter. Every individual event and heartbeat has a second live
    database-backed authorization check. On revoke/disable the stream ends
    without sending a new event. No positive auth decisions are cached.

    max_frames is a local factory/test bound, never a user query parameter.
    """
    if max_frames is not None and (type(max_frames) is not int or max_frames < 1):
        raise ValueError("MAX_FRAMES_INVALID")
    if not 0.01 <= poll_interval <= 30:
        raise ValueError("POLL_INTERVAL_INVALID")
    cursor = after_event_id
    sent = 0
    while True:
        if is_disconnected is not None and await is_disconnected():
            return
        try:
            events = await run_in_threadpool(
                service.replay_events, token, queue_id,
                after_event_id=cursor, limit=100,
            )
            if not events:
                # Revalidate even for empty-stream heartbeats.
                await run_in_threadpool(service.require_queue_read, token, queue_id)
                yield ": keepalive\n\n"
            else:
                for event in events:
                    if is_disconnected is not None and await is_disconnected():
                        return
                    # Critical: a token may be revoked after obtaining the
                    # page, and before individual frames are sent.
                    await run_in_threadpool(service.require_queue_read, token, queue_id)
                    yield _frame(event)
                    cursor = event.id
                    sent += 1
                    if max_frames is not None and sent >= max_frames:
                        return
        except AuthorizationError:
            # A stream's 200 headers may already be sent; do not append a
            # stale event, error body or secret after revocation.
            return
        await anyio.sleep(poll_interval)


def create_local_queue_app(
    service: AuthorizedLocalQueue,
    *,
    poll_interval: float = 0.5,
    lab_allow_testclient: bool = False,
    lab_max_sse_frames: int | None = None,
) -> FastAPI:
    """Build an ASGI app WITHOUT binding a socket or starting an HTTP server.

    Only loopback peer addresses and loopback Host are accepted, including
    for authenticated tokens. For synthetic TestClient requests only,
    lab_allow_testclient permits the special 'testclient' peer/Host.
    """
    if not isinstance(service, AuthorizedLocalQueue):
        raise TypeError("AUTHORIZED_LOCAL_QUEUE_REQUIRED")
    if not 0.01 <= poll_interval <= 30:
        raise ValueError("POLL_INTERVAL_INVALID")
    if lab_max_sse_frames is not None and (
        type(lab_max_sse_frames) is not int or lab_max_sse_frames < 1
    ):
        raise ValueError("LAB_MAX_FRAMES_INVALID")
    app = FastAPI(
        debug=False, docs_url=None, redoc_url=None, openapi_url=None,
        title="Digital Crown Queue Core Local-Only ASGI",
    )
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=(
            ["localhost", "127.0.0.1", "[::1]", "testserver"]
            if lab_allow_testclient else
            ["localhost", "127.0.0.1", "[::1]"]
        ),
    )

    @app.middleware("http")
    async def local_only(request: Request, call_next):
        peer = request.client.host if request.client else ""
        try:
            loopback = ip_address(peer).is_loopback
        except ValueError:
            loopback = lab_allow_testclient and peer == "testclient"
        if not loopback:
            response = JSONResponse({"code": "LOCAL_ONLY"}, status_code=403)
        elif request.url.path.startswith("/v1/"):
            # Gate authentication BEFORE body parsing/validation so a guest
            # cannot elicit 422 or probe command schemas. The service still
            # resolves rights again inside the locked queue transaction.
            try:
                token = _token(request)
                principal = await run_in_threadpool(
                    service._operators.resolve_session, token,
                )
                if principal is None:
                    raise AuthorizationError("AUTH_REQUIRED", 401)
            except Exception:
                response = JSONResponse(
                    {"code": "AUTH_REQUIRED"}, status_code=401,
                )
            else:
                response = await call_next(request)
        else:
            response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    @app.exception_handler(AuthorizationError)
    async def denied(_request: Request, error: AuthorizationError):
        return JSONResponse(
            {"code": error.code}, status_code=error.status_code,
        )

    @app.exception_handler(QueueDomainError)
    async def domain_error(_request: Request, error: QueueDomainError):
        code = error.code
        status = 409 if code.endswith(("_CONFLICT", "_STALE")) else 400
        return JSONResponse({"code": code}, status_code=status)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(_request: Request, _error: RequestValidationError):
        # FastAPI validation detail often includes input values; do not echo
        # tokens, unexpected patient fields or contents in public errors.
        return JSONResponse({"code": "INVALID_REQUEST"}, status_code=422)

    @app.post("/v1/visits/{visit_id}/commands")
    async def human_command(visit_id: str, body: HumanCommandBody, request: Request):
        token = _token(request)
        result = await run_in_threadpool(
            service.perform,
            token, body.command, visit_id,
            expected_version=body.expected_version,
            resource_id=body.resource_id,
            reason_code=body.reason_code,
        )
        return asdict(result)

    @app.get("/v1/queues/{queue_id}/snapshot")
    async def queue_snapshot(queue_id: str, request: Request):
        token = _token(request)
        rows = await run_in_threadpool(service.queue_snapshot, token, queue_id)
        return {"visits": [asdict(row) for row in rows]}

    @app.get("/v1/queues/{queue_id}/events")
    async def queue_events(
        queue_id: str, request: Request,
        after_event_id: str | None = Query(default=None, max_length=128),
        limit: int = Query(default=100, ge=1, le=100),
    ):
        token = _token(request)
        rows = await run_in_threadpool(
            service.replay_events, token, queue_id,
            after_event_id=after_event_id, limit=limit,
        )
        return {"events": [asdict(row) for row in rows]}

    @app.get("/v1/queues/{queue_id}/stream")
    async def queue_stream(queue_id: str, request: Request):
        token = _token(request)
        cursor = request.headers.get("last-event-id")
        if cursor is not None and (not cursor or len(cursor) > 128):
            raise AuthorizationError("AUTHZ_DENIED", 403)
        # Authenticate, authorize queue access and validate replay cursor
        # BEFORE returning 200/text-event-stream.
        await run_in_threadpool(
            service.replay_events, token, queue_id,
            after_event_id=cursor, limit=1,
        )
        return StreamingResponse(
            authenticated_event_frames(
                service, token, queue_id, after_event_id=cursor,
                poll_interval=poll_interval,
                max_frames=lab_max_sse_frames,
                is_disconnected=request.is_disconnected,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate",
                "X-Accel-Buffering": "no",
            },
        )

    return app
