import api from './axiosInstance';

export async function getMissions({ pet_id }) {
  const res = await api.get(`/api/v1/missions?pet_id=${pet_id}`);
  return res.data;
}

export async function completeMission({ mission_id }) {
  const res = await api.patch(`/api/v1/missions/${mission_id}`, { completed: true });
  return res.data;
}
