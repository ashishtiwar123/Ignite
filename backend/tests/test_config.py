from app.config.settings import get_settings

def test_settings_defaults():
    settings = get_settings()
    assert settings.ENVIRONMENT in ["development", "production", "staging", "test"]
    assert isinstance(settings.CORS_ORIGINS, list)
