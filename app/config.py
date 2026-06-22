from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    deepgram_api_key: str
    groq_api_key: str
    sarvam_api_key: str = ""
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "BpjGufoPiobT79j2vtj4"
    elevenlabs_model: str = "eleven_turbo_v2_5"
    tavus_api_key: str = ""
    tavus_replica_id: str = ""
    tavus_persona_id: str = ""
    frontend_url: str = "http://localhost:5173"
    database_url: str = "sqlite+aiosqlite:///./data/app.db"

    class Config:
        env_file = ".env"


settings = Settings()
