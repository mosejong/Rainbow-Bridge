# 사용자 흐름도 — 레인보우 브릿지

> User Flow · 발표용 플로우차트

```mermaid
flowchart TD
    A([🔐 회원가입 / 로그인\nJWT · SQLite]) --> B{기존 펫\n있음?}

    B -- Yes --> D
    B -- No --> C[🐾 반려동물 프로필 등록\n이름 · 종 · 함께한 기간 · 추억 키워드]

    C --> D[💜 감정 체크인\n위기 감지 L0~L3 · 1393 안내]

    D --> E{risk_level\nL2 이상?}
    E -- Yes --> Z([🚨 1393 위기 라우팅\n자살예방상담전화 안내])
    E -- No --> F[📝 추모 메시지 생성\nGemini LLM · RAG few-shot]

    F --> G[🔊 TTS 낭독\nGoogle Cloud TTS · 톤 선택]

    G --> H{TTS\n완료?}
    H -- No --> G2([⚠️ 사진 업로드\n비활성화])
    H -- Yes --> I[🎬 추모 영상 만들기\n사진 업로드 → LivePortrait → 음성 합치기]

    I --> J[✅ 일상 복귀 미션\n오늘의 미션 추천 · 완료 체크]

    J --> K([📊 추모 타임라인 · 리포트\n회복 여정 기록])

    style Z fill:#fee2e2,stroke:#ef4444,color:#991b1b
    style G2 fill:#fef9c3,stroke:#eab308,color:#713f12
    style A fill:#ede9fe,stroke:#7c3aed
    style K fill:#d1fae5,stroke:#059669
```

## 핵심 분기

| 분기 | 조건 | 결과 |
|------|------|------|
| 기존 펫 있음 | 로그인 후 GET /pets 확인 | 감정 체크인 바로 이동 |
| 위기 감지 L2+ | risk_level ≥ 2 | 1393 즉시 안내, 메시지 생성 중단 |
| TTS 미완료 | tts_done localStorage 없음 | 사진 업로드 버튼 비활성화 |
