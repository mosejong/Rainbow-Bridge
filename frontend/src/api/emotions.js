import api from './axiosInstance';

export async function postEmotion({ pet_id, mood, note }) {
  const { data } = await api.post('/api/v1/emotions', { pet_id, mood, note });
  return data;
}
