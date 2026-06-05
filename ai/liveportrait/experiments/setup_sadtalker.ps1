# setup_sadtalker.ps1 — SadTalker 립싱크 비교 실험용 설치 (Windows / 정환주 GPU 서버)
#
# 용도: 장민수님 립싱크 비교 실험(방법4). LivePortrait conda 환경과 격리된
#       별도 env 에 설치 → 작동 중인 LivePortrait 의존성 안 깨짐.
#
# ⚠️ 실행 전 읽기:
#   - 골자입니다. 단계별 성공 확인하며 수동 진행 권장.
#   - ❗ SadTalker README 는 torch 1.12.1 + CUDA 11.3 을 권장하나, RTX 5060(신형
#     Blackwell)은 이 구버전 CUDA 와 호환 안 됨(sm_120 미지원). → RTX 5060 호환
#     torch(CUDA 12.x 대응)로 설치해야 함. 버전은 호환 확인 후 결정 — 못박지 않음.
#   - 모델 다운로드의 download_models.sh 는 bash 스크립트 → Windows 는 수동 다운로드.
#   - clone/모델 위치는 레포 밖 작업 폴더 권장(대용량, git 커밋 금지).

$ErrorActionPreference = "Stop"
$WORK = "C:\Rainbow_Bridge\_experiments"   # ← 레포 밖. 환주님 환경에 맞게 변경
New-Item -ItemType Directory -Force -Path $WORK | Out-Null
Set-Location $WORK

# 1) 격리 conda env
conda create -y -n sadtalker python=3.8
conda activate sadtalker

# 2) clone + 의존성
git clone https://github.com/OpenTalker/SadTalker
Set-Location SadTalker
# ⚠️ torch 는 requirements.txt 의 1.12.1+cu113 대신 RTX 5060 호환 버전 먼저 설치 권장.
#    예) https://pytorch.org 에서 CUDA 12.x 대응 torch 설치 후 → 나머지:
pip install -r requirements.txt

# 3) 모델 다운로드 (Windows = 수동. download_models.sh 는 Linux/macOS 용)
#    Google Drive / GitHub Releases / Baidu(pw: sadt) 에서 받아 압축 해제:
#      → checkpoints\   및   gfpgan\
#    릴리스: https://github.com/OpenTalker/SadTalker/releases
New-Item -ItemType Directory -Force -Path "checkpoints" | Out-Null
New-Item -ItemType Directory -Force -Path "gfpgan" | Out-Null
Write-Host "▶ checkpoints\ 와 gfpgan\ 에 모델 수동 배치 후 추론 실행하세요." -ForegroundColor Yellow

# 4) 추론 (입력: 얼굴 이미지/영상 + 음성)
#    python inference.py --driven_audio <음성.wav> --source_image <얼굴.png> `
#        --enhancer gfpgan --result_dir results
#    → 결과: results\<timestamp>\*.mp4
