import uuid
import logging
from fastapi import APIRouter
from livekit.api import AccessToken, VideoGrants, LiveKitAPI, CreateAgentDispatchRequest
from app.config import settings
from app.schemas import TokenRequest, TokenResponse

router = APIRouter()
logger = logging.getLogger("voiceai.livekit")

AGENT_NAME = "agent-test"


@router.post("/token", response_model=TokenResponse)
async def get_livekit_token(request: TokenRequest):
    room_name = request.room_name or f"voiceai-{uuid.uuid4().hex[:8]}"
    participant_identity = request.participant_identity or f"user-{uuid.uuid4().hex[:6]}"

    token = (
        AccessToken(api_key=settings.livekit_api_key, api_secret=settings.livekit_api_secret)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            )
        )
        .with_identity(participant_identity)
        .to_jwt()
    )

    try:
        async with LiveKitAPI(
            url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        ) as lkapi:
            await lkapi.agent_dispatch.create_dispatch(
                CreateAgentDispatchRequest(
                    agent_name=AGENT_NAME,
                    room=room_name,
                )
            )
            logger.info("Dispatched agent '%s' to room '%s'", AGENT_NAME, room_name)
    except Exception as e:
        logger.warning("Agent dispatch failed (non-fatal): %s", e)

    return TokenResponse(token=token, room_name=room_name, url=settings.livekit_url)
