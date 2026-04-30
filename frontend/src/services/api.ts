import axios from 'axios';
import { useAppStore } from '../store';

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = useAppStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAppStore.getState().logout();
    }
    return Promise.reject(error);
  },
);

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  timestamp: string;
  prediction?: any;
}

export interface PredictRequest {
  symbol: string;
  pred_len: number;
  model_name?: string;
  lookback?: number;
  freq?: string;
  sample_count?: number;
  T?: number;
  top_p?: number;
}

export interface PredictionData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  confidence: { low_95: number; high_95: number };
}

export interface PredictResponse {
  task_id: string;
  status: string;
  symbol: string;
  model: string;
  predictions: PredictionData[];
  interpretation: string;
  risk_warning: string;
  created_at: string;
  duration_ms: number;
}

export const authApi = {
  register: (email: string, password: string) => {
    return api.post('/register', { email, password });
  },
  login: (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    return api.post('/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getMe: () => {
    return api.get('/users/me');
  },
};

export const chatApi = {
  sendMessage: (data: ChatRequest) => {
    return api.post<ChatResponse>('/chat', data);
  },
  predict: (data: PredictRequest) => {
    return api.post<PredictResponse>('/predict', data);
  },
};

export default api;
