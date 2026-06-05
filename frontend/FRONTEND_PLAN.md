# 프론트엔드 MVP 실행 계획 — 레인보우 브릿지

> 담당: 민경이 · 장민수 | 작성: 2026-06-02 | 최종 수정: 2026-06-05 | 발표: 2026-06-19 (D-14)
> 전체 협업 규칙: [CONTRIBUTING.md](../docs/CONTRIBUTING.md) | 아키텍처: [ARCHITECTURE.md](../docs/ARCHITECTURE.md)

> **백엔드 API 주소 (ngrok, 서버 켜있는 동안 사용):**
> `https://preacher-posing-lair.ngrok-free.dev`
> 로컬 확인용: `http://localhost:8000/docs`
> 민경이·장민수는 Docker 불필요 — 위 ngrok URL 바로 사용

---

## 0. 플랫폼 전략 (2026-06-05 확정)

### 웹(병원용) + Android 앱(유저용) 이중 배포

| 배포 대상 | 플랫폼 | 기술 | 대상 사용자 |
|------|------|------|------|
| 웹 | 브라우저 | Vite + React 빌드 → 서버 배포 | 병원·관련 기관 |
| Android 앱 | Google Play / APK | **Capacitor** (기존 코드 재사용) | 반려동물 보호자 |

> iOS(아이폰)는 Mac + 애플 개발자 계정 필요 → **이번 MVP 범위 제외**

### 결정 과정 요약

처음에는 발표 일정(6/19)만 고려해서 **PWA**를 검토했음.
하지만 "핸드폰에 앱 아이콘 생기고, 설치해서 앱처럼 쓰고 싶다"는 요구 확인 후 → **Capacitor**로 확정.

| | PWA | Capacitor (확정) |
|---|---|---|
| 홈 화면 아이콘 | ⚠️ 브라우저에서 "홈 추가" 필요 | ✅ 진짜 앱 아이콘 |
| 풀스크린 실행 | ⚠️ 브라우저 잔재 있음 | ✅ 주소창 없는 앱 |
| APK 설치 (발표용) | ❌ | ✅ |
| Google Play 출시 | ❌ | ✅ |
| iOS 지원 | ✅ | ❌ (Mac 없어서 제외) |
| 세팅 시간 | 반나절 | 1~2일 |

**최종 결정: Capacitor (Android 전용)** — iOS는 Mac + 애플 개발자 계정 필요하므로 이번 MVP 제외.

### 왜 Capacitor인가? (React Native 재작성 안 하는 이유)

| | Capacitor | React Native |
|---|---|---|
| 기존 React 코드 | **그대로 사용** | 전부 재작성 필요 |
| 작업량 | 세팅 1~2일 | 2주 이상 |
| 6/19 발표까지 가능? | ✅ | ❌ |
| Android 앱 배포 | ✅ | ✅ |
| Mac 없이 Android 빌드 | ✅ | ✅ |
| 실제 앱 아이콘 | ✅ | ✅ |
| 핸드폰에 직접 설치(APK) | ✅ | ✅ |

### Capacitor 동작 방식

```
npm run build (Vite)
    ↓
dist/ 폴더 (HTML + JS + CSS)
    ↓
Capacitor가 Android WebView 안에 넣음
    ↓
Android Studio → APK 빌드
    ↓
핸드폰에 설치 → 홈 화면 아이콘 생성 → 앱처럼 실행
```

### 사용자가 보는 것

- **홈 화면에 레인보우 브릿지 아이콘** 생김
- 아이콘 탭 → **풀스크린으로 앱 실행** (브라우저 주소창 없음)
- Google Play 출시 전에도 **APK 파일로 바로 설치** 가능 (테스트·발표용)

---

## 1. 기술 스택 확정

| 영역 | 선택 | 이유 |
|------|------|------|
| 빌드 | **Vite + React 18** | 빠른 HMR, 설정 최소, 일정에 최적 |
| 언어 | **JavaScript** (JS 우선) | 둘 다 처음이면 JS로 시작 → 나중에 TS 전환 가능 |
| 라우팅 | **React Router v6** | 페이지 전환 |
| HTTP | **axios** | 인터셉터로 에러·로딩 공통 처리 |
| 스타일 | **Tailwind CSS** | 빠른 UI 구성, 클래스 재사용 |
| 상태 | **React useState/useEffect** (기본) | TanStack Query는 선택 사항 |
| 모바일 앱 패키징 | **Capacitor** | 기존 웹 코드 → Android APK 변환 |

