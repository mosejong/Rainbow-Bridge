import api from './axiosInstance';

export async function getReport(petId) {
  const res = await api.get(`/api/v1/report/${petId}`);
  return res.data;
}
