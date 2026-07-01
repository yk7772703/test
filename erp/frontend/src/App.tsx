import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useEffect } from 'react'
import { Layout } from './components/layout/Layout'
import { Login } from './pages/auth/Login'
import { Register } from './pages/auth/Register'
import { Dashboard } from './pages/Dashboard'
import { ComplianceDashboard } from './pages/compliance/ComplianceDashboard'
import { useAuthStore } from './store/authStore'
import { useThemeStore } from './store/themeStore'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30000, retry: 1 },
  },
})

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  if (!isAuthenticated()) return <Navigate to="/login" replace />
  return <>{children}</>
}

function AppInit() {
  const { theme } = useThemeStore()
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
  }, [theme])
  return null
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppInit />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              borderRadius: 4,
              fontSize: 13,
              background: 'var(--toast-bg, #fff)',
              color: 'var(--toast-color, #0a0a0a)',
              border: '1px solid var(--toast-border, #e4e4e7)',
            },
          }}
        />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="finance" element={<PlaceholderPage title="Finance" />} />
            <Route path="finance/invoices" element={<PlaceholderPage title="Invoices" />} />
            <Route path="finance/accounts" element={<PlaceholderPage title="Chart of Accounts" />} />
            <Route path="finance/tax-rates" element={<PlaceholderPage title="Tax Rates" />} />
            <Route path="hr" element={<PlaceholderPage title="HR & Payroll" />} />
            <Route path="hr/employees" element={<PlaceholderPage title="Employees" />} />
            <Route path="hr/departments" element={<PlaceholderPage title="Departments" />} />
            <Route path="hr/leave" element={<PlaceholderPage title="Leave Requests" />} />
            <Route path="hr/payroll" element={<PlaceholderPage title="Payroll" />} />
            <Route path="crm" element={<PlaceholderPage title="CRM" />} />
            <Route path="crm/customers" element={<PlaceholderPage title="Customers" />} />
            <Route path="crm/pipeline" element={<PlaceholderPage title="Sales Pipeline" />} />
            <Route path="crm/contacts" element={<PlaceholderPage title="Contacts" />} />
            <Route path="compliance" element={<ComplianceDashboard />} />
            <Route path="compliance/sanctions" element={<PlaceholderPage title="Sanctions Lists" />} />
            <Route path="compliance/alerts" element={<PlaceholderPage title="Compliance Alerts" />} />
            <Route path="compliance/kyc" element={<PlaceholderPage title="KYC Records" />} />
            <Route path="compliance/regulatory" element={<PlaceholderPage title="Regulatory Updates" />} />
            <Route path="compliance/audit" element={<PlaceholderPage title="Audit Log" />} />
            <Route path="inventory" element={<PlaceholderPage title="Inventory" />} />
            <Route path="reports" element={<PlaceholderPage title="Reports" />} />
            <Route path="settings" element={<PlaceholderPage title="Settings" />} />
            <Route path="notifications" element={<PlaceholderPage title="Notifications" />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-center">
        <h1 className="text-xl font-semibold text-primary-950 dark:text-white mb-2">{title}</h1>
        <p className="text-sm text-primary-400">Module coming soon</p>
      </div>
    </div>
  )
}
