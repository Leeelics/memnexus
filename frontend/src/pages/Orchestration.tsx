import { useState } from 'react'
import { PlayIcon, PauseIcon, StopIcon, PlusIcon } from '@heroicons/react/24/outline'

// Mock data for visualization
const mockTasks = [
  { id: 'task_1', name: 'Design Architecture', role: 'architect', status: 'completed', dependencies: [] },
  { id: 'task_2', name: 'Design Database', role: 'architect', status: 'completed', dependencies: ['task_1'] },
  { id: 'task_3', name: 'Implement API', role: 'backend', status: 'running', dependencies: ['task_2'] },
  { id: 'task_4', name: 'Implement Frontend', role: 'frontend', status: 'pending', dependencies: ['task_1'] },
  { id: 'task_5', name: 'Write Tests', role: 'tester', status: 'pending', dependencies: ['task_3', 'task_4'] },
]

export function Orchestration() {
  const [isExecuting, setIsExecuting] = useState(false)
  const [progress, setProgress] = useState(0.4)
  
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Orchestration</h1>
          <p className="text-gray-500 mt-1">Manage multi-agent task execution</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setIsExecuting(!isExecuting)}
            className="btn-primary flex items-center gap-2"
          >
            {isExecuting ? (
              <>
                <PauseIcon className="w-5 h-5" />
                Pause
              </>
            ) : (
              <>
                <PlayIcon className="w-5 h-5" />
                Execute
              </>
            )}
          </button>
          <button className="btn-danger flex items-center gap-2">
            <StopIcon className="w-5 h-5" />
            Stop
          </button>
        </div>
      </div>
      
      {/* Progress */}
      <div className="card">
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-semibold text-gray-900">Execution Progress</h3>
          <span className="text-sm text-gray-500">{(progress * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress * 100}%` }}
          />
        </div>
      </div>
      
      {/* Task Flow Visualization */}
      <div className="card">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold text-gray-900">Task Flow</h3>
          <button className="btn-secondary flex items-center gap-2 text-sm">
            <PlusIcon className="w-4 h-4" />
            Add Task
          </button>
        </div>
        
        <div className="space-y-4">
          {mockTasks.map((task) => (
            <div
              key={task.id}
              className={`p-4 rounded-lg border-2 transition-all ${
                task.status === 'completed'
                  ? 'bg-green-50 border-green-200'
                  : task.status === 'running'
                  ? 'bg-blue-50 border-blue-300'
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-center gap-4">
                <div className={`w-3 h-3 rounded-full ${
                  task.status === 'completed'
                    ? 'bg-green-500'
                    : task.status === 'running'
                    ? 'bg-blue-500 animate-pulse'
                    : 'bg-gray-300'
                }`} />
                <div className="flex-1">
                  <div className="flex justify-between items-center">
                    <h4 className="font-medium text-gray-900">{task.name}</h4>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      task.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : task.status === 'running'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-gray-100 text-gray-700'
                    }`}>
                      {task.status}
                    </span>
                  </div>
                  <div className="flex gap-4 mt-2 text-sm text-gray-500">
                    <span>Role: <span className="text-gray-700">{task.role}</span></span>
                    {task.dependencies.length > 0 && (
                      <span>Dependencies: {task.dependencies.join(', ')}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Execution Strategy */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Execution Strategy</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {['sequential', 'parallel', 'review', 'auto'].map((strategy) => (
            <button
              key={strategy}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                strategy === 'sequential'
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <h4 className="font-medium text-gray-900 capitalize">{strategy}</h4>
              <p className="text-sm text-gray-500 mt-1">
                {strategy === 'sequential' && 'Execute tasks one by one'}
                {strategy === 'parallel' && 'Execute tasks in parallel'}
                {strategy === 'review' && 'Execute with review cycles'}
                {strategy === 'auto' && 'Auto-select optimal strategy'}
              </p>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
