import app.core.ai_path  # noqa: F401

from ai.evaluation.report import build_report

from app.db.mongodb import mongodb
from app.schemas.report import EmotionTrend, ReportResponse
from bson import ObjectId


async def get_report(pet_id: str, period: str | None = None) -> ReportResponse:
    """반려동물별 사용 리포트 집계.

    DB 조회는 여기(백엔드)서 하고, 실제 집계는 ai/evaluation 의 순수 함수
    build_report 에 위임(정환주 ⑧). 컬렉션 필드명을 build_report 입력
    규약(mood·done)에 맞춰 정규화해 넘긴다.
    """
    # 감정: DB score → build_report 의 mood 키로 정규화
    emotion_checkins = [
        {"created_at": str(doc["created_at"]), "mood": doc["score"]}
        async for doc in mongodb.db["emotions"]
        .find({"pet_id": pet_id}, {"score": 1, "created_at": 1})
        .sort("created_at", 1)
    ]

    # 미션: DB completed → done 키로 정규화
    raw_missions = await mongodb.db["missions"].find({"pet_id": pet_id}).to_list(None)
    missions = [{"done": m.get("completed")} for m in raw_missions]

    # LLM 사용 로그: llm_logs 컬렉션 (messages.count 임시 → 실데이터)
    llm_logs = await mongodb.db["llm_logs"].find({"pet_id": pet_id}).to_list(None)
    # 영상 재생횟수 집계
    play_count = 0
    async for doc in mongodb.db["media_assets"].find(
        {"pet_id": pet_id}, {"play_count": 1}
    ):
        play_count += doc.get("play_count", 0)

    # 로그인 접속 횟수 집계
    pet_doc = await mongodb.db["pets"].find_one(
        {"_id": ObjectId(pet_id)}, {"user_id": 1}
    )
    user_id = pet_doc.get("user_id") if pet_doc else None
    session_count = (
        await mongodb.db["access_logs"].count_documents({"user_id": user_id})
        if user_id
        else 0
    )

    report = build_report(
        pet_id,
        period,
        llm_logs=llm_logs,
        emotion_checkins=emotion_checkins,
        missions=missions,
        play_count=play_count,
        session_count=session_count,
    )

    return ReportResponse(
        pet_id=report["pet_id"],
        period=report["period"],
        usage=report["usage"],
        emotion_trend=[
            EmotionTrend(created_at=str(row["created_at"]), score=row["mood"])
            for row in report["emotion_trend"]
        ],
        mission_completion_rate=report["mission_completion_rate"],
        revisit=report["revisit"],
        play_count=report["play_count"],
        session_count=report["session_count"],
    )
