from typing import Optional
from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    asset_id: str


class MediaStatusResponse(BaseModel):
    asset_id: str
    status: str  # processing | done | error
    gif_url: Optional[str] = None  # ① GIF (d9 잔잔한 드라이빙, 다운로드용)
    video_url: Optional[str] = None  # ③ 1인칭 편지용 무음 영상 (d3 입모양)
    voiced_url: Optional[str] = None  # ③ 1인칭 편지용 영상 + TTS 합친 결과
    dubbed_url: Optional[str] = None  # PERSO 다국어 더빙 결과 (추후)
