// utils/api.js — All backend API calls
// The "proxy" field in package.json forwards /upload-resume etc. to localhost:8000
import axios from 'axios';

const api = axios.create({ timeout: 120000 });

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
  return data; // { file_id, filename, parsed }
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

// Download URL — goes through proxy
export const downloadUrl = (fileId) => 
  `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/download/${fileId}_enhanced`;
