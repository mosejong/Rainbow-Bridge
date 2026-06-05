import api from './axiosInstance';

export async function getLatestMessage(pet_id) {
  const { data } = await api.get(`/api/v1/messages/${pet_id}/latest`);
  return data;
}

export async function generateMessage({ pet_id, tone, emotion_score, note }) {
  const { data } = await api.post('/api/v1/messages', { pet_id, tone, emotion_score, note });
  return data;
}
