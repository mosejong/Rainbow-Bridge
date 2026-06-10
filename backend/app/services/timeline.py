"""타임라인 집계 — 여러 컬렉션을 합쳐 반려동물별 추모 기록 시계열로.

프론트(timeline.jsx)는 각 항목의 ``{_id, type, created_at}`` 만 쓰고,
type 은 emotion·message·mission·media 4종을 안다(TYPE_META).
"""

from typing import Any

from app.db.mongodb import mongodb


def _iso(ts: Any) -> str:
    """created_at 정규화 — datetime/str 혼재(옛 데이터) 방어.

    ISO 문자열은 사전식 정렬 = 시간순이라, 정규화 후 문자열 정렬로 안전하게 묶는다.
    """
    return ts.isoformat() if hasattr(ts, "isoformat") else str(ts)


def _entry(doc: dict, type_: str, ts: Any) -> dict:
    _id = str(doc["_id"])
    return {"_id": _id, "type": type_, "ref_id": _id, "created_at": _iso(ts)}


async def get_timeline(pet_id: str) -> list[dict]:
    """추모 기록(메시지·감정·완료미션·완성영상)을 합쳐 최신순으로 반환. 없으면 빈 리스트."""
    items: list[dict] = []

    # 추모 메시지 — 위기(safety) 메시지는 타임라인에서 제외
    async for d in mongodb.db["messages"].find(
        {"pet_id": pet_id, "source": {"$ne": "safety"}}, {"created_at": 1}
    ):
        items.append(_entry(d, "message", d.get("created_at")))

    # 감정 기록
    async for d in mongodb.db["emotions"].find({"pet_id": pet_id}, {"created_at": 1}):
        items.append(_entry(d, "emotion", d.get("created_at")))

    # 완료한 미션 — 완료 시각 기준(없으면 생성 시각)
    async for d in mongodb.db["missions"].find(
        {"pet_id": pet_id, "completed": True}, {"created_at": 1, "completed_at": 1}
    ):
        items.append(_entry(d, "mission", d.get("completed_at") or d.get("created_at")))

    # 완성된 추모 영상
    async for d in mongodb.db["media_assets"].find(
        {"pet_id": pet_id, "status": "done"}, {"created_at": 1}
    ):
        items.append(_entry(d, "media", d.get("created_at")))

    items.sort(key=lambda x: x["created_at"] or "", reverse=True)
    return items
