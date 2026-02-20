import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { CheckIcon, XMarkIcon, ClockIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

// Mock API - would be replaced with real interventions API
const mockInterventions = [
  {
    id: 'int_001',
    type: 'approval',
    title: 'Review Database Schema',
    description: 'Agent has proposed database schema changes. Please review before proceeding.',
    session_id: 'sess_123',
    task_id: 'task_456',
    status: 'waiting_for_human',
    created_at: '2026-02-20T10:30:00Z',
    deadline: '2026-02-20T11:30:00Z',
  },
  {
    id: 'int_002',
    type: 'decision',
    title: 'Select Frontend Framework',
    description: 'Which framework should we use for the frontend?',
    session_id: 'sess_124',
    task_id: 'task_789',
    status: 'pending',
    created_at: '2026-02-20T11:00:00Z',
    options: [
      { id: 'react', label: 'React', action: 'select_react' },
      { id: 'vue', label: 'Vue', action: 'select_vue' },
      { id: 'svelte', label: 'Svelte', action: 'select_svelte' },
    ],
  },
]

export function Interventions() {
  const queryClient = useQueryClient()
  const [selectedIntervention, setSelectedIntervention] = useState<any>(null)
  
  // In real implementation:
  // const { data: interventions } = useQuery('interventions', () => interventionsApi.list())
  const interventions = mockInterventions
  
  const resolveMutation = useMutation(
    ({ id, resolution }: { id: string; resolution: any }) =>
      Promise.resolve({ success: true }),
    {
      onSuccess: () => {
        toast.success('Intervention resolved')
        setSelectedIntervention(null)
      },
    }
  )
  
  const handleResolve = (action: string) => {
    if (selectedIntervention) {
      resolveMutation.mutate({
        id: selectedIntervention.id,
        resolution: { action },
      })
    }
  }
  
  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'approval':
        return <CheckIcon className="w-5 h-5 text-blue-500" />
      case 'decision':
        return <ClockIcon className="w-5 h-5 text-yellow-500" />
      default:
        return <ClockIcon className="w-5 h-5 text-gray-500" />
    }
  }
  
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Human Interventions</h1>
        <p className="text-gray-500 mt-1">Review and respond to agent requests</p>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Pending</p>
          <p className="text-2xl font-bold text-gray-900">
            {interventions.filter((i) => i.status === 'pending').length}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Waiting</p>
          <p className="text-2xl font-bold text-yellow-600">
            {interventions.filter((i) => i.status === 'waiting_for_human').length}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Approved</p>
          <p className="text-2xl font-bold text-green-600">
            {interventions.filter((i) => i.status === 'approved').length}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Rejected</p>
          <p className="text-2xl font-bold text-red-600">
            {interventions.filter((i) => i.status === 'rejected').length}
          </p>
        </div>
      </div>
      
      {/* Interventions List */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Interventions</h3>
        <div className="space-y-4">
          {interventions.map((intervention) => (
            <div
              key={intervention.id}
              className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 cursor-pointer transition-colors"
              onClick={() => setSelectedIntervention(intervention)}
            >
              <div className="flex items-start gap-4">
                <div className="mt-1">{getTypeIcon(intervention.type)}</div>
                <div className="flex-1">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-gray-900">{intervention.title}</h4>
                      <p className="text-sm text-gray-500 mt-1">{intervention.description}</p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      intervention.status === 'waiting_for_human'
                        ? 'bg-yellow-100 text-yellow-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {intervention.status}
                    </span>
                  </div>
                  <div className="flex gap-4 mt-3 text-sm text-gray-500">
                    <span>Session: {intervention.session_id}</span>
                    <span>Task: {intervention.task_id}</span>
                    {intervention.deadline && (
                      <span className="text-red-500">
                        Deadline: {new Date(intervention.deadline).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Intervention Detail Modal */}
      {selectedIntervention && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl p-6 w-full max-w-lg">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-lg font-semibold">{selectedIntervention.title}</h3>
              <button
                onClick={() => setSelectedIntervention(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            
            <p className="text-gray-600 mb-6">{selectedIntervention.description}</p>
            
            {selectedIntervention.options && (
              <div className="space-y-2 mb-6">
                {selectedIntervention.options.map((option: any) => (
                  <button
                    key={option.id}
                    onClick={() => handleResolve(option.action)}
                    className="w-full text-left p-3 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-colors"
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            )}
            
            <div className="flex justify-end gap-3">
              <button
                onClick={() => handleResolve('reject')}
                className="btn-secondary"
              >
                Reject
              </button>
              <button
                onClick={() => handleResolve('approve')}
                className="btn-primary"
              >
                Approve
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
