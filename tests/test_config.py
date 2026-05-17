"""Tests para el módulo de configuración."""
import os
import pytest
from unittest.mock import patch


def test_settings_faltan_variables():
    """Test: cuando faltan variables, get_settings() lanza error."""
    # Mock sin vars de entorno
    with patch.dict(os.environ, {}, clear=True):
        from src.config import get_settings
        from src.config import Settings

        # Si clear=True, no hay .env
        settings = Settings()
        # Forzar que no cargue de .env (si existiera)
        with patch.object(settings, 'openai_api_key', ''):
            with pytest.raises(ValueError) as exc_info:
                get_settings()
            assert 'OPENAI_API_KEY' in str(exc_info.value)


def test_settings_todas_presentes():
    """Test: cuando todas las variables están, settings carga."""
    env_vars = {
        'OPENAI_API_KEY': 'sk-test-openai',
        'MINIMAX_API_KEY': 'sk-test-minimax',
        'MINIMAX_GROUP_ID': 'test-group',
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key',
        'TELEGRAM_BOT_TOKEN': 'test-token',
    }
    with patch.dict(os.environ, env_vars, clear=True):
        from src.config import get_settings
        settings = get_settings()
        assert settings.openai_api_key == 'sk-test-openai'
        assert settings.supabase_url == 'https://test.supabase.co'


def test_settings_solo_algunas_presentes():
    """Test: falla si falta alguna variable."""
    env_vars = {
        'OPENAI_API_KEY': 'sk-test',
        # faltan las demás
    }
    with patch.dict(os.environ, env_vars, clear=True):
        from src.config import get_settings
        with pytest.raises(ValueError) as exc_info:
            get_settings()
        assert 'MINIMAX_API_KEY' in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])