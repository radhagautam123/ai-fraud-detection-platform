import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/alerts', label: 'Alerts', icon: '🚨' },
  { to: '/transactions', label: 'Transactions', icon: '💳' },
  { to: '/model-monitoring', label: 'Model Monitoring', icon: '🧠' },
  { to: '/audit-logs', label: 'Audit Logs', icon: '📋' },
]

const roleBadge = {
  ADMIN: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  ANALYST: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  VIEWER: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
}

export default function Layout({ children }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100">
      <aside className="w-64 bg-gray-950 border-r border-gray-800 flex flex-col flex-shrink-0">
        <div className="p-5 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <span className="text-xl">🛡️</span>
            <div>
              <h1 className="text-base font-bold tracking-tight text-white">Fraud Detection</h1>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest">Investigation Platform</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-fraud-600/20 text-fraud-400 border border-fraud-500/20'
                    : 'text-gray-400 hover:bg-gray-800/50 hover:text-gray-200 border border-transparent'
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-gray-800 space-y-2">
          {user && (
            <div className="flex items-center gap-3 px-3 py-2">
              <div className="w-8 h-8 rounded-full bg-gray-800 flex items-center justify-center text-sm font-medium text-gray-300">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">{user.username}</p>
                <span className={`inline-block text-[10px] px-1.5 py-0.5 rounded border ${roleBadge[user.role] || roleBadge.VIEWER}`}>
                  {user.role}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="text-gray-500 hover:text-gray-300 text-xs transition-colors"
                title="Sign out"
              >
                ⏻
              </button>
            </div>
          )}
        </div>
      </aside>

      <main className="flex-1 overflow-auto">
        <div className="p-6 max-w-7xl mx-auto">{children}</div>
      </main>
    </div>
  )
}
