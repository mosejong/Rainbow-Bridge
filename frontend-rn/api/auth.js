import api from './axiosInstance';

export async function login({ email, password }) {
  const res = await api.post('/api/v1/auth/login', { email, password });
  return res.data;
}

export async function register({ email, password, name }) {
  const res = await api.post('/api/v1/auth/register', { email, password, nickname: name });
  return res.data;
}
