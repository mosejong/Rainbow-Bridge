# 프론트엔드 MVP 실행 계획 — 레인보우 브릿지

> 담당: 민경이 · 장민수 | 작성: 2026-06-02 | 발표: 2026-06-19 (D-17)
> 전체 협업 규칙: [CONTRIBUTING.md](../docs/CONTRIBUTING.md) | 아키텍처: [ARCHITECTURE.md](../docs/ARCHITECTURE.md)

---

## 1. 기술 스택 확정

| 영역 | 선택 | 이유 |
|------|------|------|
| 빌드 | **Vite + React 18** | 빠른 HMR, 설정 최소, 18일 일정에 최적 |
| 언어 | **JavaScript** (JS 우선) | 둘 다 처음이면 JS로 시작 → 나중에 TS 전환 가능 |
| 라우팅 | **React Router v6** | 페이지 전환 |
| HTTP | **axios** | 인터셉터로 에러·로딩 공통 처리 |
| 스타일 | **Tailwind CSS** | 빠른 UI 구성, 클래스 재사용 |
| 상태 | **React useState/useEffect** (기본) | TanStack Query는 선택 사항 |

> 장민수님이 Node.js/npm 설치가 안 됐다면 오늘 먼저 해결하고 시작하세요. (아래 §7 셋업 참고)

---

## 2. 역할 분담 최종 확정

> 기준: "파일 단위로 담당이 갈리면 Git 충돌이 거의 없다" — 페이지 파일 = 담당자

### 민경이 담당 (핵심 서비스 플로우)

| 기능 | 페이지 파일 | 우선순위 |
|------|------------|---------|
| ① 반려동물 프로필 입력 | `ProfilePage.jsx` | 2순위 |
| ② 감정 체크인 | `EmotionPage.jsx` | 3순위 |
| ③ AI 추모 메시지 카드 | `MessagePage.jsx` | 4순위 |
| ⑦ 위험 감정 경고 모달 | `SafetyModal.jsx` | **1순위 (최우선)** |
| ⑧ 평가 리포트 | `ReportPage.jsx` | 마지막 |

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
| Vite 프로젝트 초기 세팅 | **민경이** (먼저 push → 장민수 pull) | 오늘 |
| 공통 컴포넌트 (`Button`, `Card`, `LoadingSpinner`) | **민경이** | 1주차 |
| axios 인스턴스 + Mock 데이터 | **민경이** | 1주차 |
| 앱 라우팅 (`App.jsx`) | **민경이** | 1주차 |

> ⚠️ `api/`, `components/`, `App.jsx` 는 공통 파일 — 수정할 때는 서로 미리 얘기하고 PR 올리기

---

## 3. 폴더 구조

```
frontend/
├── FRONTEND_PLAN.md       ← 이 파일
├── package.json
├── vite.config.js
├── index.html
└── src/
    ├── api/
    │   ├── axiosInstance.js   # baseURL, 헤더 공통 설정
    │   ├── pets.js            # /api/v1/pets 관련 함수
    │   ├── emotions.js        # /api/v1/emotions
    │   ├── messages.js        # /api/v1/messages
    │   ├── missions.js        # /api/v1/missions
    │   ├── timeline.js        # /api/v1/timeline
    │   ├── report.js          # /api/v1/report
    │   └── media.js           # /api/v1/media
    ├── components/
    │   ├── Button.jsx         # 공통 버튼
    │   ├── Card.jsx           # 공통 카드
    │   ├── LoadingSpinner.jsx # 로딩 표시
    │   └── SafetyModal.jsx    # 1393 경고 모달 (민경이, 최우선)
    ├── pages/
    │   ├── ProfilePage.jsx    # 민경이
    │   ├── EmotionPage.jsx    # 민경이
    │   ├── MessagePage.jsx    # 민경이
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
| 프로필 등록 | `POST` | `/api/v1/pets` | ProfilePage |
| 감정 체크인 | `POST` | `/api/v1/emotions` | EmotionPage |
| 메시지 생성 | `POST` | `/api/v1/messages/generate` | MessagePage |
| TTS 생성 | `POST` | `/api/v1/messages/{id}/tts` | TtsPage |
| 미션 조회 | `GET` | `/api/v1/missions?pet_id=` | MissionPage |
| 미션 완료 | `PATCH` | `/api/v1/missions/{id}` | MissionPage |
| 타임라인 | `GET` | `/api/v1/timeline/{pet_id}` | TimelinePage |
| 리포트 | `GET` | `/api/v1/report/{pet_id}` | ReportPage |
| 사진 업로드 | `POST` | `/api/v1/media/upload` | MediaPage |

### Mock 데이터 예시 (백엔드 전 임시 사용)

```js
// src/api/mock.js
export const mockPet = {
  _id: "pet_001",
  name: "콩이",
  species: "강아지",
  period: "2018-2026",
  memories: ["공원 산책", "간식 좋아함", "낮잠 자는 거 좋아함"],
  photo_url: null,
};