> 장민수님이 Node.js/npm 설치가 안 됐다면 오늘 먼저 해결하고 시작하세요. (아래 §7 셋업 참고)

---

## 2. 역할 분담 최종 확정

> 기준: "파일 단위로 담당이 갈리면 Git 충돌이 거의 없다" — 페이지 파일 = 담당자

### 민경이 담당 (핵심 서비스 플로우 + LLM 연동)

> 민경이 = **프론트-AI 연결 담당자**. 반소람님 프롬프트 완성되면 바로 붙이는 역할.

| 기능 | 페이지 파일 | 우선순위 |
|------|------------|---------|
| ⑦ 위험 감정 경고 모달 | `SafetyModal.jsx` | **1순위 (최우선)** |
| ① 반려동물 프로필 입력 | `ProfilePage.jsx` | 2순위 |
| ② 감정 체크인 | `EmotionPage.jsx` | 3순위 |
| ③ AI 추모 메시지 카드 + **LLM API 연동** | `MessagePage.jsx` | 4순위 |
| ⑧ 평가 리포트 | `ReportPage.jsx` | 마지막 |

**추가된 역할:** `POST /api/v1/messages/generate` 호출 + 결과 카드 UI. 반소람님 프롬프트 완성되면 바로 연동.

### 장민수 담당 (미디어·미션·타임라인)

| 기능 | 페이지 파일 | 우선순위 |
|------|------------|---------|
| ④ TTS 톤 선택 + 오디오 플레이어 | `TtsPage.jsx` | 2순위 |
| ⑤ 미션 카드 + 완료 체크 | `MissionPage.jsx` | 3순위 |
| ⑥ 추모 타임라인 | `TimelinePage.jsx` | 4순위 |
| 가산점: 사진→영상 다운로드 | `MediaPage.jsx` | 여유 시 |

### 공동 작업

| 항목 | 담당 | 시점 |
|------|------|------|
| Vite 프로젝트 초기 세팅 | **민경이** (먼저 push → 장민수 pull) | 완료 |
| 공통 컴포넌트 (`Button`, `Card`, `LoadingSpinner`) | **민경이** | 완료 |
| axios 인스턴스 + Mock 데이터 | **민경이** | 완료 |
| 앱 라우팅 (`App.jsx`) | **민경이** | 완료 |
| **Capacitor Android 앱 세팅** | **민경이** | 2주차 |

> ⚠️ `api/`, `components/`, `App.jsx` 는 공통 파일 — 수정할 때는 서로 미리 얘기하고 PR 올리기

---

## 3. 폴더 구조

```
frontend/
├── FRONTEND_PLAN.md       ← 이 파일
├── package.json
├── vite.config.js
├── capacitor.config.ts    ← Capacitor 세팅 후 생성됨
├── index.html
├── android/               ← Capacitor 세팅 후 생성됨 (Android Studio 프로젝트)
└── src/
    ├── api/
    │   ├── axiosInstance.js   # baseURL, 헤더 공통 설정
    │   ├── auth.js            # 로그인/회원가입
    │   ├── pets.js            # /api/v1/pets 관련 함수
    │   ├── emotions.js        # /api/v1/emotions
    │   ├── messages.js        # /api/v1/messages
    │   ├── missions.js        # /api/v1/missions
    │   ├── timeline.js        # /api/v1/timeline
    │   ├── report.js          # /api/v1/report
    │   ├── media.js           # /api/v1/media
    │   ├── hospitals.js       # /api/v1/hospitals (다음 주 연동 예정)
    │   └── funerals.js        # /api/v1/funerals (다음 주 연동 예정)
    ├── components/
    │   ├── Button.jsx
    │   ├── Card.jsx
    │   ├── LoadingSpinner.jsx
    │   └── SafetyModal.jsx    # 1393 경고 모달 (민경이, 최우선)
    ├── pages/
    │   ├── LoginPage.jsx      # 민경이
    │   ├── RegisterPage.jsx   # 민경이
    │   ├── ProfilePage.jsx    # 민경이
    │   ├── EmotionPage.jsx    # 민경이
    │   ├── MessagePage.jsx    # 민경이
    │   ├── SymptomsPage.jsx   # 민경이 (병원 카드 포함)
    │   ├── HealthRecordsPage.jsx # 민경이 (투약·검진 기록)
    │   ├── FuneralPage.jsx    # 민경이 (장례 안내)
    │   ├── TtsPage.jsx        # 장민수
    │   ├── MissionPage.jsx    # 장민수
    │   ├── TimelinePage.jsx   # 장민수
    │   ├── ReportPage.jsx     # 민경이
    │   └── MediaPage.jsx      # 장민수 (가산점)
    ├── hooks/
    │   └── useSafetyCheck.js  # 위험 감정 감지 훅
    ├── App.jsx                # 라우터 설정
    └── main.jsx               # 진입점
```

