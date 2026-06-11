# Expo SDK 52 → 54 업그레이드 트러블슈팅

작성일: 2026-06-11  
작성: 민경이 (프론트엔드)

---

## 0. 업그레이드 목적

강사님 요청에 따라 Expo SDK 버전을 **52 → 54**로 올리고, **Android + iOS 모두** Expo Go(App Store/Play Store 최신판)로 실행 가능하도록 환경을 맞췄습니다.

### 핵심 효과

| 항목 | SDK 52 (이전) | SDK 54 (현재) |
|------|-------------|-------------|
| iOS Expo Go 실행 | ❌ 불가 (App Store Expo Go가 SDK 52 미지원) | ✅ 가능 (최신 Expo Go가 SDK 54 지원) |
| Android Expo Go 실행 | APK 구버전 직접 설치 필요 | ✅ Play Store 최신판 바로 사용 |
| React Native 버전 | 0.76.7 | 0.77.2 |

---

## 1. 변경된 파일 목록

| 파일 | 변경 내용 |
|------|----------|
| `package.json` | 전체 패키지 버전 SDK 54 호환으로 업그레이드 |
| `app.json` | iOS ATS 예외 설정, Android cleartext 허용, expo-font 플러그인 추가 |
| `app/(app)/photos.jsx` | `MediaTypeOptions.Images` → `['images']` |
| `app/(app)/media.jsx` | `MediaTypeOptions.Images` → `['images']` |

---

## 2. 패키지 버전 변경 상세

| 패키지 | SDK 52 (이전) | SDK 54 (현재) | 비고 |
|--------|-------------|-------------|------|
| `expo` | ~52.0.47 | ~54.0.0 | 메이저 업 |
| `react-native` | 0.76.7 | 0.77.2 | 메이저 업 |
| `expo-router` | ~4.0.17 | ~6.0.24 | 메이저 업 |
| `expo-av` | ~15.0.2 | ~16.0.8 | 메이저 업 |
| `expo-font` | ~13.0.4 | ~14.0.12 | 메이저 업 |
| `expo-image-picker` | ~16.0.6 | ~17.0.11 | 메이저 업 |
| `expo-linear-gradient` | ~14.0.2 | ~15.0.8 | 메이저 업 |
| `expo-linking` | ~7.0.5 | ~8.0.12 | 메이저 업 |
| `expo-splash-screen` | ~0.29.22 | ~31.0.13 | 메이저 업 |
| `expo-status-bar` | ~2.0.1 | ~3.0.9 | 메이저 업 |
| `expo-constants` | ~17.0.8 | ~18.0.13 | 메이저 업 |
| `react-native-safe-area-context` | 4.12.0 | ~5.6.0 | 메이저 업 |
| `react-native-screens` | ~4.4.0 | ~4.16.0 | 마이너 업 |
| `react-native-svg` | 15.8.0 | 15.12.1 | 마이너 업 |
| `@react-native-async-storage/async-storage` | 2.1.0 | 2.2.0 | 마이너 업 |
| `@react-native-community/datetimepicker` | 8.2.0 | 8.4.4 | 마이너 업 |
| `babel-preset-expo` | ~12.0.0 | ~13.0.0 | 메이저 업 |

---

## 3. 트러블슈팅 — 발생한 오류 및 해결

### 오류 1: `@react-native-community/datetimepicker@8.3.2` 버전 없음

**현상**
```
npm error notarget No matching version found for @react-native-community/datetimepicker@8.3.2.
```

**원인**  
처음에 package.json에 `8.3.2`를 직접 입력했는데, 이 버전은 npm 레지스트리에 존재하지 않습니다.  
(8.3.0 → 8.4.0으로 건너뜀, 8.3.2 없음)

**해결**  
버전을 직접 지정하는 대신, `npx expo install` 명령을 사용하여 Expo가 SDK 54와 호환되는 정확한 버전(`8.4.4`)을 자동 선택하도록 함.

```bash
# ❌ 잘못된 방법 (버전 직접 지정)
npm install @react-native-community/datetimepicker@8.3.2

# ✅ 올바른 방법 (expo install이 자동 해결)
npx expo install @react-native-community/datetimepicker
```

---

### 오류 2: `ImagePicker.MediaTypeOptions.Images` deprecation 경고

**현상**  
SDK 54 / expo-image-picker 17.x에서 `MediaTypeOptions.Images`는 deprecated되어 경고 또는 오류 발생.

**원인**  
`expo-image-picker` 15.x 이후 `MediaTypeOptions` enum이 deprecated됐고, 17.x에서는 문자열 배열 방식이 권장됨.

**영향 파일**
- `app/(app)/photos.jsx`
- `app/(app)/media.jsx`

