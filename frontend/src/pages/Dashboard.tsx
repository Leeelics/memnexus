import { useQuery } from 'react-query'
import { sessionsApi, memoryApi } from '../services/api'
import {
  PlayIcon,
  PauseIcon,
  UsersIcon,
  CircleStackIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/solid'

export function Dashboard() {
  const { data: sessions } = useQuery('sessions', () => sessionsApi.list())
  const { data: memoryStats } = useQuery('memoryStats', () => memoryApi.stats())
  
  const sessionList = sessions?.data || []
  const runningSessions = sessionList.filter((s: any) => s.status === 'running')
  const pausedSessions = sessionList.filter((s: any) => s.status === 'paused')
  
  const stats = [
    {
      title: 'Total Sessions',
      value: sessionList.length,
      icon: CircleStackIcon,
      color: 'bg-blue-500',
    },
    {
      title: 'Running',
      value: runningSessions.length,
      icon: PlayIcon,
      color: 'bg-green-500',
    },
    {
      title: 'Paused',
      value: pausedSessions.length,
      icon: PauseIcon,
      color: 'bg-yellow-500',
    },
    {
      title: 'Total Agents',
      value: sessionList.reduce((acc: number, s: any) => acc + s.agent_count, 0),
      icon: UsersIcon,
      color: 'bg-purple-500',
    },
  ]
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Overview of your multi-agent sessions</p>
      </div>
      
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.title} className="card">
            <div className="flex items-center gap-4">
              <div className={`w-12 h-12 ${stat.color} rounded-xl flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-gray-500">{stat.title}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {/* Recent Sessions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Sessions</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Name</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Agents</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Tasks</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Created</th>
              </tr>
            </thead>
            <tbody>
              {sessionList.slice(0, 5).map((session: any) => (
                <tr key={session.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="font-medium text-gray-900">{session.name}</div>
                    <div className="text-sm text-gray-500">{session.id}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      session.status === 'running'
                        ? 'bg-green-100 text-green-700'
                        : session.status === 'paused'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {session.status === 'running' && <span className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse" />}
                      {session.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-700">{session.agent_count}</td>
                  <td className="py-3 px-4 text-gray-700">{session.task_count}</td>
                  <td className="py-3 px-4 text-gray-500 text-sm">
                    {new Date(session.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Memory Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Memory Statistics</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Total Entries</span>
              <span className="font-semibold text-gray-900">
                {memoryStats?.data?.total_entries || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Sessions</span>
              <span className="font-semibold text-gray-900">
                {memoryStats?.data?.sessions || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Memory Types</span>
              <span className="font-semibold text-gray-900">
                {Object.keys(memoryStats?.data?.memory_types || {}).length}
              </span>
            </div>
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">System Status</h3>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <CheckCircleIcon className="w-5 h-5 text-green-500" />
              <span className="text-gray-700">API Server</span>
              <span className="ml-auto text-green-600 text-sm font-medium">Online</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircleIcon className="w-5 h-5 text-green-500" />
              <span className="text-gray-700">Memory Store</span>
              <span className="ml-auto text-green-600 text-sm font-medium">Connected</span>
            </div>
            <div className="flex items-center gap-3">
              <CheckCircleIcon className="w-5 h-5 text-green-500" />
              <span className="text-gray-700">Orchestrator</span>
              <span className="ml-auto text-green-600 text-sm font-medium">Ready</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
