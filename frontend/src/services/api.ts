import axios from 'axios';
import { TMDbDrama, MediaFile, KDramaRequest, User } from '../types';

const API_BASE = '/api/v1';

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Set token dynamically
client.interceptors.request.use((config) => {
  const token = localStorage.getItem('kdrama_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const api = {
  // Dramas & Search
  searchDramas: async (query: string, limit: number = 20, offset: number = 0) => {
    const res = await client.get('/dramas', { params: { query, limit, offset } });
    return res.data;
  },

  getRecentUploads: async (limit: number = 20) => {
    const res = await client.get('/dramas', { params: { limit } });
    return res.data;
  },

  getDramaDetails: async (tmdbId: number) => {
    const res = await client.get(`/dramas/${tmdbId}`);
    return res.data;
  },

  // Requests
  createRequest: async (drama_name: string, details?: string, tmdb_id?: number) => {
    const res = await client.post('/requests', { drama_name, details, tmdb_id });
    return res.data;
  },

  getMyRequests: async () => {
    const res = await client.get('/requests/my');
    return res.data.requests as KDramaRequest[];
  },

  // Auth
  telegramLogin: async (telegramUser: any) => {
    const res = await client.post('/auth/telegram', telegramUser);
    if (res.data.access_token) {
      localStorage.setItem('kdrama_token', res.data.access_token);
      localStorage.setItem('kdrama_user', JSON.stringify(res.data.user));
    }
    return res.data;
  }
};