**해결**  
```jsx
// ❌ 이전 (deprecated)
mediaTypes: ImagePicker.MediaTypeOptions.Images,

// ✅ 수정 후
mediaTypes: ['images'],
```

---

### 오류 3 (예상): expo-router 4.x → 6.x 메이저 업 호환성

**현상**  
`expo-router`가 `~4.0.17` → `~6.0.24`로 두 메이저 버전 올라감.

**위험도**: 낮음 — 기본 라우팅 API(`Stack`, `router`, `Redirect`, `useRouter`)는 호환 유지됨.

**실행 시 오류가 난다면 확인할 것**

1. `_layout.jsx`에서 Stack 설정이 올바른지 확인
2. `router.push()`, `router.navigate()`, `router.replace()` 동작 확인
3. `(auth)`, `(app)` 그룹 라우팅 정상 동작 확인

```bash
# 캐시 지우고 재시작
npx expo start -c
```

---

### 오류 4 (예상): expo-av 16.x — Video/Audio API 변경

**현상**  
expo-av 15.x → 16.x에서 `Video` 컴포넌트가 deprecated(권장: `expo-video` 별도 패키지로 이관).

**위험도**: 낮음 — expo-av 16.x는 `Video`, `Audio`, `ResizeMode` 여전히 export함. 완전 제거는 SDK 55+ 예정.

**당장 코드 변경 불필요**, 아래 경고 메시지는 정상임:
```
[expo-av] Video component will be removed in a future version of expo-av. Please migrate to expo-video.
```

**만약 실제 오류가 발생하면**: `expo-video` 패키지로 마이그레이션 필요
```bash
npx expo install expo-video
```

---

### 오류 5 (예상): Metro 번들러 캐시 충돌

**현상**  
SDK 업그레이드 후 `npx expo start` 시 에러 또는 이전 캐시 충돌.

**해결**
```bash
# 캐시 완전 클리어 후 재시작
npx expo start -c

# 또는 (Android)
npx expo start --android --clear

# 또는 (iOS)
npx expo start --ios --clear
```

---

### 오류 6 (예상): react-native-safe-area-context 4.x → 5.x

**현상**  
`react-native-safe-area-context` 4.12.0 → 5.6.0으로 메이저 업.

**위험도**: 매우 낮음 — v5.x는 v4.x와 API 완전 호환.  
`SafeAreaView`, `SafeAreaProvider`, `useSafeAreaInsets` 사용 방식 동일.

---

## 4. iOS 실행 가이드 (SDK 54 기준)

### 사전 조건
- iPhone에 **App Store 최신 Expo Go** 설치
- 개발 PC와 iPhone이 **같은 Wi-Fi** 연결
- 백엔드 서버: 이미 HTTPS (`https://rainbow-bridge.duckdns.org`) → iOS ATS 정책 자동 충족 ✅

### 실행 방법
```bash
cd frontend-rn
npx expo start

# QR 코드를 iPhone 카메라(iOS 16+) 또는 Expo Go 앱으로 스캔
```

> SDK 52 때와 달리, **APK 구버전 설치 없이** 최신 App Store Expo Go로 바로 실행됩니다.

---

## 5. Android 실행 가이드 (SDK 54 기준)

### 사전 조건
- Android에 **Play Store 최신 Expo Go** 설치 (구버전 APK 불필요)
- 개발 PC와 Android가 **같은 Wi-Fi** 연결

### 실행 방법
```bash
cd frontend-rn
npx expo start

# QR 코드를 Expo Go 앱으로 스캔
```

---

## 6. 업그레이드 후 재설치 절차 (정리)

SDK 업그레이드 또는 node_modules 문제가 생겼을 때의 클린 재설치 순서:

```bash
# 1. node_modules 및 lock 파일 삭제
# Windows PowerShell:
Remove-Item -Recurse -Force node_modules
Remove-Item -Force package-lock.json

# 2. 설치
npm install

# 3. expo 호환 패키지 자동 업데이트 (버전 맞춤)
npx expo install --fix

# 4. 캐시 클리어 후 실행
npx expo start -c
```

---

## 7. 알려진 경고 (무시해도 됨)

| 경고 메시지 | 원인 | 무시 가능? |
|------------|------|----------|
| `[expo-av] Video component will be removed...` | expo-av 16.x에서 Video deprecated | ✅ SDK 54에서는 동작함 |
| `npm warn ERESOLVE overriding peer dependency` | 일부 패키지 peer dep 느슨한 선언 | ✅ 정상 설치됨 |
| `14 moderate severity vulnerabilities` | React Native 생태계 내 간접 의존성 | ✅ 앱 보안과 무관 (개발 환경) |

---

*참고: Expo SDK 54 공식 릴리즈 노트 — [expo.dev/changelog](https://expo.dev/changelog)*
