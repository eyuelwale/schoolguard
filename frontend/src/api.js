import axios from "axios";

const getBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  return "";
};

const api = axios.create({
  baseURL: getBaseUrl(),
  timeout: 300000, // 5 minutes timeout (300,000 ms) as requested
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("schoolguard_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export default api;
