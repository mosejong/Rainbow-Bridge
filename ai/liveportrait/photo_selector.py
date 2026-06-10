"""LivePortrait 적합 사진 자동 선택.

업로드된 반려동물 사진 여러 장 중 LivePortrait 추모 영상 생성에 가장 적합한
사진을 자동으로 골라줍니다.

선택 기준:
  1. 정면 여부 (필터): Gemini Vision으로 front 판별 — side·back·none 즉시 실격(0점)
     API 실패 시 판단 보류 → 품질 점수로만 비교 (실격 처리 안 함)
  2. 품질 점수 (합산, 정면 통과 사진에만 적용):
     - 선명도  (50%): Laplacian 분산 — 흐릿하면 LP 결과물도 번짐
     - 밝기    (20%): 128 근처 최적 — 너무 어둡거나 밝으면 얼굴 인식률 저하
     - 해상도  (15%): 고해상도일수록 세부 표현력 향상 (최대 3MP 클리핑)
     - 종횡비  (15%): 1:1에 가까울수록 LP crops 왜곡 최소화
     - 얼굴 크기 (보너스): MediaPipe 감지 시 얼굴 크기 비율 가산 — 감지 실패 시 0

사용처:
  - backend/app/services/media.py: select_best_pet_photo()
  - POST /media/generate/{pet_id} 엔드포인트에서 자동 호출
"""
from __future__ import annotations

import base64
import os
from pathlib import Path


def _is_front_facing(image_path: str | Path) -> bool | None:
    """Gemini Vision으로 동물이 정면을 향하는지 판별.

    Returns:
        True  — 정면 확인
        False — 측면·뒷면·동물 없음 (실격)
        None  — API 실패 또는 키 없음 (판단 보류, 실격 처리 안 함)
    """
    try:
        from openai import OpenAI

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
        if not api_key:
            return None

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()

        suffix = Path(image_path).suffix.lower()
        mime = (
            "image/png" if suffix == ".png"
            else "image/webp" if suffix == ".webp"
            else "image/jpeg"
        )

        client = OpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        response = client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{img_b64}"},
                        },
                        {
                            "type": "text",
                            "text": (
                                "이 사진에서 동물의 얼굴 방향을 판단하세요. "
                                "다음 단어 중 하나만 답하세요: "
                                "front (정면), side (측면), back (뒷모습 또는 엉덩이), none (동물 없음)"
                            ),
                        },
                    ],
                }
            ],
            max_tokens=5,
        )
        answer = response.choices[0].message.content.strip().lower().split()[0]
        return answer == "front"
    except Exception:
        return None


def _face_bonus(img) -> float:
    """MediaPipe 얼굴 감지 성공 시 얼굴 크기 비율 보너스 반환. 실패·미설치 시 0."""
    try:
        import cv2
        import mediapipe as mp

        mp_face = mp.solutions.face_detection
        with mp_face.FaceDetection(
            model_selection=0, min_detection_confidence=0.3
        ) as detector:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb)
            if not results.detections:
                return 0.0
            best = max(
                results.detections,
                key=lambda d: (
                    d.location_data.relative_bounding_box.width
                    * d.location_data.relative_bounding_box.height
                ),
            )
            bb = best.location_data.relative_bounding_box
            face_ratio = bb.width * bb.height  # 0~1 (정면 펫 사진 통상 0.05~0.4)
            return face_ratio * 50.0
    except Exception:
        return 0.0


def score(image_path: str | Path) -> float:
    """이미지 한 장의 LivePortrait 적합도 점수를 반환합니다 (높을수록 좋음)."""
    # 정면이 아닌 것으로 확인된 사진은 즉시 실격
    orientation = _is_front_facing(image_path)
    if orientation is False:
        return 0.0

    try:
        import cv2
        import numpy as np
    except ImportError as e:
        raise RuntimeError(
            "opencv-python 필요: pip install opencv-python"
        ) from e

    img = cv2.imread(str(image_path))
    if img is None:
        return 0.0

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # 선명도: Laplacian 분산 (높을수록 선명 — 수백~수천 범위)
    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    # 밝기: 128 기준 대칭, 0~1 정규화
    brightness = float(np.mean(gray))
    brightness_score = 1.0 - abs(brightness - 128.0) / 128.0

    # 해상도: 메가픽셀 (최대 3MP 클리핑 후 0~3 범위)
    megapixels = min((h * w) / 1_000_000, 3.0)

    # 종횡비: 1:1 = 1.0, 2:1 = 0.5
    ratio = min(h, w) / max(h, w) if max(h, w) > 0 else 0.0

    return (
        sharpness * 0.50
        + brightness_score * 50.0 * 0.20
        + megapixels * 10.0 * 0.15
        + ratio * 50.0 * 0.15
        + _face_bonus(img)
    )


def pick_best(paths: list[str | Path]) -> Path | None:
    """여러 사진 경로 중 LivePortrait 적합도가 가장 높은 사진 경로를 반환합니다."""
    if not paths:
        return None
    scored = [(score(p), Path(p)) for p in paths if Path(p).exists()]
    if not scored:
        return None
    return max(scored, key=lambda x: x[0])[1]