---

## 4. 백엔드 API 명세 (연동 기준)

> 백엔드가 아직 준비 안 됐으면 Mock 데이터로 화면 먼저 만들고, API 나오면 교체

### 엔드포인트 목록

| 기능 | 메서드 | 경로 | 담당 페이지 |
|------|--------|------|------------|
| 로그인 | `POST` | `/api/v1/auth/login` | LoginPage |
| 프로필 등록 | `POST` | `/api/v1/pets` | ProfilePage |
| 감정 체크인 | `POST` | `/api/v1/emotions` | EmotionPage |
| 메시지 생성 | `POST` | `/api/v1/messages/generate` | MessagePage |
| TTS 생성 | `POST` | `/api/v1/messages/{id}/tts` | TtsPage |
| 미션 조회 | `GET` | `/api/v1/missions?pet_id=` | MissionPage |
| 미션 완료 | `PATCH` | `/api/v1/missions/{id}` | MissionPage |
| 타임라인 | `GET` | `/api/v1/timeline/{pet_id}` | TimelinePage |
| 리포트 | `GET` | `/api/v1/report/{pet_id}` | ReportPage |
| 사진 업로드 | `POST` | `/api/v1/media/upload` | MediaPage |
| 주변 병원 | `GET` | `/api/v1/hospitals` | SymptomsPage |
| 장례식장 | `GET` | `/api/v1/funerals` | FuneralPage |
| 장례 기록 | `POST` | `/api/v1/funeral-records` | FuneralPage |

---

## 5. 기능별 상세 구현 계획

---

### ⑦ SafetyModal — 1393 위험 감정 경고 (민경이, 최우선)

**왜 먼저?** 법적·윤리적 안전 장치. 감정 체크인에서 risk_flag=true 오면 반드시 띄워야 함.

**구현 내용:**
```
- 모달 오버레이 (배경 어둡게)
- ⚠️ 아이콘 + "힘드신가요?" 제목
- "정신건강 위기상담 전화 1393" 문구 (굵게)
- [전화 연결] 버튼 → href="tel:1393" (클릭 시 전화 앱 연결)
- [닫기] 버튼
- 1393 번호는 절대 수정하지 말 것
```

**코드 스케치:**
```jsx
// components/SafetyModal.jsx
function SafetyModal({ isOpen, onClose }) {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 mx-4 max-w-sm text-center">
        <div className="text-4xl mb-3">⚠️</div>
        <h2 className="text-xl font-bold text-red-600 mb-2">힘드신가요?</h2>
        <p className="text-gray-700 mb-4">
          지금 많이 힘드시다면<br/>
          전문가와 이야기해보세요.
        </p>
        <a href="tel:1393"
           className="block bg-red-500 text-white py-3 rounded-xl font-bold text-lg mb-3">
          📞 정신건강 위기상담 1393
        </a>
        <button onClick={onClose} className="text-gray-400 text-sm">
          닫기
        </button>
      </div>
    </div>
  );
}
```

---

### ① ProfilePage — 반려동물 프로필 입력 (민경이)

