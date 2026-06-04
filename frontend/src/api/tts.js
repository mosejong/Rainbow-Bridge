import axiosInstance from './axiosInstance';

export async function generateTts({ pet_id, text, tone }) {
  const { data } = await axiosInstance.post('/api/v1/tts', { pet_id, text, tone });
  return data;
}
