from typing import Optional
from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    asset_id: str


class MediaStatusResponse(BaseModel):
    asset_id: str
    status: str  # processing | done | error
    video_url: Optional[str] = None  # LivePortrait 무음 영상
    voiced_url: Optional[str] = None  # 영상 + TTS 합친 결과
    dubbed_url: Optional[str] = None  # PERSO 다국어 더빙 결과 (추후)
