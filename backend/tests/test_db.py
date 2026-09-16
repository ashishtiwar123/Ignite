import os
from unittest import mock
from app.db.client import get_supabase_client
from app.config.settings import get_settings

def test_supabase_missing_credentials_fails_gracefully():
    # If SUPABASE_URL or KEY are empty, the client should return None
    # Instead of mutating the actual environment, we mock the settings
    with mock.patch('app.db.client.get_settings') as mock_get_settings:
        mock_settings = mock.Mock()
        mock_settings.SUPABASE_URL = ""
        mock_settings.SUPABASE_KEY = ""
        mock_get_settings.return_value = mock_settings
        
        client = get_supabase_client()
        assert client is None

def test_supabase_client_initialization():
    # Test valid configuration
    with mock.patch('app.db.client.get_settings') as mock_get_settings:
        mock_settings = mock.Mock()
        mock_settings.SUPABASE_URL = "http://localhost:8000"
        mock_settings.SUPABASE_KEY = "dummy-key-for-test-do-not-use"
        mock_get_settings.return_value = mock_settings
        
        # We also need to mock create_client so it doesn't actually try to connect
        with mock.patch('app.db.client.create_client') as mock_create_client:
            mock_client = mock.Mock()
            mock_create_client.return_value = mock_client
            
            client = get_supabase_client()
            assert client is not None
            mock_create_client.assert_called_once_with("http://localhost:8000", "dummy-key-for-test-do-not-use")
