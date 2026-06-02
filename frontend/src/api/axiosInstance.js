import axios from 'axios';

const api = axios.create({
  baseURL: 'https://preacher-posing-lair.ngrok-free.dev',
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true',
  },
});

export default api;
