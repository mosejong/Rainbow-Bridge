import api from './axiosInstance';

export async function getTimeline({ pet_id }) {
  const res = await api.get(`/api/v1/timeline/${pet_id}`);
  return res.data;
}
