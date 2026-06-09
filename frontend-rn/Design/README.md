# 레인보우 브릿지 — 프론트엔드 디자인 가이드

> 참고 이미지: `frontend/Reset/PastelTone.jpg` (색상 기준), `frontend-rn/assets/3_White_Yoon.png` (캐릭터 마스코트)

---

## 색상 팔레트 (`constants/colors.js`)

앱 아이콘(고양이+강아지, 무지개 하늘)과 PastelTone.jpg를 기준으로 라벤더/보라 파스텔 톤으로 통일.

### 기본 색상

| 변수명 | HEX | 용도 | 미리보기 |
|--------|-----|------|----------|
| `background` | `#F0EBF8` | 전체 화면 배경 (소프트 라벤더) | ![](https://via.placeholder.com/20/F0EBF8/F0EBF8) |
| `primary` | `#D4B5DC` | 포인트 색상, 링크, 선택 상태 (더스티 퍼플-핑크) | |
| `secondary` | `#B8D0E8` | 보조 포인트 (소프트 스카이 블루) | |
| `cta` | `#9B8DC8` | 로그인·확인 등 주요 버튼 (소프트 미디엄 퍼플) | |
| `white` | `#FFFFFF` | 카드, 인풋 배경 | |
| `card` | `#FFFFFF` | 카드 컴포넌트 배경 | |
| `divider` | `#E5DCF0` | 구분선, 인풋 테두리 | |
| `inputBg` | `#F7F3FC` | 입력 필드 배경 | |

### 텍스트 색상

| 변수명 | HEX | 용도 |
|--------|-----|------|
| `textPrimary` | `#4A3F6B` | 제목, 본문 (딥 퍼플) |
| `textSecondary` | `#8B80A8` | 부제목, 보조 설명 (미디엄 퍼플) |
| `textLight` | `#C0B5D0` | 플레이스홀더, 비활성 텍스트 |

### 상태 색상

| 변수명 | HEX | 용도 |
|--------|-----|------|
| `danger` | `#E57373` | 오류, 경고 메시지 |
| `success` | `#7BC8A4` | 성공 상태 |
| `warning` | `#F4C97A` | 주의 상태 |

### 선택 상태 (감정 체크인 등)

| 변수명 | HEX | 용도 |
|--------|-----|------|
| `selected` | `#D4B5DC` | 선택된 항목 배경 |
| `selectedBorder` | `#B89BC8` | 선택된 항목 테두리 |
| `selectedText` | `#4A3F6B` | 선택된 항목 텍스트 |

---

## 사용법 예시

```js
import { COLORS } from '../../constants/colors';

// StyleSheet에서
const styles = StyleSheet.create({
  container: { backgroundColor: COLORS.background },
  button:    { backgroundColor: COLORS.cta },
  title:     { color: COLORS.textPrimary },
  input:     { borderColor: COLORS.divider, backgroundColor: COLORS.white },
});
```

---

## 캐릭터 이미지

| 파일 | 위치 | 용도 |
|------|------|------|
| `3_White_Yoon.png` | `frontend-rn/assets/3_White_Yoon.png` | 로그인 화면 상단 마스코트 |
| `2_White_Sister.png` | `frontend/assets/2_White_Sister.png` | 앱 아이콘 레퍼런스 이미지 |
| `PastelTone.jpg` | `frontend/Reset/PastelTone.jpg` | 색상 팔레트 레퍼런스 |

### 이미지 사용 예시 (login.jsx)

```jsx
<Image
  source={require('../../assets/3_White_Yoon.png')}
  style={{ width: 180, height: 180, borderRadius: 28 }}
  resizeMode="contain"
/>
```

---

## 레이아웃 원칙

- **배경**: 항상 `COLORS.background` (소프트 라벤더)
- **카드/인풋**: `COLORS.white` + 테두리 `COLORS.divider` + `borderRadius: 16`
- **주요 버튼**: `COLORS.cta` + `borderRadius: 16` + `paddingVertical: 16`
- **그림자**: `shadowColor: COLORS.cta`, `shadowOpacity: 0.3`, `elevation: 5`
- **간격**: 섹션 간 `gap: 12`, 헤더 마진 `marginBottom: 44`

---

## 화면별 적용 현황

| 화면 | 파일 | 색상 적용 | 이미지 적용 |
|------|------|-----------|-------------|
| 로그인 | `app/(auth)/login.jsx` | ✅ | ✅ `3_White_Yoon.png` |
| 회원가입 | `app/(auth)/register.jsx` | ✅ | — |
| 감정 체크인 | `app/(app)/emotion.jsx` | ✅ | — |
| 프로필 | `app/(app)/profile.jsx` | ✅ | — |
| 미션 | `app/(app)/mission.jsx` | ✅ | — |
| 타임라인 | `app/(app)/timeline.jsx` | ✅ | — |
| 추모 메시지 | `app/(app)/message.jsx` | ✅ | — |
| 리포트 | `app/(app)/report.jsx` | ✅ | — |
| 장례 안내 | `app/(app)/funeral.jsx` | ✅ | — |

---

## 색상 업데이트 이력

| 날짜 | 변경 내용 |
|------|-----------|
| 2026-06-08 | PastelTone.jpg + 앱 아이콘 기반 라벤더 파스텔 톤으로 전면 개편 (`background` 베이지→라벤더, `cta` 청록→소프트 퍼플) |
