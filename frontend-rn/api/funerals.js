import api from './axiosInstance';

export async function getFunerals(params) {
  const res = await api.get('/api/v1/funerals', { params });
  return res.data;
}

export async function createFuneralRecord(payload) {
  const res = await api.post('/api/v1/funeral-records', payload);
  return res.data;
}
