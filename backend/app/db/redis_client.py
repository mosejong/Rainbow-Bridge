"""Redis 클라이언트 — 감정 체크인 최근 기록 캐시."""

import json
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

_client: Optional[aioredis.Redis] = None

RECENT_EMOTIONS_MAX = 7  # 최근 N회 보관
RECENT_EMOTIONS_TTL = 86400  # 24h


def get_redis() -> aioredis.Redis:
    global _client
    if _client is None:
        _client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


async def push_emotion(
    pet_id: str, score: int, risk_level: int, created_at: str
) -> None:
    r = get_redis()
    key = f"pet:{pet_id}:emotions:recent"
    entry = json.dumps(
        {"score": score, "risk_level": risk_level, "created_at": created_at}
    )
    async with r.pipeline() as pipe:
        pipe.lpush(key, entry)
        pipe.ltrim(key, 0, RECENT_EMOTIONS_MAX - 1)
        pipe.expire(key, RECENT_EMOTIONS_TTL)
        await pipe.execute()


async def get_recent_emotions(pet_id: str) -> list[dict]:
    r = get_redis()
    key = f"pet:{pet_id}:emotions:recent"
    raw = await r.lrange(key, 0, -1)
    return [json.loads(x) for x in raw]
