# 레인보우 브릿지 — 프론트엔드 (React Native + Expo)

> **⚠️ 프론트엔드는 `frontend-rn/` 에서 작업하세요.**
> `frontend/` 는 구버전(Vite+React)이며 더 이상 사용하지 않습니다.

---

## 빠른 시작

### 1. 패키지 설치

```bash
cd frontend-rn
npm install --legacy-peer-deps
```

### 2. 환경변수 설정

`frontend-rn/.env` 파일을 만들어요 (없으면 직접 생성):

```
EXPO_PUBLIC_API_URL=http://<내 PC IP>:8000
```

**내 PC IP 확인:**
- Windows PowerShell: `ipconfig | Select-String "IPv4"`
- Mac/Linux: `ifconfig | grep "inet "`

> ⚠️ `localhost` 는 폰에서 안 됩니다. 반드시 실제 IP를 써야 해요.

### 3. 백엔드 실행 (Docker)

```bash
cd ..   # 루트 폴더로
docker compose -f backend/docker-compose.yml up -d
```

`rainbow_backend`, `rainbow_mongo`, `rainbow_redis` 세 개가 Running 이면 OK.
확인: 브라우저에서 `http://localhost:8000/health` → `{"status":"ok"}` 뜨면 성공.

### 4. Expo 개발 서버 시작

```bash
cd frontend-rn
npx expo start --clear
```

---

## 폰에서 실제 앱 확인하기 (Expo Go)

### 준비물
- PC와 폰이 **같은 WiFi** 에 연결돼 있어야 해요

### 순서

**1) 폰 Play Store / App Store 에서 "Expo Go" 설치**

**2) `npx expo start --clear` 실행**
터미널에 QR 코드가 뜹니다.

**3) QR 스캔**
- Android: Expo Go 앱 열기 → `Scan QR code` 탭해서 스캔
- iOS: 기본 카메라 앱으로 스캔

앱이 자동으로 폰에 로드됩니다!

**코드 수정 시 폰에 자동 반영** (저장하면 바로 업데이트)

### 같은 WiFi 없을 때 (학교·카페 공용 WiFi)

```bash
npx expo start --tunnel
```

인터넷 경유로 연결됩니다 (다소 느림).

---

## 폴더 구조

```
frontend-rn/
├── app/
│   ├── _layout.jsx          # 루트 레이아웃
│   ├── index.jsx            # 진입점 → /login 리다이렉트
│   ├── (auth)/
│   │   ├── login.jsx        # 로그인
│   │   └── register.jsx     # 회원가입
│   └── (app)/
│       ├── profile.jsx      # 반려동물 프로필
│       ├── emotion.jsx      # 감정 체크인
│       ├── message.jsx      # 추모 메시지
│       ├── tts.jsx          # TTS 음성 재생
│       ├── mission.jsx      # 일상 복귀 미션
│       ├── timeline.jsx     # 추모 타임라인
│       ├── report.jsx       # 감정 리포트
│       ├── funeral.jsx      # 장례 안내
│       ├── symptoms.jsx     # 증상 안내
│       ├── health-records.jsx # 투약·검진 기록
│       ├── memories.jsx     # 추억 키워드
│       └── media.jsx        # 추모 영상
├── api/                     # 백엔드 API 호출
├── components/              # 공통 컴포넌트 (Button, Card, SafetyModal 등)
├── constants/
│   └── colors.js            # 파스텔 색상 팔레트
└── assets/images/           # 앱 아이콘·스플래시 이미지
```

---

## 색상 팔레트

| 이름 | 코드 | 용도 |
|------|------|------|
| background | `#F2EEE5` | 배경 (크림) |
| primary | `#E5C1C5` | 핑크 포인트 |
| secondary | `#C3E2DD` | 민트 포인트 |
| cta | `#6ECEDA` | 버튼·CTA |
| textPrimary | `#4A4458` | 본문 텍스트 |

---

## 주의사항

- `SafetyModal` 의 **1393** 번호는 절대 변경 금지입니다
- `.env` 파일은 절대 커밋하지 마세요 (`.gitignore` 에 등록됨)
- 프론트 작업은 **`frontend-rn/`** 에서만 하세요
