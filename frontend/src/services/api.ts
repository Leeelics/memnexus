import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Sessions
export const sessionsApi = {
  list: () => api.get('/sessions'),
  get: (id: string) => api.get(`/sessions/${id}`),
  create: (data: any) => api.post('/sessions', data),
  delete: (id: string) => api.delete(`/sessions/${id}`),
  start: (id: string) => api.post(`/sessions/${id}/start`),
  pause: (id: string) => api.post(`/sessions/${id}/pause`),
}

// Agents
export const agentsApi = {
  list: (sessionId: string) => api.get(`/sessions/${sessionId}/agents`),
  add: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/agents`, data),
  launch: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/agents/launch`, data),
  connect: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/agents/connect`, data),
}

// Memory
export const memoryApi = {
  search: (sessionId: string, query: string, limit?: number) =>
    api.get(`/sessions/${sessionId}/memory`, { params: { query, limit } }),
  add: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/memory`, data),
  stats: () => api.get('/memory/stats'),
}

// RAG
export const ragApi = {
  ingest: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/rag/ingest`, data),
  ingestFile: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/rag/ingest-file`, data),
  query: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/rag/query`, data),
}

// Orchestration
export const orchestrationApi = {
  createPlan: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/plan`, data),
  executePlan: (sessionId: string, data: any) => api.post(`/sessions/${sessionId}/execute`, data),
  pause: (sessionId: string) => api.post(`/sessions/${sessionId}/pause`),
  resume: (sessionId: string) => api.post(`/sessions/${sessionId}/resume`),
  cancel: (sessionId: string) => api.post(`/sessions/${sessionId}/cancel`),
}

// Interventions
export const interventionsApi = {
  list: (sessionId: string) => api.get(`/sessions/${sessionId}/interventions`),
  resolve: (interventionId: string, data: any) => api.post(`/interventions/${interventionId}/resolve`, data),
}

// Health
export const healthApi = {
  check: () => api.get('/health'),
}

// WebSocket
export class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  
  constructor(private url: string) {}
  
  connect(onMessage: (data: any) => void) {
    this.ws = new WebSocket(this.url)
    
    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onMessage(data)
    }
    
    this.ws.onclose = () => {
      console.log('WebSocket closed')
      this.attemptReconnect(onMessage)
    }
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
  }
  
  private attemptReconnect(onMessage: (data: any) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++
      setTimeout(() => this.connect(onMessage), 1000 * this.reconnectAttempts)
    }
  }
  
  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
  
  disconnect() {
    this.ws?.close()
  }
}
