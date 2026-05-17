"""Configuración del proyecto RAG-Obras."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Settings cargados desde variables de entorno."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = Field(default="", description="OpenAI API key para embeddings")
    minimax_api_key: str = Field(default="", description="MiniMax API key para LLM")
    minimax_group_id: str = Field(default="", description="MiniMax Group ID")
    supabase_url: str = Field(default="", description="URL de Supabase")
    supabase_key: str = Field(default="", description="API key de Supabase")
    telegram_bot_token: str = Field(default="", description="Token del bot de Telegram")


def get_settings() -> Settings:
    """Carga settings y valida que estén presentes."""
    settings = Settings()

    missing = []
    if not settings.openai_api_key:
        missing.append("OPENAI_API_KEY")
    if not settings.minimax_api_key:
        missing.append("MINIMAX_API_KEY")
    if not settings.minimax_group_id:
        missing.append("MINIMAX_GROUP_ID")
    if not settings.supabase_url:
        missing.append("SUPABASE_URL")
    if not settings.supabase_key:
        missing.append("SUPABASE_KEY")
    if not settings.telegram_bot_token:
        missing.append("TELEGRAM_BOT_TOKEN")

    if missing:
        raise ValueError(f"Faltan variables requeridas: {', '.join(missing)}")

    return settings


# Instancia global (se carga lazy)
_settings: Optional[Settings] = None


def get_settings_lazy() -> Settings:
    """Obtiene settings, cachea la primera vez."""
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings