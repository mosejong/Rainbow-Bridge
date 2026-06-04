import api from './axiosInstance';

export async function getMissions({ pet_id }) {
  const { data } = await api.get(`/api/v1/missions/${pet_id}`);
  return data;
}

export async function completeMission({ mission_id }) {
  const { data } = await api.patch(`/api/v1/missions/${mission_id}/complete`, { completed: true });
  return data;
}
