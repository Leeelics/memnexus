import { BellIcon } from '@heroicons/react/24/outline'
import { useStore } from '../store/useStore'

export function Header() {
  const { pendingInterventions } = useStore()
  
  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-800">Dashboard</h2>
      </div>
      
      <div className="flex items-center gap-4">
        <button className="relative p-2 text-gray-500 hover:text-gray-700">
          <BellIcon className="w-6 h-6" />
          {pendingInterventions > 0 && (
            <span className="absolute top-1 right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {pendingInterventions}
            </span>
          )}
        </button>
        
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gray-300 rounded-full" />
          <span className="text-sm font-medium text-gray-700">Admin</span>
        </div>
      </div>
    </header>
  )
}
