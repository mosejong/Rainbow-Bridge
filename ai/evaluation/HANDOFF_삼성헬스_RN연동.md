# 핸드오프 — 삼성헬스 실연동 (RN + 개발빌드)

> 작성: 정환주 · 2026-06-11 · 영역 `ai/evaluation/`(어댑터·점수) → **RN=민경이 / 엔드포인트=모세종** 인계.
> 목적: 삼성헬스(→Health Connect) **실데이터**를 회복점수에 흘려보내는 마지막 단계.
> Python 어댑터·점수 로직은 **완료**(더미 검증 58 테스트). 남은 건 ① RN 읽기 ② 백엔드 엔드포인트 ③ 개발빌드.

---

## 0. 왜 핸드오프인가 (경계)

| 부분 | 상태 | 담당 |
|------|------|------|
| Health Connect JSON → `{steps, sleep_hours}` 어댑터 | ✅ 완료 (`health_adapter.from_health_connect`) | 정환주 |
| 회복점수·교차검증 로직 | ✅ 완료 (`health_signal`·`recovery_signal`) | 정환주 |
| **RN 측 `readRecords` 읽기** | ⬜ 미구현 | **민경이** (네이티브 모듈) |
| **백엔드 수신 엔드포인트** | ⬜ 미구현 | **모세종** |
| **개발빌드 + 권한 허용** | ⬜ 미실행 | 폰 있는 사람 |

> ⚠️ 삼성헬스 모듈은 **Expo Go에서 안 됨**(네이티브) → **개발빌드 필수**. 팀 공유 Expo Go 워크플로 깨지지 않게 **격리 개발빌드 브랜치**에서 작업.

---

## 1. 전체 경로

```
삼성헬스 앱  ──(설정: Health Connect 동기화 ON)──▶  Health Connect
   ▲ 별개 생태계, 동기화 안 켜면 데이터 안 넘어옴
                                                      │
   RN 앱(개발빌드) ──readRecords('Steps'/'SleepSession')──┘
        │  raw JSON {records:[...]}
        ▼
   POST /api/v1/health-sync (백엔드, 모세종)
        │
        ▼  from_health_connect(steps_result, sleep_result) → {steps, sleep_hours}   ← 내 어댑터 재사용
   build_report(... steps=, sleep_hours=)  →  recovery_signal + cross_check
```

---

## 2. RN 측 코드 (민경이) — `react-native-health-connect@3.5.3`

> API는 공식 문서 검증함(2026-06-11): `initialize`/`requestPermission`/`readRecords` 시그니처 확인.
> `getSdkStatus`·`SdkAvailabilityStatus` 는 라이브러리 export — 사용 전 버전별 문서 재확인 권장.

```typescript
import {
  initialize,
  requestPermission,
  readRecords,
  getSdkStatus,
  SdkAvailabilityStatus,
} from 'react-native-health-connect';

// 오늘 0시~현재 (단일 일 범위 — 어댑터가 무조건 합산하므로 하루만 질의!)
function todayRange() {
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  return { operator: 'between' as const, startTime: start.toISOString(), endTime: now.toISOString() };
}

export async function readSamsungHealth() {
  // 1) Health Connect 설치/가용 확인
  const status = await getSdkStatus();
  if (status !== SdkAvailabilityStatus.SDK_AVAILABLE) {
    return { available: false, reason: status }; // 미설치/업데이트 필요 → UI 안내
  }

  // 2) 클라이언트 초기화
  const ok = await initialize();
  if (!ok) return { available: false, reason: 'init_failed' };

  // 3) 읽기 권한 (사용자가 '허용' 탭 — 사람 손 필요)
  await requestPermission([
    { accessType: 'read', recordType: 'Steps' },
    { accessType: 'read', recordType: 'SleepSession' },
  ]);

  // 4) 오늘치 읽기
  const timeRangeFilter = todayRange();
  const steps_result = await readRecords('Steps', { timeRangeFilter });
  const sleep_result = await readRecords('SleepSession', { timeRangeFilter });

  // 5) 백엔드로 raw JSON 그대로 전송 (파싱은 백엔드 from_health_connect 가 함)
  return { available: true, steps_result, sleep_result };
}
```

> ⚠️ **단일 일 범위만 질의.** 어댑터 `total_steps`/`total_sleep_hours` 는 넘어온 레코드를 **무조건 전부 합산**한다 → 여러 날 질의하면 합산돼 점수 왜곡(어댑터 docstring 경고 참고).

