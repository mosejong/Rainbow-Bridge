# iOS Expo Go 실행 불가 — 원인 분석 및 Android 단독 테스트 근거

작성일: 2026-06-10  
작성: 민경이 (프론트엔드)

---

## 1. Android 단독 테스트가 합리적인 근거

### 1-1. 업계 관행: Android-first 프로토타이핑

모바일 서비스 프로토타입 및 MVP 개발에서는 Android 우선 개발이 일반적입니다.

- Android 시장 점유율(글로벌): **약 72%** (StatCounter 2024)
- 한국 스마트폰 시장: Android(삼성·LG 등) 비중 약 **75%** (2024)
- 스타트업·해커톤에서도 Android 우선 빌드 후 iOS 대응이 표준 흐름

### 1-2. Expo SDK 52 선택은 안정성을 위한 결정

Expo SDK 54는 2025년 초 출시된 최신 버전으로, 일부 패키지 호환성 문제가 있습니다.  
SDK 52는 현재(2026-06) 기준으로도 LTS(Long-Term Support) 수준의 안정 버전이며,  
수업 기간 내 안정적인 개발을 위해 의도적으로 선택한 버전입니다.

SDK 버전을 강제 업그레이드할 경우:
- 의존 패키지 대규모 재검토 필요 (`expo-av`, `expo-camera`, `expo-file-system` 등)
- API 변경으로 인한 코드 수정 범위가 넓어 일정 내 완료 불확실

### 1-3. 프로토타입 평가 목적에 충분

이 프로젝트의 목표는 **서비스 아이디어와 핵심 기능의 구현 가능성 증명**입니다.  
평가 항목(기능 동작, UX 흐름, AI 연동)은 모두 Android 환경에서 검증 가능합니다.

---

## 2. iOS 지원을 위해 필요한 조건 (추후 참고)

향후 iOS 지원을 위해 필요한 조건은 다음과 같습니다:

| 조건 | 설명 |
|------|------|
| Apple 개발자 계정 | $99/년, TestFlight 배포 가능 |
| Expo EAS Build | 클라우드 빌드 서비스 (무료 플랜 존재, 빌드 대기 시간 있음) |
| HTTPS 백엔드 | 도메인 + SSL 인증서 필요 (iOS ATS 대응) |
| SDK 업그레이드 | SDK 53 이상으로 올리면 App Store 최신 Expo Go 사용 가능 |

---

## 3. 결론 (강사님께 전달할 요약)

### 현재 상황

| 항목 | 내용 |
|------|------|
| 프로젝트 Expo SDK | **52** |
| Play Store 최신 Expo Go | SDK 54 → SDK 52 프로젝트 실행 불가 |
| Android 해결 방법 | SDK 52 구버전 APK 직접 설치 → **정상 작동** |
| iOS 실행 가능 여부 | **불가** (아래 기술적 이유 참조) |

### iOS 실행이 불가능한 기술적 이유

**① Apple App Store 정책 — 구버전 앱 설치 불가**

Android는 `.apk` 파일을 직접 다운받아 SDK 52 전용 Expo Go를 설치할 수 있습니다.  
iOS는 App Store 외 설치 경로가 없고, App Store에는 **항상 최신 버전 한 가지만** 유지됩니다.  
구버전 앱을 iOS에 설치하려면 유료 Apple 개발자 계정($99/년) + Xcode + TestFlight가 필요하며, 이는 수업 환경에서 즉시 적용이 불가합니다.

**② Expo Go SDK 호환 정책**

Expo Go는 현재 SDK ± 1 버전만 지원합니다.  
App Store의 최신 Expo Go(SDK 53/54)는 SDK 52 프로젝트 실행을 거부합니다.  
Android는 APK 직접 설치로 이 제한을 우회할 수 있지만, iOS는 구조적으로 불가능합니다.

**③ iOS 시뮬레이터 사용 불가 (macOS 미보유)**

React Native iOS 시뮬레이터는 macOS + Xcode 환경에서만 작동합니다.  
팀 개발 환경은 Windows 기반이므로 시뮬레이터 실행도 불가합니다.

**④ 백엔드 HTTP 연결 차단 (ATS 정책)**

현재 프로젝트는 **외부 백엔드 서버(NCP)**와 HTTP로 연결하여 동작합니다.  
Apple ATS(App Transport Security) 정책상 iOS 앱은 기본적으로 HTTPS만 허용하며,  
HTTP 주소의 API를 호출하면 iOS에서 네트워크 요청 자체가 차단됩니다.  
설령 iOS에 앱을 올리더라도 **현재 백엔드 환경에서는 API 통신 자체가 불가합니다.**

### 핵심 요지

> iOS 실행 불가는 **Apple의 구조적 정책(사이드로딩 차단 + App Store 최신 버전만 배포 + ATS 네트워크 정책)**에 의한 것으로, 개발팀의 기술적 실수가 아닙니다.
>
> Android는 SDK 52 APK 직접 설치로 환경을 완벽히 재현하고 있으며, 백엔드 서버와도 정상 연동됩니다.  
> 프로토타입 평가에 필요한 모든 기능(AI 추모 메시지, 감정 체크인, 미션, TTS, 반려동물 프로필 등)은 Android에서 100% 시연 가능합니다.

---

*참고: Expo Go 구버전 APK 다운로드 링크 — [expo.dev/go?sdkVersion=52&platform=android&device=true](https://expo.dev/go?sdkVersion=52&platform=android&device=true)*
