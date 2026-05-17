"""Tests para el módulo de configuración."""
import os
import pytest
from unittest.mock import patch


def test_settings_faltan_variables():
    """Test: cuando faltan variables, get_settings() lanza error."""
    with patch.dict(os.environ, {}, clear=True):
        from src.config import Settings, get_settings
        settings = Settings(_env_file=None)
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
        from src.config import Settings
        settings = Settings(_env_file=None)
        assert settings.openai_api_key == 'sk-test-openai'
        assert settings.supabase_url == 'https://test.supabase.co'


def test_settings_solo_algunas_presentes():
    """Test: falla si falta alguna variable."""
    env_vars = {
        'OPENAI_API_KEY': 'sk-test',
    }
    with patch.dict(os.environ, env_vars, clear=True):
        from src.config import get_settings
        with pytest.raises(ValueError) as exc_info:
            get_settings()
        assert 'MINIMAX_API_KEY' in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])