import os
from supabase import create_client, Client
from app.config.settings import get_settings
import logging

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client | None:
    """
    Initialize and return the Supabase client safely.
    Returns None if configuration is missing, rather than crashing or using dummy keys.
    """
    settings = get_settings()
    
    # We must explicitly ensure we don't try to connect with empty dummy strings
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase credentials are not fully configured.")
        return None
        
    try:
        # Create a single client instance
        client: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        return None
