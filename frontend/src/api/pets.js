import api from './axiosInstance';
import { mockPet } from './mock';

const USE_MOCK = false;

export async function createPet(data) {
  if (USE_MOCK) {
    return { ...mockPet, ...data, _id: 'pet_' + Date.now() };
  }
  const res = await api.post('/api/v1/pets', data);
  return res.data;
}
