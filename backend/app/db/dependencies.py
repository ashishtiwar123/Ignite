import logging
from fastapi import HTTPException
from app.config.settings import get_settings
from app.db.repositories import InMemoryIncidentRepository
from app.db.base_repository import BaseIncidentRepository

logger = logging.getLogger(__name__)

# Cache the in-memory repo so state persists across requests during testing
_in_memory_repo_instance = InMemoryIncidentRepository()

def get_incident_repository() -> BaseIncidentRepository:
    settings = get_settings()
    
    if settings.PERSISTENCE_BACKEND == "supabase":
        from app.db.supabase_repository import SupabaseIncidentRepository
        from app.db.client import get_supabase_client
        
        client = get_supabase_client()
        if not client:
            # DO NOT silently fall back to in-memory
            logger.error("Supabase backend requested but credentials missing/invalid.")
            raise RuntimeError("Supabase configuration is invalid or missing.")
            
        return SupabaseIncidentRepository(client)
        
    elif settings.PERSISTENCE_BACKEND == "inmemory":
        return _in_memory_repo_instance
        
    else:
        raise ValueError(f"Unknown PERSISTENCE_BACKEND: {settings.PERSISTENCE_BACKEND}")


from app.db.assessment_repository import InMemoryAssessmentRepository, BaseAssessmentRepository

_in_memory_assessment_repo_instance = InMemoryAssessmentRepository()

def get_assessment_repository() -> BaseAssessmentRepository:
    settings = get_settings()
    
    if settings.PERSISTENCE_BACKEND == "supabase":
        from app.db.supabase_assessment_repository import SupabaseAssessmentRepository
        from app.db.client import get_supabase_client
        
        client = get_supabase_client()
        if not client:
            logger.error("Supabase backend requested but credentials missing/invalid.")
            raise RuntimeError("Supabase configuration is invalid or missing.")
            
        return SupabaseAssessmentRepository(client)
        
    elif settings.PERSISTENCE_BACKEND == "inmemory":
        return _in_memory_assessment_repo_instance
        
    else:
        raise ValueError(f"Unknown PERSISTENCE_BACKEND: {settings.PERSISTENCE_BACKEND}")

from app.db.needs_repository import InMemoryNeedsRepository, BaseNeedsRepository

_in_memory_needs_repo_instance = InMemoryNeedsRepository()

def get_needs_repository() -> BaseNeedsRepository:
    settings = get_settings()
    
    if settings.PERSISTENCE_BACKEND == "supabase":
        from app.db.supabase_needs_repository import SupabaseNeedsRepository
        from app.db.client import get_supabase_client
        
        client = get_supabase_client()
        if not client:
            logger.error("Supabase backend requested but credentials missing/invalid.")
            raise RuntimeError("Supabase configuration is invalid or missing.")
            
        return SupabaseNeedsRepository(client)
        
    elif settings.PERSISTENCE_BACKEND == "inmemory":
        return _in_memory_needs_repo_instance
        
    else:
        raise ValueError(f"Unknown PERSISTENCE_BACKEND: {settings.PERSISTENCE_BACKEND}")

from app.db.resource_repository import InMemoryResourceRepository, BaseResourceRepository

_in_memory_resource_repo_instance = InMemoryResourceRepository()

def get_resource_repository() -> BaseResourceRepository:
    settings = get_settings()
    
    if settings.PERSISTENCE_BACKEND == "supabase":
        from app.db.supabase_resource_repository import SupabaseResourceRepository
        from app.db.client import get_supabase_client
        
        client = get_supabase_client()
        if not client:
            logger.error("Supabase backend requested but credentials missing/invalid.")
            raise RuntimeError("Supabase configuration is invalid or missing.")
            
        return SupabaseResourceRepository(client)
        
    elif settings.PERSISTENCE_BACKEND == "inmemory":
        return _in_memory_resource_repo_instance
        
    else:
        raise ValueError(f"Unknown PERSISTENCE_BACKEND: {settings.PERSISTENCE_BACKEND}")

from app.db.allocation_repository import InMemoryAllocationRepository, BaseAllocationRepository

_in_memory_allocation_repo_instance = InMemoryAllocationRepository()

def get_allocation_repository() -> BaseAllocationRepository:
    settings = get_settings()
    
    if settings.PERSISTENCE_BACKEND == "supabase":
        from app.db.supabase_allocation_repository import SupabaseAllocationRepository
        from app.db.client import get_supabase_client
        
        client = get_supabase_client()
        if not client:
            logger.error("Supabase backend requested but credentials missing/invalid.")
            raise RuntimeError("Supabase configuration is invalid or missing.")
            
        return SupabaseAllocationRepository(client)
        
    elif settings.PERSISTENCE_BACKEND == "inmemory":
        return _in_memory_allocation_repo_instance
        
    else:
        raise ValueError(f"Unknown PERSISTENCE_BACKEND: {settings.PERSISTENCE_BACKEND}")

