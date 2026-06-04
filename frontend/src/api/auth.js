import api from './axiosInstance';

export async function register({ email, password, nickname }) {
  const { data } = await api.post('/api/v1/auth/register', { email, password, nickname });
  return data;
}

export async function login({ email, password }) {
  const { data } = await api.post('/api/v1/auth/login', { email, password });
  return data;
}