전송:
```typescript
const hc = await readSamsungHealth();
if (hc.available) {
  await fetch(`${API}/api/v1/health-sync`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }, // 한글 없음, UTF-8 자동
    body: JSON.stringify({
      pet_id,
      steps_result: hc.steps_result,   // {records:[{count, ...}]}
      sleep_result: hc.sleep_result,   // {records:[{startTime, endTime, ...}]}
    }),
  });
}
```

---

## 3. 백엔드 엔드포인트 계약 (모세종)

`POST /api/v1/health-sync` — RN raw JSON 수신 → 내 어댑터로 파싱 → 리포트.

```python
from ai.evaluation.health_adapter import from_health_connect
from ai.evaluation.report import build_report

@router.post("/api/v1/health-sync")
async def health_sync(body: HealthSyncIn):
    parsed = from_health_connect(body.steps_result, body.sleep_result)  # {steps, sleep_hours}
    # health_logs 저장(영속화) — 날짜별 1건. 이후 build_report 가 읽어 씀.
    await mongodb.db["health_logs"].insert_one({
        "pet_id": body.pet_id, "date": today(), **parsed,
    })
    report = build_report(body.pet_id, ..., **parsed)
    return report["recovery_signal"]
```

- 입력 스키마: `{pet_id: str, steps_result: dict|None, sleep_result: dict|None}`.
- `from_health_connect` 는 레코드 없으면 `None` 반환(graceful) — 어댑터가 이미 처리.
- ⚠️ **수면은 회복점수서 제외**(결정문서 §2) → `sleep_hours` 는 `cross_check`·표시로만 들어감. 활동(`steps`)만 점수 반영. (이미 코드에 반영됨)

---

## 4. 개발빌드 가이드 (폰 있는 사람)

Expo 프로젝트(`frontend-rn/`)는 Expo Go로 네이티브 모듈을 못 올림 → **개발빌드** 필요.

```bash
# 1) 라이브러리 설치
npx expo install react-native-health-connect

# 2) 네이티브 코드 생성(prebuild) — 격리 브랜치에서만!
npx expo prebuild --platform android

# 3-A) 로컬 빌드(안드 SDK 있으면)
npx expo run:android
# 3-B) 또는 클라우드 빌드(EAS)
eas build --platform android --profile development
```

설치 후 폰에서: **삼성헬스 → 설정 → Health Connect 동기화 ON** → 앱 실행 → 권한 "허용".

---

## 5. AndroidManifest 권한 (확인 필요 — 라이브러리 문서 기준으로 채울 것)

Health Connect 는 매니페스트에 read 권한 + 권한 안내 화면 intent-filter 가 필요하다. 정확한 권한 문자열·설정은 **react-native-health-connect 공식 문서의 setup 섹션을 따를 것**(버전마다 다를 수 있어 여기 임의 단정 안 함). 대략:
- `android.permission.health.READ_STEPS`, `android.permission.health.READ_SLEEP` (정확 문자열 문서 확인)
- 권한 사용 이유 안내(privacy policy) rationale 액티비티 등록
- `minSdkVersion` Health Connect 요구치 확인

---

## 6. 검증 체크리스트 (실기기 붙은 뒤)

1. `getSdkStatus()` → `SDK_AVAILABLE` (아니면 Health Connect 설치 안내 UI)
2. 권한 다이얼로그 떠서 "허용" → `requestPermission` resolve
3. `readRecords('Steps')` 가 `{records:[{count}]}` 반환 (오늘 데이터)
4. `POST /api/v1/health-sync` → `recovery_signal` 응답에 `activity_score`·`sleep_score`·`cross_check` 채워짐
5. `scoring == "blend"`(활동 들어옴), 수면은 `"참고 — 점수 미반영"` 표시
6. **백업:** 실기기 안 되면 §export 경로(본인 데이터 내보내기 → 파서)로 발표 실결과 대체

---

## 7. 빌드 없이 실결과 — export 경로 (정환주 단독, 발표 백업)

삼성헬스 앱 → **설정 → 데이터 다운로드/내보내기** → zip/csv 받기 → 그 파일 형식 맞춰 파서 작성(`ai/evaluation/`) → 본인 실제 수면·걸음으로 회복점수 출력. **개발빌드·폰 권한 불필요.** 파일 형식 확인 후 1차 파서 작성 예정.
