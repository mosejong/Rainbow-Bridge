"""LivePortrait 추모 영상 생성 파이프라인.

반려동물 사진(source) + 모션 영상(driving) → 잔잔히 움직이는 추모 영상(MP4).

- 외부 LivePortrait 설치본(레포 밖)을 감싸는 얇은 래퍼입니다.
  모델 가중치·생성 영상은 이 레포에 포함하지 않습니다.
- `LIVEPORTRAIT_MODE` 로 로컬 GPU ↔ Replicate API 를 전환합니다.
  (AI 파트 provider 추상화와 같은 원칙 — 한쪽이 막히면 즉시 다른 쪽으로 시연)

⚠️ 윤리 경계: 반려동물이 말하는/대화하는 영상 ❌. 눈·코·입 미세 움직임 정도의
   상징적 추모 영상만 생성합니다. (README §0)

환경 변수(.env):
    LIVEPORTRAIT_MODE       local | remote | replicate   (기본 local)
    LIVEPORTRAIT_HOME       외부 LivePortrait 클론 경로 (local 모드, GPU 서버)
    LIVEPORTRAIT_DRIVING    기본 모션(driving) 영상 경로 (GPU 서버에 올린 영상)
    LIVEPORTRAIT_CONDA_ENV  conda 환경 이름      (기본 liveportrait)
    LIVEPORTRAIT_DRIVING_MULTIPLIER 모션 강도            (기본 0.4)
    LIVEPORTRAIT_REMOTE_URL remote 모드일 때 터널된 GPU 서비스 주소
                            (예: https://xxxx.ngrok.io) — 백엔드가 사용
    REPLICATE_API_TOKEN     replicate 모드일 때만

모드:
    local    — 이 머신의 GPU 로 직접 추론 (개발 PC / GPU 서버에서 server.py 가 호출)
    remote   — 터널된 GPU 서비스(server.py)에 HTTP 요청 (NCP 백엔드가 사용)
    replicate— Replicate 클라우드 fallback
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

# ---------- 설정 (환경 변수 → 기본값) ----------
MODE = os.getenv("LIVEPORTRAIT_MODE", "local")
LP_HOME = Path(os.getenv("LIVEPORTRAIT_HOME", r"c:\JMS\2_project\LivePortrait"))
CONDA_ENV = os.getenv("LIVEPORTRAIT_CONDA_ENV", "liveportrait")
REPLICATE_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")
# remote 모드: 터널된 GPU 서비스(server.py) 주소. 백엔드(NCP)가 이걸로 호출.
REMOTE_URL = os.getenv("LIVEPORTRAIT_REMOTE_URL", "").rstrip("/")

# 추모 영상에 어울리는 기본 모션(잔잔한 움직임). 추후 전용 템플릿으로 교체 예정.
# 서버 배포 대비: LIVEPORTRAIT_DRIVING 으로 경로 분리(없으면 LivePortrait 예제 d0).
# → 서버에선 driving 영상을 올리고 LIVEPORTRAIT_DRIVING 에 그 경로를 지정하세요.
DEFAULT_DRIVING = Path(
    os.getenv(
        "LIVEPORTRAIT_DRIVING",
        str(LP_HOME / "assets" / "examples" / "driving" / "d0.mp4"),
    )
)

# 모션 강도. 동물은 animation_region(eyes 등)이 무시되므로, driving_multiplier를
# 낮춰서 입 움직임을 억제하고 잔잔한 ambient 느낌을 냄. 0.4 = 입 거의 닫힘 + 눈/고개 미세.
# (검증 2026-06-04: 강아지·고양이·기타 7종 모두 0.4에서 잔잔한 추모 톤 확인)
DRIVING_MULTIPLIER = float(os.getenv("LIVEPORTRAIT_DRIVING_MULTIPLIER", "0.4"))


class LivePortraitError(RuntimeError):
    """파이프라인 실행 실패."""


def _find_ffmpeg() -> str:
    """ffmpeg 실행 파일 경로를 찾습니다.

    시스템 PATH에 ffmpeg가 있으면 그걸 쓰고, 없으면 imageio_ffmpeg가
    내장한 바이너리로 폴백합니다. (이 PC엔 시스템 ffmpeg가 없어 conda의
    imageio_ffmpeg 내장 ffmpeg를 사용 — 2026-06-05 확인)
    """
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg  # 지연 import (합치기 때만 필요)

        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as e:
        raise LivePortraitError(
            "ffmpeg를 찾을 수 없습니다. 시스템에 ffmpeg를 설치하거나 "
            "`pip install imageio-ffmpeg` 후 다시 시도하세요."
        ) from e


def merge_audio(
    video_path: str | Path,
    audio_path: str | Path,
    output_path: str | Path | None = None,
) -> Path:
    """무음 추모 영상 + 낭독 음성(mp3) → 음성 입힌 MP4. 결과 경로 반환.

    영상이 음성보다 짧으면 영상을 반복(loop)해 음성 길이에 맞춥니다.
    (추모 톤: 메시지 낭독 내내 반려동물 얼굴이 잔잔히 움직임)

    ⚠️ 윤리: 이 기본 파이프라인은 영상에 **오디오만 얹습니다(립싱크 없음).**
       PERSO 립싱크/더빙은 사용자 선택과 라벨을 전제로 한 별도 후처리 단계입니다.

    Args:
        video_path: LivePortrait 무음 영상(MP4)
        audio_path: TTS 낭독 음성(mp3)
        output_path: 결과 경로 (None이면 영상 옆에 `<stem>_voiced.mp4`)
    """
    video_path = Path(video_path)
    audio_path = Path(audio_path)

    if not video_path.exists():
        raise FileNotFoundError(f"영상 없음: {video_path}")
    if not audio_path.exists():
        raise FileNotFoundError(f"음성 없음: {audio_path}")

    if output_path is None:
        output_path = video_path.with_name(f"{video_path.stem}_voiced.mp4")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = _find_ffmpeg()
    # -stream_loop -1: 영상 무한 반복 → -shortest 로 음성이 끝나면 종료.
    # libx264 + yuv420p 재인코딩: loop 이음새가 깔끔하고 브라우저 <video> 호환.
    # -map: 영상은 입력0(0:v), 음성은 입력1(1:a)에서 가져옴.
    cmd = [
        ffmpeg, "-y",
        "-stream_loop", "-1", "-i", str(video_path),
        "-i", str(audio_path),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path),
    ]
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    if result.returncode != 0:
        raise LivePortraitError(f"음성 합치기 실패:\n{result.stderr[-2000:]}")
    if not output_path.exists():
        raise LivePortraitError(f"합쳐진 영상을 찾을 수 없음: {output_path}")
    return output_path


def generate_video(
    source_image: str | Path,
    driving_video: str | Path | None = None,
    output_dir: str | Path = "output",
) -> Path:
    """사진 → 추모 영상(MP4) 생성. 생성된 MP4 경로를 반환.

    Args:
        source_image: 반려동물 사진 경로
        driving_video: 모션 영상 경로 (None이면 기본 잔잔한 모션)
        output_dir: 결과 저장 폴더
    """
    source_image = Path(source_image)
    output_dir = Path(output_dir)

    if not source_image.exists():
        raise FileNotFoundError(f"source 사진 없음: {source_image}")

    # remote 모드: driving 은 GPU 서버가 자기 것을 사용 → 사진만 보냄.
    if MODE == "remote":
        return _generate_remote(source_image, output_dir)

    # local / replicate 모드는 driving 영상이 로컬에 있어야 함.
    driving_video = Path(driving_video) if driving_video else DEFAULT_DRIVING
    if not driving_video.exists():
        raise FileNotFoundError(f"driving 영상 없음: {driving_video}")

    if MODE == "replicate":
        return _generate_replicate(source_image, driving_video, output_dir)
    return _generate_local(source_image, driving_video, output_dir)


def _generate_remote(source: Path, output_dir: Path) -> Path:
    """터널된 GPU 서비스(server.py)에 사진을 보내 무음 영상을 받아 저장.

    백엔드(NCP)에서 사용. GPU 가 없는 머신에서도 정환주 GPU 서버로 추론을 위임.
    driving 영상은 GPU 서버가 자기 LIVEPORTRAIT_DRIVING 을 사용하므로 보내지 않음.
    """
    if not REMOTE_URL:
        raise LivePortraitError(
            "LIVEPORTRAIT_REMOTE_URL 이 설정되지 않았습니다 (remote 모드)."
        )
    try:
        import requests  # remote 모드에서만 필요하므로 지연 import
    except ImportError as e:
        raise LivePortraitError("requests 패키지 미설치: pip install requests") from e

    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"{source.stem}--remote.mp4"

    try:
        with open(source, "rb") as img:
            resp = requests.post(
                f"{REMOTE_URL}/generate",
                files={"source": (source.name, img, "application/octet-stream")},
                timeout=300,  # GPU 추론 ~1분, 여유 있게
            )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise LivePortraitError(f"원격 GPU 서비스 호출 실패: {e}") from e

    if not resp.content:
        raise LivePortraitError("원격 GPU 서비스가 빈 응답을 반환했습니다.")
    out_path.write_bytes(resp.content)
    return out_path


def _generate_local(source: Path, driving: Path, output_dir: Path) -> Path:
    """로컬 GPU(외부 LivePortrait animals 모드)로 생성."""
    if not LP_HOME.exists():
        raise LivePortraitError(
            f"LivePortrait 설치본을 찾을 수 없음: {LP_HOME}\n"
            f"LIVEPORTRAIT_HOME 환경변수를 확인하세요."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    out_abs = output_dir.resolve()

    # animals 모드는 stitching 미학습 → --no_flag_stitching 필수
    # driving_multiplier로 모션 강도 억제 (입 움직임 줄여 "말하는 영상" 방지)
    cmd = [
        "conda", "run", "-n", CONDA_ENV, "python", "inference_animals.py",
        "-s", str(source.resolve()),
        "-d", str(driving.resolve()),
        "-o", str(out_abs),
        "--no_flag_stitching",
        "--driving_multiplier", str(DRIVING_MULTIPLIER),
    ]

    result = subprocess.run(
        cmd, cwd=str(LP_HOME), capture_output=True, text=True, encoding="utf-8", errors="ignore"
    )
    if result.returncode != 0:
        raise LivePortraitError(f"LivePortrait 실행 실패:\n{result.stderr[-2000:]}")

    # 출력 파일명: {source_stem}--{driving_stem}.mp4
    expected = out_abs / f"{source.stem}--{driving.stem}.mp4"
    if not expected.exists():
        raise LivePortraitError(f"생성 영상을 찾을 수 없음: {expected}")
    return expected


def _generate_replicate(source: Path, driving: Path, output_dir: Path) -> Path:
    """Replicate API(fofr/live-portrait)로 생성. 로컬 GPU fallback."""
    if not REPLICATE_TOKEN:
        raise LivePortraitError("REPLICATE_API_TOKEN 이 설정되지 않았습니다.")

    try:
        import replicate  # 로컬 모드에선 불필요하므로 지연 import
    except ImportError as e:
        raise LivePortraitError("replicate 패키지 미설치: pip install replicate") from e

    output_dir.mkdir(parents=True, exist_ok=True)

    with open(source, "rb") as img, open(driving, "rb") as vid:
        output_url = replicate.run(
            "fofr/live-portrait",  # animals 파라미터 지원 여부 확인 필요
            input={"face_image": img, "driving_video": vid},
        )

    # 결과 URL 다운로드
    import httpx

    out_path = output_dir / f"{source.stem}--replicate.mp4"
    resp = httpx.get(str(output_url), timeout=120)
    resp.raise_for_status()
    out_path.write_bytes(resp.content)
    return out_path


if __name__ == "__main__":
    # 스모크 테스트: 샘플 고양이 사진으로 생성
    sample = LP_HOME / "assets" / "examples" / "source" / "s39.jpg"
    print(f"[모드] {MODE}")
    print(f"[입력] {sample}")
    result = generate_video(sample, output_dir="output")
    print(f"[성공] 생성됨 → {result}")
