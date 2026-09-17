import os
import pytest

# Ensure automated regression tests run with inmemory persistence by default
# so that offline unit/mock test suites execute cleanly without requiring external
# live Supabase network connections or failing on missing live service credentials.
# Live and fail-loud behaviors are tested explicitly.
os.environ.setdefault("PERSISTENCE_BACKEND", "inmemory")
