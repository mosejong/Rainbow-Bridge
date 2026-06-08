import api from './axiosInstance';

export async function generateMessage({ pet_id }) {
  const res = await api.post('/api/v1/messages/generate', { pet_id });
  return res.data;
}

export async function getLatestMessage(petId) {
  const res = await api.get(`/api/v1/messages/latest?pet_id=${petId}`);
  return res.data;
}
