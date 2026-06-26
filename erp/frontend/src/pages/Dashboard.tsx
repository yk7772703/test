import { useQuery } from '@tanstack/react-query'
import { financeApi, hrApi, crmApi, complianceApi } from '../lib/api'
import { StatCard, Card } from '../components/ui/Card'
import { Badge, severityVariant } from '../components/ui/Badge'
import { DollarSign, Users, Building2, ShieldAlert, AlertTriangle, FileCheck } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { useThemeStore } from '../store/themeStore'
import { useAuthStore } from '../store/authStore'

function fmt(n: number) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)
}

export function Dashboard() {
  const { theme } = useThemeStore()
  const { user } = useAuthStore()
  const isDark = theme === 'dark'

  const { data: finance } = useQuery({ queryKey: ['finance-dash'], queryFn: () => financeApi.getDashboard().then(r => r.data) })
  const { data: hr } = useQuery({ queryKey: ['hr-dash'], queryFn: () => hrApi.getDashboard().then(r => r.data) })
  const { data: crm } = useQuery({ queryKey: ['crm-dash'], queryFn: () => crmApi.getDashboard().then(r => r.data) })
  const { data: alertStats } = useQuery({ queryKey: ['alert-stats'], queryFn: () => complianceApi.getAlertStats().then(r => r.data) })
  const { data: alerts } = useQuery({ queryKey: ['alerts-recent'], queryFn: () => complianceApi.getAlerts({ size: 5 }).then(r => r.data) })

  const textColor = isDark ? '#a1a1aa' : '#71717a'
  const gridColor = isDark ? '#27272a' : '#f4f4f5'

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-xl font-semibold text-primary-950 dark:text-white">Dashboard</h1>
        <p className="text-sm text-primary-500 mt-0.5">
          {user?.jurisdiction} · {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
        </p>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Accounts Receivable"
          value={finance ? fmt(finance.accounts_receivable) : '—'}
          icon={<DollarSign size={16} className="text-primary-600 dark:text-primary-400" />}
        />
        <StatCard
          label="Accounts Payable"
          value={finance ? fmt(finance.accounts_payable) : '—'}
          icon={<DollarSign size={16} className="text-primary-600 dark:text-primary-400" />}
        />
        <StatCard
          label="Total Employees"
          value={hr?.total_employees ?? '—'}
          sub={`${hr?.pending_leave_requests ?? 0} pending leaves`}
          icon={<Users size={16} className="text-primary-600 dark:text-primary-400" />}
        />
        <StatCard
          label="Pipeline Value"
          value={crm ? fmt(crm.pipeline_value) : '—'}
          sub={`${crm?.total_customers ?? 0} customers`}
          icon={<Building2 size={16} className="text-primary-600 dark:text-primary-400" />}
        />
      </div>

      {/* Compliance KPIs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Open Alerts"
          value={alertStats?.total_open ?? '—'}
          danger={alertStats?.total_open > 0}
          icon={<ShieldAlert size={16} className="text-red-500" />}
        />
        <StatCard
          label="Critical Alerts"
          value={alertStats?.open_by_severity?.critical ?? 0}
          danger={(alertStats?.open_by_severity?.critical ?? 0) > 0}
          icon={<AlertTriangle size={16} className="text-red-500" />}
        />
        <StatCard
          label="Sanctioned Customers"
          value={crm?.sanctioned_customers ?? '—'}
          danger={(crm?.sanctioned_customers ?? 0) > 0}
          icon={<AlertTriangle size={16} className="text-red-500" />}
        />
        <StatCard
          label="KYC Pending"
          value={crm?.kyc_pending ?? '—'}
          icon={<FileCheck size={16} className="text-primary-600 dark:text-primary-400" />}
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Revenue trend */}
        <Card>
          <h2 className="text-sm font-semibold text-primary-700 dark:text-primary-300 mb-4">Revenue Trend</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={finance?.revenue_trend || []} barSize={24}>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: textColor }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: textColor }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{
                  background: isDark ? '#18181b' : '#fff',
                  border: `1px solid ${isDark ? '#27272a' : '#e4e4e7'}`,
                  borderRadius: 4,
                  fontSize: 12,
                }}
                formatter={(v: number) => [fmt(v), 'Revenue']}
              />
              <Bar dataKey="total" fill={isDark ? '#ffffff' : '#0a0a0a'} radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* HR by department */}
        <Card>
          <h2 className="text-sm font-semibold text-primary-700 dark:text-primary-300 mb-4">Employees by Department</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={hr?.by_department || []} barSize={24} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 11, fill: textColor }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: textColor }} axisLine={false} tickLine={false} width={80} />
              <Tooltip
                contentStyle={{ background: isDark ? '#18181b' : '#fff', border: `1px solid ${isDark ? '#27272a' : '#e4e4e7'}`, borderRadius: 4, fontSize: 12 }}
              />
              <Bar dataKey="count" fill={isDark ? '#ffffff' : '#0a0a0a'} radius={[0, 2, 2, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Recent alerts */}
      <Card padding={false}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-primary-100 dark:border-primary-800">
          <h2 className="text-sm font-semibold text-primary-700 dark:text-primary-300">Recent Compliance Alerts</h2>
          <a href="/compliance/alerts" className="text-xs text-primary-500 hover:text-primary-700 dark:hover:text-primary-300">
            View all →
          </a>
        </div>
        <div className="divide-y divide-primary-100 dark:divide-primary-800">
          {alerts?.items?.length === 0 && (
            <p className="px-5 py-6 text-sm text-primary-400 text-center">No open alerts</p>
          )}
          {(alerts?.items || []).map((alert: any) => (
            <div key={alert.id} className="flex items-center justify-between px-5 py-3">
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-primary-900 dark:text-white truncate">{alert.title}</p>
                <p className="text-xs text-primary-500 mt-0.5">
                  {new Date(alert.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-2 ml-4">
                <Badge variant={severityVariant(alert.severity)}>{alert.severity}</Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}
