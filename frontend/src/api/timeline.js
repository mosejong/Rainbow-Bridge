import axiosInstance from './axiosInstance';

export async function getTimeline({ pet_id }) {
  const { data } = await axiosInstance.get(`/api/v1/timeline/${pet_id}`);
  return data;
}
