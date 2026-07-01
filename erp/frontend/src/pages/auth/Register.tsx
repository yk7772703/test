import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { authApi } from '../../lib/api'
import { useAuthStore } from '../../store/authStore'
import { useThemeStore } from '../../store/themeStore'
import { ShieldCheck, Sun, Moon } from 'lucide-react'
import toast from 'react-hot-toast'

export function Register() {
  const navigate = useNavigate()
  const { login, isAuthenticated } = useAuthStore()
  const { theme, toggle } = useThemeStore()
  const [fullName, setFullName] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [jurisdiction, setJurisdiction] = useState('US')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (isAuthenticated()) navigate('/')
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await authApi.register({ email, username, password, full_name: fullName, jurisdiction })
      const data = res.data
      login(data.access_token, {
        id: data.user_id,
        email: data.email,
        username: data.email,
        full_name: data.full_name,
        jurisdiction,
      })
      navigate('/')
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-primary-50 dark:bg-primary-950 flex flex-col items-center justify-center px-4">
      <button
        onClick={toggle}
        className="absolute top-4 right-4 p-2 rounded hover:bg-primary-100 dark:hover:bg-primary-800 transition-colors"
      >
        {theme === 'dark'
          ? <Sun size={16} className="text-primary-400" />
          : <Moon size={16} className="text-primary-600" />
        }
      </button>

      <div className="w-full max-w-sm">
        <div className="flex items-center justify-center gap-2 mb-8">
          <ShieldCheck size={24} className="text-primary-950 dark:text-white" />
          <span className="text-lg font-semibold text-primary-950 dark:text-white">ComplianceERP</span>
        </div>

        <div className="bg-white dark:bg-primary-900 border border-primary-200 dark:border-primary-800 rounded-lg p-8 shadow-card">
          <h1 className="text-base font-semibold text-primary-950 dark:text-white mb-1">Create account</h1>
          <p className="text-sm text-primary-500 mb-6">Enterprise ERP · US / UK / Canada</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-primary-700 dark:text-primary-300 mb-1">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={e => setFullName(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-primary-200 dark:border-primary-700 rounded bg-white dark:bg-primary-950 text-primary-950 dark:text-white placeholder-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-950 dark:focus:ring-white"
                placeholder="John Smith"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-primary-700 dark:text-primary-300 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={e => setUsername(e.target.value)}
                required
                autoFocus
                className="w-full px-3 py-2 text-sm border border-primary-200 dark:border-primary-700 rounded bg-white dark:bg-primary-950 text-primary-950 dark:text-white placeholder-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-950 dark:focus:ring-white"
                placeholder="johnsmith"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-primary-700 dark:text-primary-300 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
                className="w-full px-3 py-2 text-sm border border-primary-200 dark:border-primary-700 rounded bg-white dark:bg-primary-950 text-primary-950 dark:text-white placeholder-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-950 dark:focus:ring-white"
                placeholder="you@company.com"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-primary-700 dark:text-primary-300 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2 text-sm border border-primary-200 dark:border-primary-700 rounded bg-white dark:bg-primary-950 text-primary-950 dark:text-white placeholder-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-950 dark:focus:ring-white"
                placeholder="••••••••"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-primary-700 dark:text-primary-300 mb-1">Jurisdiction</label>
              <select
                value={jurisdiction}
                onChange={e => setJurisdiction(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-primary-200 dark:border-primary-700 rounded bg-white dark:bg-primary-950 text-primary-950 dark:text-white focus:outline-none focus:ring-1 focus:ring-primary-950 dark:focus:ring-white"
              >
                <option value="US">🇺🇸 United States</option>
                <option value="UK">🇬🇧 United Kingdom</option>
                <option value="CA">🇨🇦 Canada</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 text-sm font-medium bg-primary-950 dark:bg-white text-white dark:text-primary-950 rounded hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="text-xs text-center text-primary-400 mt-4">
            Already have an account?{' '}
            <a href="/login" className="text-primary-700 dark:text-primary-300 hover:underline">Sign in</a>
          </p>
        </div>

        <p className="text-xs text-center text-primary-400 mt-6">
          SOX · GDPR · AML · OFAC · KYC · CASL · PIPEDA
        </p>
      </div>
    </div>
  )
}
