"""Live caption WebSocket (PRD Ch9.6 "Live Transcript", Ch9.24 security rules).

    ws /api/v1/consultations/{id}/live

The doctor's browser streams 16 kHz mono 16-bit PCM frames up and receives
`{"type": "caption", ...}` JSON messages back. The API only relays: audio goes
onto a Redis list consumed by `app/workers/live_worker.py`, captions come back
over Redis pub/sub — the API process never runs speech recognition.

Security (same bar as the HTTP API, plus WebSocket-specific checks):
* the access-token cookie is fully validated (session, user, hospital, role);
* `Origin` must be one of the configured frontend origins (blocks cross-site
  WebSocket hijacking, which CORS does not cover);
* only the assigned doctor, only for their own in-progress consultation;
* the session is re-checked every minute so a revoked session or deactivated
  account is cut off promptly, even though the socket outlives the 15-minute
  access token;
* frame size is capped and malformed frames are ignored.
"""

import asyncio
import contextlib
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.exceptions import AppError
from app.core.live_audio import MAX_FRAME_BYTES, MAX_QUEUED_FRAMES, caption_channel, encode_frame, valid_pcm
from app.core.logging import logger
from app.core.redis import get_redis_bytes, resolve
from app.dependencies.auth import authenticate_access_token
from app.models.enums import ConsultationStatus, RoleName, UserStatus
from app.repositories.consultation_repository import ConsultationRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository

router = APIRouter(tags=["live"])

WS_UNAUTHENTICATED = 4401
WS_FORBIDDEN = 4403
WS_NOT_FOUND = 4404
SESSION_RECHECK_SECONDS = 60


async def _session_still_valid(session_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    async with AsyncSessionLocal() as db:
        session = await SessionRepository(db).get_by_id(session_id)
        if session is None or session.expires_at <= datetime.now(timezone.utc):
            return False
        user = await UserRepository(db).get_by_id(user_id)
        return user is not None and user.status == UserStatus.active


@router.websocket("/consultations/{consultation_id}/live")
async def live_captions(websocket: WebSocket, consultation_id: uuid.UUID) -> None:
    origin = websocket.headers.get("origin")
    if origin is not None and origin not in settings.cors_origins_list:
        await websocket.close(code=WS_FORBIDDEN)
        return

    async with AsyncSessionLocal() as db:
        try:
            current = await authenticate_access_token(db, websocket.cookies.get(settings.access_token_cookie_name))
        except AppError:
            await websocket.close(code=WS_UNAUTHENTICATED)
            return
        if current.role != RoleName.doctor:
            await websocket.close(code=WS_FORBIDDEN)
            return
        consultation = await ConsultationRepository(db).get_by_id(consultation_id, hospital_id=current.hospital)
        if (
            consultation is None
            or consultation.doctor_id != current.user.id
            or consultation.status != ConsultationStatus.in_progress
        ):
            await websocket.close(code=WS_NOT_FOUND)
            return
        session_id, user_id = current.session_id, current.user.id

    await websocket.accept()
    redis = get_redis_bytes()
    pubsub = redis.pubsub()
    await pubsub.subscribe(caption_channel(consultation_id))

    async def receive_audio() -> None:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return
            data = message.get("bytes")
            if data is None:
                if message.get("text") == "end":
                    return
                continue
            if len(data) > MAX_FRAME_BYTES or not valid_pcm(data):
                continue  # ignore malformed frames rather than dropping the whole session
            await resolve(redis.lpush(settings.live_audio_key, encode_frame(consultation_id, data)))
            await resolve(redis.ltrim(settings.live_audio_key, 0, MAX_QUEUED_FRAMES - 1))  # keep the newest audio

    async def send_captions() -> None:
        async for item in pubsub.listen():
            if item["type"] == "message":
                await websocket.send_text(item["data"].decode())

    async def watch_session() -> None:
        while True:
            await asyncio.sleep(SESSION_RECHECK_SECONDS)
            if not await _session_still_valid(session_id, user_id):
                await websocket.close(code=WS_UNAUTHENTICATED)
                return

    tasks = [asyncio.create_task(fn()) for fn in (receive_audio, send_captions, watch_session)]
    try:
        # Whichever finishes first (client left / session revoked / socket error) ends the stream.
        await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    except WebSocketDisconnect:
        pass
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)  # reap them so nothing is left unretrieved
        with contextlib.suppress(Exception):
            # Tell the worker to caption whatever audio is left, then forget this consultation.
            await resolve(redis.lpush(settings.live_audio_key, encode_frame(consultation_id, b"")))
            await pubsub.unsubscribe()
            await pubsub.aclose()
        with contextlib.suppress(Exception):
            await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
        logger.info("Live captions closed for consultation %s", consultation_id)
