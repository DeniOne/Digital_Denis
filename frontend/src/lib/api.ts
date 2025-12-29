import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const messagesApi = {
  send: async (content: string, sessionId?: string) => {
    const response = await api.post('/messages', { content, session_id: sessionId });
    return response.data;
  },
  getHistory: async (sessionId: string) => {
    const response = await api.get(`/messages/session/${sessionId}`);
    return response.data;
  },
};

export const memoryApi = {
  list: async (type?: string, limit = 20, offset = 0) => {
    const params = { limit, offset, ...(type && { item_type: type }) };
    const response = await api.get('/memory', { params });
    return response.data;
  },
  get: async (id: string) => {
    const response = await api.get(`/memory/${id}`);
    return response.data;
  },
  search: async (query: string) => {
    const response = await api.post('/memory/search', { query });
    return response.data;
  },
};

export default api;