export const mockEmotion = {
  _id: "emo_001",
  pet_id: "pet_001",
  mood: "슬픔",
  note: "오늘 콩이 생각이 많이 났어",
  risk_flag: false,
};

export const mockMessage = {
  _id: "msg_001",
  pet_id: "pet_001",
  content: "콩이는 당신과 함께한 모든 순간을 소중히 간직하고 있을 거예요. 공원 산책도, 함께한 낮잠도 모두 아름다운 기억입니다.",
  tone: "따뜻함",
};

export const mockMissions = [
  { _id: "mis_001", title: "오늘 5분 산책하기", done: false },
  { _id: "mis_002", title: "콩이 사진 1장 꺼내보기", done: false },
  { _id: "mis_003", title: "좋아하는 음악 듣기", done: true },
];

export const mockTimeline = [
  { _id: "tl_001", type: "emotion", ref_id: "emo_001", created_at: "2026-06-01" },
  { _id: "tl_002", type: "message", ref_id: "msg_001", created_at: "2026-06-02" },
];
```

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
2. 성공 → `pet_id` 저장 (localStorage 또는 상태) → EmotionPage로 이동
3. 실패 → 에러 메시지 표시

**상태 관리:**
```js
const [form, setForm] = useState({
  name: '', species: '강아지', period: '', memories: [], photo: null
});
const [petId, setPetId] = useState(null); // 저장 후 이 ID로 이후 API 호출
```

---

### ② EmotionPage — 감정 체크인 (민경이)

**UI:**
- 오늘 기분을 선택하세요 (이모지 버튼 5개)
  - 😊 괜찮아요 / 😔 슬퍼요 / 😢 많이 힘들어요 / 😰 너무 힘들어요 / 😶 잘 모르겠어요
- 선택한 감정 텍스트 + 선택적 메모 입력칸

**위험 감정 처리 (핵심!):**
```js
const RISK_MOODS = ['너무 힘들어요']; // 백엔드에서도 감지하지만 프론트 선제 처리

