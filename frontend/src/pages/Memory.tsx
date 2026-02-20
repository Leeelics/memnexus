import { useState } from 'react'
import { MagnifyingGlassIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

const mockMemories = [
  { id: 'mem_001', content: 'Created user authentication system with JWT', source: 'claude', type: 'code', timestamp: '2026-02-20T10:30:00Z' },
  { id: 'mem_002', content: 'Designed database schema for user profiles', source: 'kimi', type: 'conversation', timestamp: '2026-02-20T10:25:00Z' },
  { id: 'mem_003', content: 'API endpoints: POST /api/auth/login, POST /api/auth/register', source: 'claude', type: 'code', timestamp: '2026-02-20T10:20:00Z' },
]

export function Memory() {
  const [query, setQuery] = useState('')
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Memory</h1>
        <p className="text-gray-500 mt-1">Search and explore shared agent memory</p>
      </div>
      
      {/* Search */}
      <div className="card">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memory..."
            className="w-full pl-12 pr-4 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>
      
      {/* Memory List */}
      <div className="space-y-4">
        {mockMemories.map((memory) => (
          <div key={memory.id} className="card hover:shadow-md transition-shadow">
            <div className="flex items-start gap-4">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <DocumentTextIcon className="w-5 h-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-gray-800">{memory.content}</p>
                <div className="flex gap-4 mt-3 text-sm text-gray-500">
                  <span className="px-2 py-1 bg-gray-100 rounded">{memory.source}</span>
                  <span className="px-2 py-1 bg-gray-100 rounded">{memory.type}</span>
                  <span>{new Date(memory.timestamp).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
