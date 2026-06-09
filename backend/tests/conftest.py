"""pytest 공통 픽스처 — CI 환경변수 주입 + 외부 의존성 stub."""

import os
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

# ── 1) 환경변수 (모듈 import 전에 세팅해야 JWT_SECRET_KEY 검사를 통과)
_TEST_ENV = {
    "JWT_SECRET_KEY": "test-secret-key-for-ci-only",
    "MONGODB_URL": "mongodb://localhost:27017",
    "MONGODB_DB_NAME": "rainbow_test",
    "REDIS_URL": "redis://localhost:6379",
    "POSTGRES_URL": "postgresql+asyncpg://user:pass@localhost/rainbow_test",
}
for _k, _v in _TEST_ENV.items():
    os.environ.setdefault(_k, _v)


# ── 2) 설치되지 않은 외부 패키지 stub (redis, motor 등)
def _stub_module(name: str) -> ModuleType:
    mod = ModuleType(name)
    sys.modules[name] = mod
    return mod


if "chromadb" not in sys.modules:
    _chroma = _stub_module("chromadb")
    _chroma.PersistentClient = MagicMock
    _chroma.Client = MagicMock

if "redis" not in sys.modules:
    _redis = _stub_module("redis")
    _redis_asyncio = _stub_module("redis.asyncio")
    # from_url 이 aioredis.Redis 인스턴스를 반환하도록 stub
    _mock_redis_instance = MagicMock()
    _mock_redis_instance.pipeline = MagicMock(
        return_value=MagicMock(__aenter__=AsyncMock(), __aexit__=AsyncMock())
    )
    _redis_asyncio.from_url = MagicMock(return_value=_mock_redis_instance)
    _redis_asyncio.Redis = MagicMock
