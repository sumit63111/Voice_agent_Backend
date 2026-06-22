from dotenv import load_dotenv
load_dotenv()

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from livekit import rtc
from livekit.agents import Agent, AgentSession, JobContext, RoomInputOptions, WorkerOptions, cli, function_tool
from livekit.plugins import deepgram, elevenlabs, groq
from livekit.plugins.tavus import AvatarSession

from agent.prompt import SYSTEM_PROMPT
from agent.safeguard import is_safe, REDIRECT_MESSAGE
from app.config import settings

from tools.identify_user import handle_identify_user
from tools.fetch_slots import handle_fetch_slots
from tools.book_appointment import handle_book_appointment
from tools.retrieve_appointments import handle_retrieve_appointments
from tools.cancel_appointment import handle_cancel_appointment
from tools.modify_appointment import handle_modify_appointment
from tools.end_conversation import handle_end_conversation

logger = logging.getLogger("voiceai.agent")


class VoiceAgent(Agent):
    def __init__(self, room: rtc.Room):
        super().__init__(instructions=SYSTEM_PROMPT)
        self._room = room
        self._session_data: dict = {}

    async def _publish(self, payload: dict):
        try:
            await self._room.local_participant.publish_data(
                json.dumps(payload).encode(), reliable=True
            )
        except Exception as e:
            logger.warning(f"Data publish failed: {e}")

    async def on_user_turn_completed(self, ctx, new_message):
        text = new_message.text_content or ""
        if text and not await is_safe(text):
            logger.info("Safeguard triggered for input: %s", text[:80])
            return REDIRECT_MESSAGE
        return await super().on_user_turn_completed(ctx, new_message)

    @asynccontextmanager
    async def _tool_call(self, tool: str):
        await self._publish({"type": "tool_call", "tool": tool, "status": "running"})
        try:
            yield
        except Exception:
            logger.exception("Tool %s failed", tool)
            await self._publish({
                "type": "tool_call",
                "tool": tool,
                "status": "error",
                "message": "Sorry, something went wrong on my end.",
            })
            raise

    async def _emit(self, tool: str, result: dict, status: str | None = None):
        await self._publish({
            "type": "tool_call",
            "tool": tool,
            "status": status or result.get("status", "done"),
            "message": result.get("message", ""),
            **{k: v for k, v in result.items() if k not in ("status", "message")},
        })

    @function_tool
    async def identify_user(self, phone_number: str) -> str:
        async with self._tool_call("identify_user"):
            result = await handle_identify_user(phone_number)
            if not result.get("error"):
                self._session_data["user_id"] = result.get("user_id")
                self._session_data["phone_number"] = result.get("phone_number")
            await self._emit("identify_user", result, "error" if result.get("error") else "done")
            return result["message"]

    @function_tool
    async def fetch_slots(self, date: str) -> str:
        async with self._tool_call("fetch_slots"):
            result = await handle_fetch_slots(date)
            await self._emit("fetch_slots", result, "done")
            return result["message"]

    @function_tool
    async def book_appointment(self, date: str, time: str, reason: str = "General consultation") -> str:
        async with self._tool_call("book_appointment"):
            user_id = self._session_data.get("user_id")
            result = await handle_book_appointment(user_id, date, time, reason)
            await self._emit("book_appointment", result)
            return result["message"]

    @function_tool
    async def retrieve_appointments(self) -> str:
        async with self._tool_call("retrieve_appointments"):
            user_id = self._session_data.get("user_id")
            result = await handle_retrieve_appointments(user_id)
            await self._emit("retrieve_appointments", result, "done")
            return result["message"]

    @function_tool
    async def cancel_appointment(self, appointment_id: str) -> str:
        async with self._tool_call("cancel_appointment"):
            result = await handle_cancel_appointment(appointment_id)
            await self._emit("cancel_appointment", result)
            return result["message"]

    @function_tool
    async def modify_appointment(self, appointment_id: str, new_date: str = "", new_time: str = "") -> str:
        async with self._tool_call("modify_appointment"):
            result = await handle_modify_appointment(appointment_id, new_date or None, new_time or None)
            await self._emit("modify_appointment", result)
            return result["message"]

    @function_tool
    async def end_conversation(self) -> str:
        async with self._tool_call("end_conversation"):
            result = await handle_end_conversation(
                room=self._room,
                session_data=self._session_data,
            )
            await self._publish({
                "type": "tool_call",
                "tool": "end_conversation",
                "status": "done",
                "message": "Call ended.",
            })
            await self._publish({
                "type": "call_ended",
                "summary": result.get("summary", ""),
                "appointments": result.get("appointments", []),
                "timestamp": datetime.utcnow().isoformat(),
            })
            return result["message"]


async def entrypoint(ctx: JobContext):
    await ctx.connect()
    logger.info("Agent connected to room: %s", ctx.room.name)

    agent = VoiceAgent(room=ctx.room)

    session = AgentSession(
        stt=deepgram.STT(model="nova-3-general", language="multi"),
        llm=groq.LLM(model="llama-3.3-70b-versatile"),
        tts=elevenlabs.TTS(
            api_key=settings.elevenlabs_api_key,
            voice_id=settings.elevenlabs_voice_id,
            model=settings.elevenlabs_model,
        ),
    )

    if settings.tavus_api_key and settings.tavus_replica_id:
        try:
            avatar = AvatarSession(
                replica_id=settings.tavus_replica_id,
                persona_id=settings.tavus_persona_id or None,
                api_key=settings.tavus_api_key,
                avatar_participant_identity="tavus-avatar",
                avatar_participant_name="AI Assistant",
            )
            await avatar.start(
                agent_session=session,
                room=ctx.room,
                livekit_url=settings.livekit_url,
                livekit_api_key=settings.livekit_api_key,
                livekit_api_secret=settings.livekit_api_secret,
            )
            logger.info("Tavus AvatarSession started (conversation_id=%s)", avatar.conversation_id)
        except Exception as e:
            logger.warning("Tavus avatar failed to start (continuing without it): %s", e)
    else:
        logger.info("Tavus not configured — skipping avatar (set TAVUS_API_KEY + TAVUS_REPLICA_ID)")

    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=RoomInputOptions(text_enabled=True),
    )
    logger.info("AgentSession started")

    await session.say(
        "Hello! Welcome to our clinic. I'm your healthcare assistant. "
        "May I have your phone number to get started?",
        allow_interruptions=True,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name="agent-test",
            ws_url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )
    )
