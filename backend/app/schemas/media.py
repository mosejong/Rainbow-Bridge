from typing import Optional
from pydantic import BaseModel


class MediaUploadResponse(BaseModel):
    asset_id: str


class MediaStatusResponse(BaseModel):
    asset_id: str
    status: str  # processing | done | error
    video_url: Optional[str] = None
