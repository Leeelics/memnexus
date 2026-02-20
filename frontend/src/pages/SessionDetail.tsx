import { useParams } from 'react-router-dom'
import { useQuery } from 'react-query'
import { sessionsApi, agentsApi } from '../services/api'
import { PlayIcon, PauseIcon, PlusIcon } from '@heroicons/react/24/outline'

export function SessionDetail() {
  const { id } = useParams<{ id: string }>()
  
  const { data: session } = useQuery(['session', id], () => sessionsApi.get(id!))
  const { data: agents } = useQuery(['agents', id], () => agentsApi.list(id!))
  
  const sessionData = session?.data
  const agentList = agents?.data || []
  
  if (!sessionData) {
    return <div className="text-center py-12">Loading...</div>
  }
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{sessionData.name}</h1>
          <p className="text-gray-500">{sessionData.id}</p>
        </div>
        <div className="flex gap-3">
          <button className="btn-primary flex items-center gap-2">
            <PlayIcon className="w-5 h-5" />
            Start
          </button>
          <button className="btn-secondary flex items-center gap-2">
            <PauseIcon className="w-5 h-5" />
            Pause
          </button>
        </div>
      </div>
      
      {/* Session Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <p className="text-sm text-gray-500">Status</p>
          <span className={`inline-block mt-1 px-3 py-1 rounded-full text-sm font-medium ${
            sessionData.status === 'running'
              ? 'bg-green-100 text-green-700'
              : 'bg-gray-100 text-gray-700'
          }`}>
            {sessionData.status}
          </span>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Strategy</p>
          <p className="text-lg font-semibold text-gray-900">{sessionData.strategy}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Working Directory</p>
          <p className="text-lg font-semibold text-gray-900">{sessionData.working_dir}</p>
        </div>
      </div>
      
      {/* Agents */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Agents</h3>
          <button className="btn-secondary flex items-center gap-2 text-sm">
            <PlusIcon className="w-4 h-4" />
            Add Agent
          </button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">ID</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Role</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">CLI</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {agentList.map((agent: any) => (
                <tr key={agent.id} className="border-b border-gray-100">
                  <td className="py-3 px-4 font-mono text-sm">{agent.id}</td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                      {agent.role}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-700">{agent.cli}</td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 rounded text-sm ${
                      agent.status === 'idle'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {agent.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
