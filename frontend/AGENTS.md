# frontend/ - React Frontend Guide

> **Language**: English (code), 中文 (docs reference)
> **Stack**: React 18 + TypeScript + Vite + Tailwind CSS + Zustand

---

## Overview

MemNexus React frontend provides a real-time dashboard for managing multi-agent sessions, monitoring agents, and orchestrating tasks.

## Structure

```
frontend/
├── src/
│   ├── App.tsx              # Root component + routing
│   ├── main.tsx             # Entry point
│   ├── components/          # Reusable UI components
│   │   ├── Layout.tsx       # App shell with sidebar
│   │   ├── Header.tsx       # Top navigation
│   │   └── Sidebar.tsx      # Navigation menu
│   ├── pages/               # Route-level pages
│   │   ├── Dashboard.tsx    # Overview + stats
│   │   ├── Sessions.tsx     # Session management
│   │   ├── SessionDetail.tsx # Single session view
│   │   ├── Agents.tsx       # Agent list
│   │   ├── Memory.tsx       # Memory explorer
│   │   ├── Orchestration.tsx # Task orchestration
│   │   ├── Interventions.tsx # Human approval queue
│   │   └── Settings.tsx     # System settings
│   ├── services/            # API clients
│   │   └── api.ts           # Axios + WebSocket wrappers
│   ├── store/               # Zustand state
│   │   └── useStore.ts      # Global state management
│   └── contexts/            # React contexts (if needed)
├── public/                  # Static assets
├── index.html               # HTML template
├── vite.config.ts           # Vite config + proxy
├── tailwind.config.js       # Tailwind customization
└── package.json             # Dependencies
```

## Patterns

### State Management (Zustand)
```typescript
// store/useStore.ts
interface StoreState {
  sessions: Session[]
  currentSession: Session | null
  // Actions
  setSessions: (sessions: Session[]) => void
  addSession: (session: Session) => void
}

export const useStore = create<StoreState>((set) => ({
  sessions: [],
  setSessions: (sessions) => set({ sessions }),
  addSession: (session) =>
    set((state) => ({ sessions: [...state.sessions, session] })),
}))
```

### API Service Pattern
```typescript
// services/api.ts - Grouped by domain
export const sessionsApi = {
  list: () => api.get('/sessions'),
  create: (data: any) => api.post('/sessions', data),
}

export const agentsApi = {
  list: (sessionId: string) => api.get(`/sessions/${sessionId}/agents`),
}
```

### Page Component Pattern
```typescript
// pages/Dashboard.tsx
import { useQuery } from 'react-query'
import { sessionsApi } from '../services/api'

export function Dashboard() {
  const { data: sessions } = useQuery('sessions', () => sessionsApi.list())
  
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>
      {/* Content */}
    </div>
  )
}
```

## Conventions

### Styling (Tailwind)
- Use `className` utility classes
- Custom colors: extend in `tailwind.config.js`
- Component spacing: `space-y-6`, `gap-4`
- Cards: custom `.card` class (see index.css)

### Imports
```typescript
// 1. React/Third-party
import { useQuery } from 'react-query'
import { PlayIcon } from '@heroicons/react/24/solid'

// 2. Services/Store
import { sessionsApi } from '../services/api'
import { useStore } from '../store/useStore'

// 3. Types (if separate)
import type { Session } from '../types'
```

### TypeScript
- Strict mode enabled
- Prefer `interface` over `type` for objects
- Use `any` sparingly (API responses)
- Function components: arrow functions

## API Proxy

Vite dev server proxies `/api` and `/ws` to backend:
```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': { target: 'http://localhost:8080' },
    '/ws': { target: 'ws://localhost:8080', ws: true },
  },
}
```

## Where to Look

| Task | Location | Notes |
|------|----------|-------|
| Add new page | `src/pages/` | Export from `App.tsx` |
| Modify API call | `src/services/api.ts` | Add to relevant domain group |
| Add global state | `src/store/useStore.ts` | Interface + actions |
| Style changes | `tailwind.config.js` | Colors, fonts, spacing |
| WebSocket | `src/services/api.ts` | `WebSocketClient` class |

## Commands

```bash
cd frontend

# Install dependencies
npm install

# Dev server (port 3000)
npm run dev

# Production build
npm run build

# Type check
npx tsc --noEmit

# Lint
npm run lint
```

## Environment Variables

```bash
# .env.local
VITE_API_URL=http://localhost:8080  # Optional, defaults to proxy
```

---

**Frontend communicates with Python backend via:**
- REST API (`/api/v1/*`)
- WebSocket (`/ws`, `/ws/sync/*`)

See `../docs/API.md` for endpoint details.
