import api from './axiosInstance';

export async function postEmotion({ pet_id, score, note }) {
  const res = await api.post('/api/v1/emotions', { pet_id, score, note });
  return res.data;
}

export async function getEmotions(petId) {
  const res = await api.get(`/api/v1/emotions?pet_id=${petId}`);
  return res.data;
}
