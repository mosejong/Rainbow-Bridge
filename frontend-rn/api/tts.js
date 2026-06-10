import api from './axiosInstance';

export async function generateTts({ pet_id, text, tone }) {
  const res = await api.post('/api/v1/tts', { pet_id, text, tone });
  return res.data;
}
