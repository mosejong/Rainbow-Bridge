import axiosInstance from './axiosInstance';

export async function uploadMedia({ file, pet_id }) {
  const form = new FormData();
  form.append('file', file);
  form.append('pet_id', pet_id);
  const { data } = await axiosInstance.post('/api/v1/media/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function getMediaStatus({ asset_id }) {
  const { data } = await axiosInstance.get(`/api/v1/media/${asset_id}`);
  return data;
}
