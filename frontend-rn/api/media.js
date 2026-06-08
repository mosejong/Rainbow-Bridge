import api from './axiosInstance';

export async function uploadMedia(formData) {
  const res = await api.post('/api/v1/media/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}
