import api from './axiosInstance';

export async function generateMessage({ pet_id }) {
  const { data } = await api.post('/api/v1/messages', { pet_id });
  return data;
}
