import api from './axiosInstance';

export async function postEmotion({ pet_id, score, note }) {
  const { data } = await api.post('/api/v1/emotions', { pet_id, score, note });
  return data;
}
