# 핸드오프 — ⑧ `build_report` 백엔드 연결 (→ 모세종)

> 작성: 정환주 · 대상: 백엔드 `backend/app/services/report.py` 주인(모세종)
> AI 쪽 [`build_report`](report.py)(순수 함수)는 완성·테스트됨([tests/test_report.py](tests/test_report.py)).
> 지금 백엔드는 `messages.count`로 **임시 집계** 중 → 아래대로 바꾸면 실데이터로 흐름.
>
> **재확인 2026-06-05(정환주):** `build_report` 테스트 3종 통과 재검증 완료. 백엔드 `report.py`는
> 아직 스텁(`TODO` 주석·`messages.count_documents` 그대로) → 아래 교체안 여전히 유효. 모세종이 붙이면 됨.

---

## 왜 그냥 못 붙이나 — 필드명 불일치 3개

| 항목 | 백엔드 DB 필드 | `build_report` 입력 규약 | 처리 |
|------|----------------|--------------------------|------|
| 감정 | `score` | `mood` | 넣을 때 `mood`로 매핑 |
| 미션 | `completed` | `done` | 넣을 때 `done`으로 매핑 |
| 사용량 | `messages` 카운트(임시) | `llm_logs` 리스트 | `llm_logs` 컬렉션 조회로 교체 |

⚠️ **트레이드오프:** 사용량을 `llm_logs` 기반으로 바꾸면, `save_log` 훅이 호출부(③ message.py·provider.py)에
아직 안 붙은 동안은 `total_calls=0`이 됩니다. 이건 "아직 로깅 안 됨"의 정확한 표시이고,
writer 일원화(#34 vs logs.py) + 훅 연결되면 자동으로 채워집니다.

---

## 교체안 (`backend/app/services/report.py` 전체)

```python
from ai.evaluation.report import build_report
from app.db.mongodb import mongodb
from app.schemas.report import EmotionTrend, ReportResponse


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

    report = build_report(
        pet_id,
        period,
        llm_logs=llm_logs,
        emotion_checkins=emotion_checkins,
        missions=missions,
    )

    # build_report 출력 → ReportResponse 매핑 (mood → score)
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
    )
```

- 임포트 경로 OK: 백엔드는 이미 `from ai.tts`·`from ai.llm.safety` 쓰는 중이라 `ai.evaluation`도 동일하게 잡힘.
- `ruff`·`black` 통과 확인함. push 전 `pytest -q`만 한번 더(로컬에 `motor` 설치 필요).
- 검증 끝나면 `report.py:4~5`의 TODO 주석 2줄 삭제.

> 백엔드는 모세종 영역이라 정환주가 직접 안 고치고 이 메모로 넘깁니다. 합치실 때 위 코드 그대로 쓰시면 됩니다.
