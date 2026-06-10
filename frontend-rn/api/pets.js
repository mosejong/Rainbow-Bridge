import api from './axiosInstance';

export async function createPet(payload) {
  const res = await api.post('/api/v1/pets', payload);
  return res.data;
}

export async function getMyPets() {
  const res = await api.get('/api/v1/pets');
  return res.data;
}

export async function getPet(petId) {
  const res = await api.get(`/api/v1/pets/${petId}`);
  return res.data;
}

export async function getRecoveryStatus(petId) {
  const res = await api.get(`/api/v1/pets/${petId}/recovery`);
  return res.data;
}
