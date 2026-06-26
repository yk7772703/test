import { Sun, Moon, Menu, Bell, ChevronDown, LogOut, User } from 'lucide-react'
import { useThemeStore } from '../../store/themeStore'
import { useAuthStore } from '../../store/authStore'
import { useState } from 'react'
import clsx from 'clsx'

interface HeaderProps {
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { theme, toggle } = useThemeStore()
  const { user, logout } = useAuthStore()
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  return (
    <header className="h-16 border-b border-primary-200 dark:border-primary-800 bg-white dark:bg-primary-950 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-10">
      {/* Left */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuClick}
          className="lg:hidden p-2 rounded hover:bg-primary-100 dark:hover:bg-primary-800 transition-colors"
        >
          <Menu size={18} className="text-primary-600 dark:text-primary-400" />
        </button>
        <div className="hidden lg:flex items-center gap-2">
          <span className="text-xs text-primary-400 dark:text-primary-500">Jurisdiction:</span>
          <JurisdictionBadge jurisdiction={user?.jurisdiction || 'US'} />
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2">
        {/* Notifications */}
        <button className="relative p-2 rounded hover:bg-primary-100 dark:hover:bg-primary-800 transition-colors">
          <Bell size={16} className="text-primary-600 dark:text-primary-400" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-red-500 rounded-full" />
        </button>

        {/* Theme toggle */}
        <button
          onClick={toggle}
          className="p-2 rounded hover:bg-primary-100 dark:hover:bg-primary-800 transition-colors"
          aria-label="Toggle theme"
        >
          {theme === 'dark'
            ? <Sun size={16} className="text-primary-400" />
            : <Moon size={16} className="text-primary-600" />
          }
        </button>

        {/* User menu */}
        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 pl-2 pr-3 py-1.5 rounded hover:bg-primary-100 dark:hover:bg-primary-800 transition-colors"
          >
            <div className="w-7 h-7 rounded-full bg-primary-950 dark:bg-white flex items-center justify-center">
              <User size={13} className="text-white dark:text-primary-950" />
            </div>
            <span className="hidden sm:block text-sm font-medium text-primary-700 dark:text-primary-300">
              {user?.full_name || user?.username || 'User'}
            </span>
            <ChevronDown size={14} className="text-primary-400" />
          </button>

          {userMenuOpen && (
            <div className="absolute right-0 top-full mt-1 w-52 bg-white dark:bg-primary-900 border border-primary-200 dark:border-primary-700 rounded-lg shadow-card dark:shadow-card-dark py-1 z-50">
              <div className="px-3 py-2 border-b border-primary-100 dark:border-primary-800">
                <p className="text-sm font-medium text-primary-900 dark:text-white">{user?.full_name}</p>
                <p className="text-xs text-primary-500">{user?.email}</p>
              </div>
              <button
                onClick={() => { logout(); window.location.href = '/login' }}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-primary-700 dark:text-primary-300 hover:bg-primary-50 dark:hover:bg-primary-800 transition-colors"
              >
                <LogOut size={14} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}

function JurisdictionBadge({ jurisdiction }: { jurisdiction: string }) {
  const labels: Record<string, string> = { US: '🇺🇸 United States', UK: '🇬🇧 United Kingdom', CA: '🇨🇦 Canada' }
  return (
    <span className="text-xs font-medium px-2 py-0.5 rounded bg-primary-100 dark:bg-primary-800 text-primary-700 dark:text-primary-300">
      {labels[jurisdiction] || jurisdiction}
    </span>
  )
}
