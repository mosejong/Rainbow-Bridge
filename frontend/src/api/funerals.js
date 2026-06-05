import api from './axiosInstance';

// TODO: 백엔드 GET /api/v1/funerals 완성 후 연동
// 파라미터: { lat, lng, radius_km } (위치 기반) 또는 { query }
export async function getFunerals(params = {}) {
  const res = await api.get('/api/v1/funerals', { params });
  return res.data; // [{ id, name, location, phone, distance, services, hours }]
}

// TODO: 백엔드 POST /api/v1/funeral-records 완성 후 연동
// 장례 신청 기록 저장
export async function createFuneralRecord(payload) {
  const res = await api.post('/api/v1/funeral-records', payload);
  return res.data;
}
