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

### ⚠️ 중요 — Expo Go 버전 주의

> 이 프로젝트는 **Expo SDK 52** 입니다.
> Play Store 최신 Expo Go(SDK 54)와 **버전이 맞지 않아 앱이 열리지 않습니다.**
> 반드시 아래 방법으로 **SDK 52 전용 APK** 를 설치하세요.

#### Android — SDK 52 Expo Go APK 설치 방법

1. **기존 Expo Go 삭제** (이미 설치돼 있으면)
2. 폰 브라우저에서 아래 주소 접속:
   ```
   expo.dev/go?sdkVersion=52&platform=android&device=true
   ```
3. **Download** 버튼 눌러서 `Expo-Go-2.32.20.apk` 다운로드
   - "File might be harmful" 경고 → **Download anyway** 선택
4. 다운로드 완료 후 APK 파일 눌러서 설치
   - "출처를 알 수 없는 앱" 팝업 → **설정** → 크롬 허용 → 뒤로 가서 설치
5. 설치된 Expo Go 열기 → **Scan QR** → 터미널 QR 스캔

#### iOS

iOS는 APK 설치가 불가합니다. 현재 iOS에서는 테스트가 어렵습니다.

---

### 준비물
- PC와 폰이 **같은 WiFi** 에 연결돼 있어야 해요

### 순서

**1) 위 방법으로 SDK 52 Expo Go APK 설치**

**2) `npx expo start --clear` 실행**
터미널에 QR 코드가 뜹니다.

**3) QR 스캔**
- Expo Go 앱 열기 → `Scan QR` 탭해서 스캔

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

## 팀원 공지 (2026-06-09 기준)

> 아래 내용을 팀 카톡/슬랙에 그대로 복붙해서 공유하세요.

---

**📢 프론트 앱 테스트 방법 안내 (필독)**

프로젝트가 **Expo SDK 52** 라서 Play Store 최신 Expo Go(SDK 54)로는 앱이 열리지 않아요.
최신 Expo Go(SDK 54)로 버전 맞춰서 프로젝트 버전을 올렸지만 버전 충돌 오류가 몇 시간째 계속 해결이 되지 않아서
Expo Go(SDK 54)를 Expo Go(SDK 52)버전 낮추었습니다.
반드시 **구버전 APK**를 따로 설치해야 합니다.

**Android 설치 순서:**
1. 기존 Expo Go 삭제
2. 폰 브라우저에서 접속:
   `expo.dev/go?sdkVersion=52&platform=android&device=true`
3. Download 버튼 → "Download anyway" 선택
4. 다운로드된 APK 파일 눌러서 설치
   (설치 허용 팝업 뜨면 허용)
5. 설치된 Expo Go 열고 QR 스캔

**역할별 할 일:**

| 대상 | 할 일 |
|------|-------|
| **민경이 (프론트 담당)** | 아래 명령어로 서버 켜기 → QR 공유 |
| **나머지 팀원** | Expo Go APK 설치 후 QR 스캔만 하면 됨 |

**민경이 PC에서 서버 켜는 법:**
```
cd frontend-rn
npx expo start --clear
```
QR코드가 뜨면 캡처해서 팀원들에게 공유하세요!

> 처음 클론했거나 `node_modules`가 없으면 먼저 `npm install --legacy-peer-deps` 실행 후 위 명령어 실행하세요.

⚠️ iOS는 현재 테스트 불가합니다.
궁금한 점은 민경이에게 문의해주세요!

---

## 주의사항

- `SafetyModal` 의 **1393** 번호는 절대 변경 금지입니다
- `.env` 파일은 절대 커밋하지 마세요 (`.gitignore` 에 등록됨)
- 프론트 작업은 **`frontend-rn/`** 에서만 하세요
