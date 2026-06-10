"""get_timeline 단위 테스트 — 여러 컬렉션 조합·필터·created_at 정규화 검증.

페이크 DB로 messages·emotions·missions·media_assets 를 흉내 내고,
safety 제외 / completed·done 필터 / datetime·str 혼재 정렬을 확인한다.
"""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.services.timeline import get_timeline

_PET = "pet_tl_1"


def _dt(day: int) -> datetime:
    return datetime(2026, 6, day, 9, 0, tzinfo=timezone.utc)


def _match(doc: dict, query: dict) -> bool:
    for k, v in query.items():
        if isinstance(v, dict) and "$ne" in v:
            if doc.get(k) == v["$ne"]:
                return False
        elif doc.get(k) != v:
            return False
    return True


class _Cursor:
    def __init__(self, docs):
        self._docs = docs

    def __aiter__(self):
        async def _gen():
            for d in self._docs:
                yield d

        return _gen()


class _Collection:
    def __init__(self, docs):
        self._docs = docs

    def find(self, query=None, projection=None):
        query = query or {}
        return _Cursor([d for d in self._docs if _match(d, query)])


class _DB:
    def __init__(self, cols):
        self._cols = cols

    def __getitem__(self, name):
        return self._cols.get(name, _Collection([]))


def _fake_mongo(cols):
    class _M:
        db = _DB(cols)

    return _M()


@pytest.mark.asyncio
async def test_timeline_combines_and_filters():
    cols = {
        "messages": _Collection(
            [
                {"_id": "m1", "pet_id": _PET, "source": "local", "created_at": _dt(2)},
                # safety(위기) 메시지는 제외돼야 함
                {"_id": "m2", "pet_id": _PET, "source": "safety", "created_at": _dt(9)},
            ]
        ),
        "emotions": _Collection([{"_id": "e1", "pet_id": _PET, "created_at": _dt(1)}]),
        "missions": _Collection(
            [
                {
                    "_id": "ms1",
                    "pet_id": _PET,
                    "completed": True,
                    "completed_at": _dt(3),
                },
                # 미완료 미션은 제외
                {
                    "_id": "ms2",
                    "pet_id": _PET,
                    "completed": False,
                    "created_at": _dt(8),
                },
            ]
        ),
        "media_assets": _Collection(
            [
                {"_id": "md1", "pet_id": _PET, "status": "done", "created_at": _dt(4)},
                # 미완성 영상은 제외
                {
                    "_id": "md2",
                    "pet_id": _PET,
                    "status": "processing",
                    "created_at": _dt(7),
                },
            ]
        ),
    }
    with patch("app.services.timeline.mongodb", new=_fake_mongo(cols)):
        items = await get_timeline(_PET)

    # 포함: message(m1)·emotion(e1)·mission(ms1)·media(md1) = 4개. safety·미완료·미완성 제외.
    assert [i["type"] for i in items] == ["media", "mission", "message", "emotion"]
    ids = {i["_id"] for i in items}
    assert ids == {"m1", "e1", "ms1", "md1"}
    assert "m2" not in ids and "ms2" not in ids and "md2" not in ids
    # ref_id 동봉, created_at 은 ISO 문자열
    assert all(i["ref_id"] == i["_id"] for i in items)
    assert all(isinstance(i["created_at"], str) for i in items)
    # 최신순(내림차순): md1(4)>ms1(3)>m1(2)>e1(1)
    dates = [i["created_at"] for i in items]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.asyncio
async def test_timeline_normalizes_mixed_created_at():
    """created_at 이 datetime/str 혼재해도 정렬·정규화가 깨지지 않는다(옛 데이터 방어)."""
    cols = {
        "messages": _Collection(
            [
                {"_id": "m1", "pet_id": _PET, "source": "local", "created_at": _dt(5)},
                # 옛 데이터: 문자열로 저장된 created_at
                {
                    "_id": "m2",
                    "pet_id": _PET,
                    "source": "local",
                    "created_at": "2026-06-03T09:00:00+00:00",
                },
            ]
        ),
    }
    with patch("app.services.timeline.mongodb", new=_fake_mongo(cols)):
        items = await get_timeline(_PET)

    assert [i["_id"] for i in items] == ["m1", "m2"]  # 6/5 > 6/3
    assert all(isinstance(i["created_at"], str) for i in items)


@pytest.mark.asyncio
async def test_timeline_empty_returns_list():
    """기록이 없으면 404가 아니라 빈 배열(프론트 빈 상태 표시용)."""
    with patch("app.services.timeline.mongodb", new=_fake_mongo({})):
        items = await get_timeline("no_such_pet")
    assert items == []
