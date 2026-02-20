import { create } from 'zustand'

interface Session {
  id: string
  name: string
  status: string
  agent_count: number
  task_count: number
  created_at: string
}

interface Agent {
  id: string
  session_id: string
  role: string
  cli: string
  status: string
}

interface StoreState {
  sessions: Session[]
  agents: Agent[]
  currentSession: Session | null
  pendingInterventions: number
  wsConnected: boolean
  
  setSessions: (sessions: Session[]) => void
  setAgents: (agents: Agent[]) => void
  setCurrentSession: (session: Session | null) => void
  setPendingInterventions: (count: number) => void
  setWsConnected: (connected: boolean) => void
  
  addSession: (session: Session) => void
  updateSession: (session: Session) => void
  removeSession: (id: string) => void
}

export const useStore = create<StoreState>((set) => ({
  sessions: [],
  agents: [],
  currentSession: null,
  pendingInterventions: 0,
  wsConnected: false,
  
  setSessions: (sessions) => set({ sessions }),
  setAgents: (agents) => set({ agents }),
  setCurrentSession: (session) => set({ currentSession: session }),
  setPendingInterventions: (count) => set({ pendingInterventions: count }),
  setWsConnected: (connected) => set({ wsConnected: connected }),
  
  addSession: (session) =>
    set((state) => ({ sessions: [...state.sessions, session] })),
  updateSession: (session) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === session.id ? session : s
      ),
    })),
  removeSession: (id) =>
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
    })),
}))
