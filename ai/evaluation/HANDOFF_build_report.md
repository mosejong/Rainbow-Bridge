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

---

## 추가 (2026-06-11) — 수면·활동 객관데이터 파라미터

`build_report` 가 `sleep_score`/`sleep_hours`/`steps`(전부 optional, 기본 `None`)를 받아 `recovery_signal` 까지 전달합니다. **하위호환** — 미제공 시 기존과 100% 동일. 출력 `recovery_signal` 에 `sleep_score`·`activity_score`·`cross_check`·`scoring` 키가 추가됩니다.

- **데이터 출처:** 삼성헬스 → Health Connect → 앱(개발빌드) → 저장. 영속화 컬렉션(`health_logs`)·스키마는 **모세종 영역 + P0 결정 대기**.
- 연결법: `get_report` 가 그 데이터를 읽어 위 교체안 `build_report(...)` 호출에 `sleep_score=`/`steps=` 인자만 추가하면 끝.
- ⚠️ **P0 미정이라 아직 붙이지 말 것:** 수면 입력을 'Health Connect 수면시간'으로 할지 '주관 수면질 5점'으로 할지 미확정 → 확정 시 공개 시그니처가 바뀔 수 있음(`sleep_hours` vs 체크인 신규 필드).

---

## health_logs 입력 계약 (제안 — 모세종 영역, P0 조건부)

> Plan 에이전트 감사(2026-06-11)가 "정환주가 입력 스키마 계약을 안 줘서 모세종이 막힘"이라 지적 → 제안만 적어둠. **P0 결정 전엔 구현하지 말 것.** 수면 필드 형식이 P0에서 갈림.

영속화 컬렉션 `health_logs` (반려동물·날짜별 1문서, 삼성헬스→Health Connect→앱이 적재):

```jsonc
{
  "pet_id": "string",
  "date": "2026-06-11",          // 일 단위 집계 키
  "steps": 6200,                 // 정수, 하루 걸음 (없으면 필드 생략 → activity 미측정)
  "sleep_hours": 7.5,            // (분기A) Health Connect 객관 수면시간
  // "sleep_quality": 4,         // (분기B) P0가 '주관 수면질'이면 이 필드로 — 체크인에 신규 필드 추가(모세종·민경이)
  "source": "health_connect",    // 출처 추적
  "synced_at": "2026-06-11T08:00:00+09:00"
}
```

- `get_report` 가 `health_logs.find({pet_id, 기간})` → 최근 1건(또는 평균)을 골라 `build_report(... sleep_score=/sleep_hours=/steps=)` 에 그대로 전달.
- **P0 분기:** (A) 객관 수면시간 점수반영 → `sleep_hours` 그대로. (B) 주관 수면질 → 체크인 스키마에 `sleep_quality` 신규 필드(모세종·민경이 작업) + 산식/테스트 재작성(정환주). 어느 쪽이든 **객관 `steps`·`sleep_hours`는 cross_check(교차검증)용으로 항상 적재**하면 손해 없음.
- 미측정 표현: 필드 생략 = `None` 전달 = 옵션A 재정규화로 점수 안 깎임(이미 구현됨).
