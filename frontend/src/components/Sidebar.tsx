import { NavLink } from 'react-router-dom'
import {
  HomeIcon,
  RectangleStackIcon,
  UsersIcon,
  CircleStackIcon,
  PlayIcon,
  HandRaisedIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'Sessions', href: '/sessions', icon: RectangleStackIcon },
  { name: 'Agents', href: '/agents', icon: UsersIcon },
  { name: 'Memory', href: '/memory', icon: CircleStackIcon },
  { name: 'Orchestration', href: '/orchestration', icon: PlayIcon },
  { name: 'Interventions', href: '/interventions', icon: HandRaisedIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

export function Sidebar() {
  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">M</span>
          </div>
          <div>
            <h1 className="font-bold text-xl text-gray-900">MemNexus</h1>
            <p className="text-xs text-gray-500">Phase 3 - Full Product</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4 space-y-1">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-gray-600 hover:bg-gray-50'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.name}</span>
          </NavLink>
        ))}
      </nav>
      
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-center gap-3 px-4 py-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          <span className="text-sm text-gray-600">System Online</span>
        </div>
      </div>
    </div>
  )
}