**입력 필드:**
- 반려동물 이름 (텍스트)
- 종 (강아지/고양이/기타 라디오)
- 함께한 기간 (시작일~종료일)
- 추억 키워드 (텍스트, 최대 3개, 엔터로 추가)
- 사진 업로드 (선택, input file)

**제출 시 동작:**
1. `POST /api/v1/pets` 호출
2. 성공 → `pet_id` 저장 (localStorage) → EmotionPage로 이동
3. 실패 → 에러 메시지 표시

---

### ② EmotionPage — 감정 체크인 (민경이)

**UI:**
- 오늘 기분을 선택하세요 (이모지 버튼 5개)
- 선택한 감정 텍스트 + 선택적 메모 입력칸

**위험 감정 처리 (핵심!):**
```js
const RISK_MOODS = ['너무 힘들어요'];

async function handleSubmit() {
  const response = await postEmotion({ mood, note, pet_id });
  if (response.risk_flag || RISK_MOODS.includes(mood)) {
    setSafetyOpen(true);
    return;
  }
  navigate('/message');
}
```

---

### ③ MessagePage — AI 추모 메시지 생성 (민경이)

**UI 흐름:**
1. **로딩 상태**: 스피너 + "콩이의 추억을 떠올리고 있어요..." 텍스트
2. **완료 상태**: 메시지 카드 (둥근 카드, 파스텔 배경)
3. **버튼**: [다시 생성] [음성으로 듣기 → TtsPage]

**주의:** "반려동물인 척" 하는 메시지 형태 금지
- ✅ "콩이와 함께한 공원 산책은..."
- ❌ "안녕 나 콩이야, 잘 지내?"

---

### ④ TtsPage — 음성 낭독 (장민수)

**UI:**
- 톤 선택: [따뜻하게 / 차분하게 / 부드럽게] 버튼
- 선택 후 [낭독 시작] 버튼
- 오디오 플레이어 (재생/일시정지/음량)

---

### ⑤ MissionPage — 미션 추천 (장민수)

**UI:**
- 미션 카드 리스트 (체크박스 + 미션 내용)
- 완료 체크 시 선 긋기 효과 + API PATCH 호출
- "오늘 미션 모두 완료!" 달성 메시지

---

### ⑥ TimelinePage — 추모 타임라인 (장민수)

**UI:**
- 날짜별 세로 타임라인
- 각 항목: 날짜 + 타입 아이콘(감정/메시지/미션) + 내용 요약
- 스크롤로 과거 기록 탐색

---

### ⑧ ReportPage — 평가 리포트 (민경이)

**UI:**
- 감정 변화 그래프 (recharts 라이브러리)
- 미션 완료율 (%)
- 추모 메시지 생성 횟수

---

## 6. 일정표 (2026-06-02 ~ 06-19)

### 1주차 (6/2~6/8) — 세팅 + 핵심 기능 ✅ 완료

| 날짜 | 민경이 | 장민수 |
|------|--------|--------|
| 6/2~3 | Vite 세팅 + 공통 컴포넌트 + ProfilePage | 환경 세팅 |
| 6/4~5 | EmotionPage + MessagePage + SymptomsPage 병원 카드 | TtsPage, MissionPage |
| 6/5 | **HealthRecordsPage 신규 · FuneralPage 신규 · 모바일 반응형 수정** | |
| 6/6~8 | 린트 정리, dev 머지, PR 정리 | 각 페이지 마무리 |

### 2주차 (6/9~6/13) — API 연동 + Android 앱 패키징

| 날짜 | 할 일 |
|------|------|
| 6/9~10 | 백엔드 API 연동 (hospitals, funerals) · axiosInstance 실서버 교체 |
| 6/11~12 | Mock 데이터 → 실제 API로 교체 (기능별) |
| 6/12~13 | **Capacitor 세팅 + Android Studio 빌드 + 핸드폰 APK 설치 테스트** |

#### Capacitor Android 세팅 순서 (6/12~13 예정)

> 사전 조건: Android Studio + JDK 17 설치 필요

