import api from './axiosInstance';

export async function getHospitals(params) {
  const res = await api.get('/api/v1/hospitals', { params });
  return res.data;
}
