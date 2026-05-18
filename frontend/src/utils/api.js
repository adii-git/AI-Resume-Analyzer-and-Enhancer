import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || '';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000,
});

api.interceptors.response.use(
  r => r,
  err => Promise.reject(new Error(
    err.response?.data?.detail || err.message || 'Request failed'
  ))
);

export async function uploadResume(file, onProgress) {
  const form = new FormData();
  form.append('file', file);
  const { data } = await api.post('/upload-resume', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => onProgress?.(Math.round(e.loaded * 100 / e.total)),
  });
  return data;
}

export async function analyzeResume(payload) {
  const { data } = await api.post('/analyze', payload);
  return data;
}

export async function enhanceResume(payload) {
  const { data } = await api.post('/enhance', payload);
  return data;
}

export async function compareResumes(payload) {
  const { data } = await api.post('/compare', payload);
  return data;
}

export async function getRoles() {
  const { data } = await api.get('/roles');
  return data.roles;
}

export const downloadUrl = (fileId) => {
  const base = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  return `${base}/download/${fileId}_enhanced`;
};