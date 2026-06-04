import api from './axiosInstance';

export async function getReport({ pet_id, period }) {
  const params = period ? { period } : {};
  const { data } = await api.get(`/api/v1/report/${pet_id}`, { params });
  return data;
}
