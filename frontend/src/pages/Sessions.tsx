import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { PlusIcon, PlayIcon, PauseIcon, TrashIcon } from '@heroicons/react/24/outline'
import { sessionsApi } from '../services/api'
import toast from 'react-hot-toast'

export function Sessions() {
  const queryClient = useQueryClient()
  const [isCreating, setIsCreating] = useState(false)
  const [newSessionName, setNewSessionName] = useState('')
  
  const { data: sessions } = useQuery('sessions', () => sessionsApi.list())
  
  const createMutation = useMutation(
    (name: string) => sessionsApi.create({ name, strategy: 'sequential' }),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sessions')
        setIsCreating(false)
        setNewSessionName('')
        toast.success('Session created')
      },
    }
  )
  
  const deleteMutation = useMutation(
    (id: string) => sessionsApi.delete(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('sessions')
        toast.success('Session deleted')
      },
    }
  )
  
  const sessionList = sessions?.data || []
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Sessions</h1>
          <p className="text-gray-500 mt-1">Manage your multi-agent sessions</p>
        </div>
        <button
          onClick={() => setIsCreating(true)}
          className="btn-primary flex items-center gap-2"
        >
          <PlusIcon className="w-5 h-5" />
          New Session
        </button>
      </div>
      
      {/* Create Session Modal */}
      {isCreating && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create New Session</h3>
            <input
              type="text"
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              placeholder="Session name"
              className="input mb-4"
              autoFocus
            />
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setIsCreating(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={() => createMutation.mutate(newSessionName)}
                disabled={!newSessionName}
                className="btn-primary"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Sessions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sessionList.map((session: any) => (
          <div key={session.id} className="card hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="font-semibold text-gray-900">{session.name}</h3>
                <p className="text-sm text-gray-500">{session.id}</p>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                session.status === 'running'
                  ? 'bg-green-100 text-green-700'
                  : session.status === 'paused'
                  ? 'bg-yellow-100 text-yellow-700'
                  : 'bg-gray-100 text-gray-700'
              }`}>
                {session.status}
              </span>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-gray-500">Agents</p>
                <p className="text-xl font-semibold text-gray-900">{session.agent_count}</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-sm text-gray-500">Tasks</p>
                <p className="text-xl font-semibold text-gray-900">{session.task_count}</p>
              </div>
            </div>
            
            <div className="flex gap-2">
              <a
                href={`/sessions/${session.id}`}
                className="flex-1 btn-primary text-center"
              >
                View
              </a>
              <button
                onClick={() => deleteMutation.mutate(session.id)}
                className="btn-danger px-3"
              >
                <TrashIcon className="w-5 h-5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
