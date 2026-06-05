# setup_wav2lip.ps1 — Wav2Lip 립싱크 비교 실험용 설치 (Windows / 정환주 GPU 서버)
#
# 용도: 장민수님 립싱크 비교 실험(방법1). LivePortrait conda 환경과 격리된
#       별도 env 에 설치 → 작동 중인 LivePortrait 의존성 안 깨짐.
#
# ⚠️ 실행 전 읽기:
#   - 이 스크립트는 골자입니다. 각 단계 성공 확인하며 수동 진행 권장(특히 모델 다운로드).
#   - RTX 5060(신형 Blackwell) 은 Wav2Lip 의 구버전 의존성(README 기준 Python 3.6)과
#     호환이 안 될 수 있음 → 아래 Python/torch 버전은 호환 확인 후 조정. 못박지 않음.
#   - clone/모델 위치는 레포 밖 작업 폴더 권장(대용량, git 커밋 금지). $WORK 를 바꿔 쓰세요.

$ErrorActionPreference = "Stop"
$WORK = "C:\Rainbow_Bridge\_experiments"   # ← 레포 밖. 환주님 환경에 맞게 변경
New-Item -ItemType Directory -Force -Path $WORK | Out-Null
Set-Location $WORK

# 1) 격리 conda env (base/liveportrait 절대 건드리지 않음)
#    README 는 Python 3.6 이지만 신형 GPU 호환 위해 3.9 시도 → 안 되면 조정.
conda create -y -n wav2lip python=3.9
conda activate wav2lip

# 2) clone + 의존성
git clone https://github.com/Rudrabha/Wav2Lip
Set-Location Wav2Lip
pip install -r requirements.txt
# ⚠️ requirements 의 librosa/numpy/torch 가 신형 GPU·신 Python 과 충돌하기로 유명.
#    충돌 시: torch 를 RTX 5060 호환 버전으로 별도 설치 후 나머지 핀 완화.

# 3) 모델 (수동 다운로드 — 자동화 불가, 아래 링크에서 받아 배치)
#    (a) Wav2Lip+GAN 체크포인트(장민수님 요청 wav2lip_gan.pth):
#        https://drive.google.com/file/d/15G3U08c8xsCkOqQxE38Z2XXDnPcOptNk/view
#        → checkpoints\wav2lip_gan.pth
#    (b) ❗ 얼굴검출 모델도 필수(빠뜨리면 추론 실패):
#        https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth
#        → face_detection\detection\sfd\s3fd.pth
New-Item -ItemType Directory -Force -Path "checkpoints" | Out-Null
New-Item -ItemType Directory -Force -Path "face_detection\detection\sfd" | Out-Null
Write-Host "▶ 모델 2개를 위 경로에 수동 배치 후 추론 실행하세요." -ForegroundColor Yellow

# 4) 추론 (입력 파일은 장민수님이 전달: 얼굴 영상 + 음성)
#    python inference.py --checkpoint_path checkpoints\wav2lip_gan.pth `
#        --face <얼굴.mp4> --audio <음성.wav>
#    → 결과: results\result_voice.mp4
