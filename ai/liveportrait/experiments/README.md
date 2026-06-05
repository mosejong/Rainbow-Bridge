# 립싱크 비교 실험 — 설치 스크립트

> 장민수님 립싱크 비교 실험 지원(GPU 자원: 정환주). LivePortrait(방법3, env)와
> 별개로 **Wav2Lip(방법1)·SadTalker(방법4)** 를 비교하기 위한 설치 골자.
> `ai/liveportrait/` 는 장민수 담당 영역 — 스크립트 위치는 합의 후 조정 가능.

## ⚠️ 공통 주의

- **격리 conda env 필수.** `base`·`liveportrait` 환경 건드리지 않음 — 의존성 충돌이
  작동 중인 LivePortrait 추론(서버)을 깨뜨릴 수 있음. 각각 `wav2lip`·`sadtalker` env.
- **RTX 5060(신형 Blackwell) 호환 주의.** 두 repo 모두 구버전 torch/CUDA 권장값을 적음:
  - Wav2Lip: README Python 3.6
  - SadTalker: torch 1.12.1 + CUDA 11.3 → **sm_120 미지원, RTX 5060 에서 안 돌 수 있음**
  → torch 는 RTX 5060 호환 버전(CUDA 12.x 대응)으로 별도 설치 후 나머지 핀 완화. 버전 못박지 않음.
- **모델 가중치는 수동 다운로드.** Wav2Lip 은 저자 외부 링크, SadTalker 는 Windows 에서
  `download_models.sh`(bash) 대신 릴리스 수동 다운로드. 스크립트가 폴더만 만들고 안내.
- **VRAM:** 현재 6GB 여유 → 두 모델 **동시 로드 말고 순차 실행**.
- **clone·모델·결과물은 레포 밖 작업 폴더**(`$WORK`)에. 대용량 → git 커밋 금지.

## 파일

| 파일 | 내용 |
|------|------|
| [setup_wav2lip.ps1](setup_wav2lip.ps1) | Wav2Lip env·clone·의존성·모델 안내(체크포인트 + s3fd 얼굴검출 둘 다 필수) |
| [setup_sadtalker.ps1](setup_sadtalker.ps1) | SadTalker env·clone·의존성·모델 안내(checkpoints/·gfpgan/) |

## 실행 (환주님이 여유 때, 단계별 확인하며)

```powershell
# 둘 다 비교하려면 각각 실행. $WORK 경로는 스크립트 안에서 본인 환경에 맞게 수정.
powershell -ExecutionPolicy Bypass -File .\setup_wav2lip.ps1
powershell -ExecutionPolicy Bypass -File .\setup_sadtalker.ps1
```

설치 후 입력 파일(얼굴 영상/이미지 + 음성)은 장민수님이 전달 → 각 repo `inference.py`
명령(스크립트 하단 주석 참고)으로 결과 추출.

## 비교 관점 (참고)

- **LivePortrait(현행):** 무음 추모 영상(입 거의 안 움직임, driving_multiplier 로 톤 조절).
- **Wav2Lip:** 입 모양 정확도 높음. 단 해상도·화질 제약.
- **SadTalker:** 머리 움직임+표정 포함. 무거움.

> 윤리 경계([../README.md](../README.md) §0) 동일 적용 — 립싱크 결과도 반려동물 1인칭 대화처럼
> 만들지 않고, "기억 기반 AI 재해석 추모" 라벨·사용자 선택 전제. 위기(risk_level 2+) 사용 금지.
