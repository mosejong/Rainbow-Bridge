import api from './axiosInstance';

export async function logPlay({ pet_id, event_type = 'tts' }) {
  const res = await api.post('/api/v1/play-logs', { pet_id, event_type });
  return res.data;
}