```bash
# 1. Capacitor 설치
npm install @capacitor/core @capacitor/cli @capacitor/android

# 2. 초기화 (앱 이름, 패키지명 입력)
npx cap init "레인보우브릿지" "com.rainbowbridge.app"

# 3. Vite 빌드
npm run build

# 4. Android 플랫폼 추가
npx cap add android

# 5. 빌드 결과물 동기화
npx cap sync android

# 6. Android Studio로 열기
npx cap open android
# → Android Studio에서 Run 버튼 → 핸드폰 연결 or 에뮬레이터
```

**APK 빌드 후 확인 사항:**
- [ ] 홈 화면에 앱 아이콘 생성
- [ ] 아이콘 탭 → 풀스크린 앱 실행 (주소창 없음)
- [ ] 로그인 → 감정 체크인 → 메시지 카드 전체 플로우
- [ ] 전화 버튼(1393) 탭 → 전화 앱 실행

### 3주차 (6/16~6/19) — 통합 + 발표 준비

| 날짜 | 할 일 |
|------|------|
| 6/16~17 | 전체 플로우 연결 테스트 (프로필→감정→메시지→미션) |
| 6/18 | 앱 아이콘 디자인 확정, 에러/로딩 처리, 모바일 대응 최종 점검 |
| 6/19 | 발표 리허설, 데모 환경 점검 (APK 설치 상태로 발표) |

---

## 7. Capacitor 세팅 시 주의사항

### API 주소 처리

Capacitor 앱은 `file://` 프로토콜로 실행되기 때문에 `localhost`에 접근이 안 됨. 반드시 ngrok URL 또는 실서버 주소 사용.

```js
// src/api/axiosInstance.js
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'https://preacher-posing-lair.ngrok-free.dev',
});
```

### Android 권한 (필요 시 추가)

- 카카오맵 위치 기반: `android/app/src/main/AndroidManifest.xml`에 위치 권한 추가
- 사진 업로드: 카메라·갤러리 접근 권한

### 앱 아이콘 변경

`android/app/src/main/res/` 폴더의 아이콘 파일을 교체하거나 Capacitor Assets 플러그인 사용.

---

## 8. 충돌 방지 규칙

1. **`pages/` 파일은 본인 담당만 수정** — 남의 파일 건드리면 반드시 먼저 알리기
2. **`components/`, `api/`, `App.jsx` 수정 시** — 카톡/슬랙으로 먼저 공지
3. **PR 단위**: 기능 하나 완성되면 바로 PR (한 번에 모아서 올리지 말 것)
4. **PR base는 항상 `dev`** — `main` 아님!
5. 막히면 5분 혼자 시도 후 바로 팀 채널 질문

---

## 9. 공통 컴포넌트 스펙

```jsx
// components/Button.jsx
// props: children, onClick, variant("primary"|"danger"|"ghost"), disabled, className
// primary: 보라색 배경 / danger: 빨간색 / ghost: 테두리만

// components/Card.jsx
// props: children, className(추가 클래스)
// 기본: 흰 배경, 둥근 모서리(rounded-2xl), 그림자(shadow-md), 패딩(p-6)

// components/LoadingSpinner.jsx
// 가운데 정렬 스피너 + 선택적 메시지 텍스트
```

---

## 10. 디자인 가이드

서비스 특성상 **부드럽고 따뜻한 톤**을 유지하세요.

| 용도 | 색상 |
|------|------|
| 주 색상 | 보라 계열 `#8B5CF6` (Tailwind: `violet-500`) |
| 배경 | 연한 라벤더 `#F5F3FF` |
| 위험 감정 | 빨강 `#EF4444` (Tailwind: `red-500`) |
| 텍스트 주 | `gray-800` |
| 텍스트 보조 | `gray-500` |
| 카드 배경 | 흰색 + 그림자 |

---

## 참고 문서

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) — API 경로·데이터 모델 확인
- [CONTRIBUTING.md](../docs/CONTRIBUTING.md) — PR·커밋 규칙
- [GIT_GUIDE.md](../docs/GIT_GUIDE.md) — Git 명령어
- [PROGRESS.md](../docs/PROGRESS.md) — 기능 완료 시 상태 업데이트 필수
