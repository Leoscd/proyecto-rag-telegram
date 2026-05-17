"""Cliente de Supabase para RAG-Obras."""
from supabase import create_client, Client
from typing import Optional

from .config import get_settings_lazy


_client: Optional[Client] = None


def get_client() -> Client:
    """Crea y retorna el cliente de Supabase."""
    global _client
    if _client is None:
        settings = get_settings_lazy()
        _client = create_client(settings.supabase_url, settings.supabase_key)
    return _client


def reset_client():
    """Reset del cliente (para testing)."""
    global _client
    _client = None