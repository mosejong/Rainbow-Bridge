import api from './axiosInstance';

// TODO: 백엔드 GET /api/v1/hospitals 완성 후 연동
// 파라미터: { lat, lng, radius_km } (카카오맵 위치 기반) 또는 { query }
export async function getHospitals(params = {}) {
  const res = await api.get('/api/v1/hospitals', { params });
  return res.data; // [{ id, name, address, phone, distance, lat, lng, hours }]
}
