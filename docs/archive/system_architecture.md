# 시스템 구성도 — 레인보우 브릿지

> System Architecture · 발표용 인프라 구성도

```mermaid
graph TB
    subgraph USER["👤 사용자"]
        Browser[웹 브라우저 / 모바일]
    end

    subgraph NCP["☁️ NCP 클라우드 서버 (101.79.19.87)"]
        nginx["🔒 nginx\nHTTPS · Let's Encrypt\nrainbow-bridge.duckdns.org"]
        
        subgraph DOCKER["🐳 Docker Compose"]
            backend["⚙️ FastAPI 백엔드\n:8000"]
            mongo[("🍃 MongoDB\n서비스 데이터")]
        end
        
        sqlite[("🗄️ SQLite\n사용자 인증")]
        static["📁 정적 파일\nuploads/ tts/ videos/"]
    end

    subgraph EXTERNAL["🌐 외부 API"]
        gemini["🤖 Gemini API\n추모 메시지 · 위기 감지"]
        gcp_tts["🔊 Google Cloud TTS\n음성 합성"]
        perso["🎬 PERSO API\n영상 립싱크"]
        kakao["📍 카카오맵 API\n동물병원 검색"]
    end

    subgraph AI_SERVER["🖥️ AI / GPU 서버"]
        chromadb["🔍 ChromaDB\nRAG 벡터DB"]
        liveportrait["🐾 LivePortrait\n사진→영상 RTX 5060"]
    end

    subgraph CICD["⚙️ CI/CD"]
        github["GitHub Actions\ndev 머지 → 자동 배포"]
    end

    Browser -->|HTTPS| nginx
    nginx -->|/api/ 프록시| backend
    nginx -->|정적 서빙| static
    backend --- mongo
    backend --- sqlite
    backend --- static
    backend -->|LLM 호출| gemini
    backend -->|음성 합성| gcp_tts
    backend -->|영상 더빙| perso
    backend -->|병원 검색| kakao
    backend -->|RAG 검색| chromadb
    backend -->|영상 생성| liveportrait
    github -->|자동 배포| NCP

    style NCP fill:#f5f3ff,stroke:#7c3aed
    style EXTERNAL fill:#ecfdf5,stroke:#059669
    style AI_SERVER fill:#fff7ed,stroke:#ea580c
    style CICD fill:#eff6ff,stroke:#2563eb
    style USER fill:#fdf4ff,stroke:#a21caf
```

## 인프라 현황

| 구성 요소 | 기술 | 상태 |
|-----------|------|------|
| 클라우드 서버 | NCP Ubuntu 24.04 | ✅ 운영 중 |
| HTTPS | DuckDNS + Let's Encrypt | ✅ |
| 컨테이너 | Docker Compose | ✅ |
| 자동 배포 | GitHub Actions (dev → NCP) | ✅ |
| LLM | Gemini API (gemini-2.5-flash) | ✅ |
| TTS | Google Cloud TTS + gTTS 폴백 | ✅ |
| RAG | ChromaDB + Gemini 임베딩 | ✅ |
| 영상 생성 | LivePortrait (RTX 5060) | 🟡 서버 설정 중 |
