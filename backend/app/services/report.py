from app.db.mongodb import mongodb
from app.schemas.report import EmotionTrend, ReportResponse

# TODO: 정환주님 ai/evaluation/report.py 의 build_report 연결 후 교체
# from ai.evaluation.report import build_report


async def get_report(pet_id: str, period: str | None = None) -> ReportResponse:
    """반려동물별 사용 리포트 집계.

    현재는 DB에서 직접 집계하는 스텁입니다.
    정환주님 build_report 함수와 연결 시 DB 조회 결과를 주입하면 됩니다.
    """
    # 감정 추이
    cursor = (
        mongodb.db["emotions"]
        .find({"pet_id": pet_id}, {"score": 1, "created_at": 1})
        .sort("created_at", 1)
    )
    emotion_trend = [
        EmotionTrend(created_at=str(doc["created_at"]), score=doc["score"])
        async for doc in cursor
    ]

    # 미션 완료율
    missions = await mongodb.db["missions"].find({"pet_id": pet_id}).to_list(None)
    completion_rate = None
    if missions:
        done = sum(1 for m in missions if m.get("completed"))
        completion_rate = round(done / len(missions), 3)

    # LLM 사용 횟수 (llm_logs 컬렉션 — 정환주님 logs.py 연결 전 임시)
    total_calls = await mongodb.db["messages"].count_documents({"pet_id": pet_id})

    return ReportResponse(
        pet_id=pet_id,
        period=period,
        usage={"total_calls": total_calls},
        emotion_trend=emotion_trend,
        mission_completion_rate=completion_rate,
    )