async function handleSubmit() {
  const response = await postEmotion({ mood, note, pet_id });
  if (response.risk_flag || RISK_MOODS.includes(mood)) {
    setSafetyOpen(true); // 모달 띄우기
    return; // 다음 화면으로 자동 이동하지 않음
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

**주의:** "반려동물인 척" 하는 메시지 형태 금지 (ARCHITECTURE 8번 원칙)
- ✅ "콩이와 함께한 공원 산책은..."
- ❌ "안녕 나 콩이야, 잘 지내?"

---

### ④ TtsPage — 음성 낭독 (장민수)

**UI:**
- 톤 선택: [따뜻하게 / 차분하게 / 부드럽게] 버튼
- 선택 후 [낭독 시작] 버튼
- 오디오 플레이어 (재생/일시정지/음량)

**API 연동:**
```js
// POST /api/v1/messages/{id}/tts → { audio_url: "..." } 응답
const response = await generateTts({ message_id, tone });
setAudioUrl(response.audio_url);
// <audio src={audioUrl} controls />
```

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
- 감정 변화 그래프 (간단한 막대 or 선 그래프)
  - 라이브러리: `recharts` (npm install recharts)
- 미션 완료율 (%)
- 추모 메시지 생성 횟수

---

## 6. 일정표 (D-17, 2026-06-02 ~ 06-19)

### 1주차 (6/2~6/8) — 세팅 + 핵심 기능

| 날짜 | 민경이 할 일 | 장민수 할 일 |
|------|------------|------------|
| **6/2 (오늘)** | Vite 프로젝트 생성 + push | 세팅 파일 pull + 환경 세팅 |
| 6/3 | SafetyModal 완성 (최우선) | TtsPage 레이아웃 잡기 |
| 6/4 | ProfilePage 완성 | MissionPage 카드 UI |
| 6/5 | EmotionPage + SafetyModal 연결 | TimelinePage 레이아웃 |
| 6/6~8 | MessagePage (로딩+카드) | 각 페이지 마무리 |

### 2주차 (6/9~6/15) — API 연동

| 날짜 | 할 일 |
|------|------|
| 6/9~10 | 백엔드 API 확인 + axiosInstance 연동 시작 |
| 6/11~12 | Mock 데이터 → 실제 API로 교체 (기능별로) |
| 6/13~15 | 위험 감정 플로우 전체 테스트 + 버그 수정 |

### 3주차 (6/16~6/19) — 통합 + 발표 준비

| 날짜 | 할 일 |
|------|------|
| 6/16~17 | 전체 플로우 연결 테스트 (프로필→감정→메시지→미션) |
| 6/18 | 디자인 통일, 에러/로딩 처리, 모바일 대응 |
| 6/19 | 발표 리허설, 데모 환경 점검 |

---

## 7. 오늘(6/2) 당장 해야 할 것

### 민경이 — Vite 프로젝트 세팅 (1~2시간)

```bash
# 1. frontend 폴더에서 실행
cd C:\Users\kysop\Team_Rainbow_Bridge\Rainbow-Bridge\frontend

# 2. Vite 프로젝트 생성 (현재 폴더에)
npm create vite@latest . -- --template react
# → 덮어쓰기 여부 물으면 y

# 3. 의존성 설치
npm install

# 4. Tailwind CSS 설치
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 5. axios + react-router-dom 설치
npm install axios react-router-dom

# 6. 개발 서버 실행 확인
npm run dev
# 브라우저에서 http://localhost:5173 열려야 함

# 7. Tailwind 설정 — tailwind.config.js 수정
# content: ["./index.html", "./src/**/*.{js,jsx}"] 로 변경

# 8. src/index.css 맨 위에 추가
# @tailwind base;
# @tailwind components;
# @tailwind utilities;
```

### 장민수 — 세팅 완료 후 (민경이 push 기다렸다가)

```bash
# 민경이가 push 하면:
git checkout jangminsu
git merge dev    # dev에 민경이 PR 머지된 후

cd frontend
npm install      # package.json 기반 의존성 설치
npm run dev      # 실행 확인
```

---

## 8. 충돌 방지 규칙

1. **`pages/` 파일은 본인 담당만 수정** — 남의 파일 건드리면 반드시 먼저 알리기
2. **`components/`, `api/`, `App.jsx` 수정 시** — 카톡/슬랙으로 먼저 공지
3. **PR 단위**: 기능 하나 완성되면 바로 PR (한 번에 모아서 올리지 말 것)
4. **PR base는 항상 `dev`** — `main` 아님!
5. 막히면 5분 혼자 시도 후 바로 팀 채널 질문

---

## 9. 공통 컴포넌트 스펙 (민경이가 먼저 만들기)

```jsx
// components/Button.jsx
// props: children, onClick, variant("primary"|"danger"|"ghost"), disabled
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

> 폰트: 기본 시스템 폰트 사용. 나눔고딕 등 한글 폰트 추가 시 팀과 상의.

---

## 참고 문서

- [ARCHITECTURE.md](../docs/ARCHITECTURE.md) — API 경로·데이터 모델 확인
- [CONTRIBUTING.md](../docs/CONTRIBUTING.md) — PR·커밋 규칙
- [GIT_GUIDE.md](../docs/GIT_GUIDE.md) — Git 명령어
- [PROGRESS.md](../docs/PROGRESS.md) — 기능 완료 시 상태 업데이트 필수
