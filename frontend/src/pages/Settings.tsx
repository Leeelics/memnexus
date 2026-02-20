import { Cog6ToothIcon } from '@heroicons/react/24/outline'

export function Settings() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Configure MemNexus</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">General</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Data Directory
              </label>
              <input
                type="text"
                value="~/.memnexus"
                readOnly
                className="input bg-gray-50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Strategy
              </label>
              <select className="input">
                <option>Sequential</option>
                <option>Parallel</option>
                <option>Review</option>
                <option>Auto</option>
              </select>
            </div>
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Agents</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Default Timeout (seconds)
              </label>
              <input
                type="number"
                defaultValue={300}
                className="input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Retries
              </label>
              <input
                type="number"
                defaultValue={3}
                className="input"
              />
            </div>
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Memory</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                LanceDB URI
              </label>
              <input
                type="text"
                value="~/.memnexus/memory.lance"
                readOnly
                className="input bg-gray-50"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Auto Sync</span>
              <button className="relative inline-flex h-6 w-11 items-center rounded-full bg-blue-500">
                <span className="translate-x-6 inline-block h-4 w-4 transform rounded-full bg-white" />
              </button>
            </div>
          </div>
        </div>
        
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">About</h3>
          <div className="space-y-2 text-sm text-gray-600">
            <div className="flex justify-between">
              <span>Version</span>
              <span className="font-medium">0.1.0</span>
            </div>
            <div className="flex justify-between">
              <span>Phase</span>
              <span className="font-medium">Phase 3 - Full Product</span>
            </div>
            <div className="flex justify-between">
              <span>License</span>
              <span className="font-medium">MIT</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
