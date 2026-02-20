import { UsersIcon, SignalIcon, CircleStackIcon } from '@heroicons/react/24/outline'

const mockAgents = [
  { id: 'ag_001', name: 'Claude Architect', role: 'architect', cli: 'claude', status: 'idle', session: 'sess_001' },
  { id: 'ag_002', name: 'Kimi Backend', role: 'backend', cli: 'kimi', status: 'coding', session: 'sess_001' },
  { id: 'ag_003', name: 'Codex Frontend', role: 'frontend', cli: 'codex', status: 'waiting', session: 'sess_001' },
  { id: 'ag_004', name: 'Claude Tester', role: 'tester', cli: 'claude', status: 'offline', session: 'sess_002' },
]

export function Agents() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Agents</h1>
        <p className="text-gray-500 mt-1">Manage connected AI agents</p>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-blue-500 rounded-xl flex items-center justify-center">
              <UsersIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Total Agents</p>
              <p className="text-2xl font-bold text-gray-900">{mockAgents.length}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-green-500 rounded-xl flex items-center justify-center">
              <SignalIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Active</p>
              <p className="text-2xl font-bold text-gray-900">
                {mockAgents.filter(a => a.status !== 'offline').length}
              </p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center">
              <CircleStackIcon className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Memory Sync</p>
              <p className="text-2xl font-bold text-gray-900">On</p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Agents Table */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Connected Agents</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Agent</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Role</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">CLI</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Session</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {mockAgents.map((agent) => (
                <tr key={agent.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4">
                    <div className="font-medium text-gray-900">{agent.name}</div>
                    <div className="text-sm text-gray-500">{agent.id}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-sm">
                      {agent.role}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-gray-700">{agent.cli}</td>
                  <td className="py-3 px-4 text-gray-700">{agent.session}</td>
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      agent.status === 'idle'
                        ? 'bg-green-100 text-green-700'
                        : agent.status === 'coding'
                        ? 'bg-blue-100 text-blue-700'
                        : agent.status === 'waiting'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${
                        agent.status === 'idle'
                          ? 'bg-green-500'
                          : agent.status === 'coding'
                          ? 'bg-blue-500 animate-pulse'
                          : agent.status === 'waiting'
                          ? 'bg-yellow-500'
                          : 'bg-gray-500'
                      }`} />
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
