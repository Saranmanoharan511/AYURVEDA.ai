import pytest
from app.core.config import settings


def test_settings_exist():
    """Test that settings are properly configured."""
    assert settings.APP_NAME is not None
    assert settings.APP_VERSION is not None
    assert settings.ENVIRONMENT is not None
    assert settings.DATABASE_URL is not None


def test_settings_defaults():
    """Test that settings have reasonable defaults."""
    assert settings.APP_NAME == "Ayurveda AI Platform"
    assert settings.APP_VERSION == "1.0.0"
    assert settings.ENVIRONMENT in ["development", "staging", "production"]
