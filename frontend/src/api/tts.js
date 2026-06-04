import axiosInstance from './axiosInstance';

export async function generateTts({ message_id, tone }) {
  const { data } = await axiosInstance.post(`/messages/${message_id}/tts`, { tone });
  return data;
}
