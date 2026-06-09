import api from './axiosInstance';

// 사진 업로드 → { asset_id } 반환. 영상 생성은 서버 백그라운드에서 진행됨.
export async function uploadMedia(formData) {
  const res = await api.post('/api/v1/media/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

// 영상 생성 상태 조회 → { asset_id, status: processing|done|error, video_url }
export async function getMediaStatus(assetId) {
  const res = await api.get(`/api/v1/media/${assetId}`);
  return res.data;
}
