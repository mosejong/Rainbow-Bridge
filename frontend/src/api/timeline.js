import axiosInstance from './axiosInstance';

export async function getTimeline({ pet_id }) {
  const { data } = await axiosInstance.get(`/timeline/${pet_id}`);
  return data;
}
