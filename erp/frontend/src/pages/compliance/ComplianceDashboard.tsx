import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { complianceApi } from '../../lib/api'
import { StatCard, Card } from '../../components/ui/Card'
import { Badge, severityVariant, statusVariant } from '../../components/ui/Badge'
import { ShieldAlert, RefreshCw, Search, AlertTriangle, CheckCircle, Clock, Globe } from 'lucide-react'
import { useState } from 'react'
import toast from 'react-hot-toast'

export function ComplianceDashboard() {
  const qc = useQueryClient()
  const [screenName, setScreenName] = useState('')
  const [screenResults, setScreenResults] = useState<any[]>([])
  const [screening, setScreening] = useState(false)

  const { data: alertStats } = useQuery({
    queryKey: ['alert-stats'],
    queryFn: () => complianceApi.getAlertStats().then(r => r.data),
    refetchInterval: 30000,
  })

  const { data: sanctionLists } = useQuery({
    queryKey: ['sanction-lists'],
    queryFn: () => complianceApi.getSanctionLists().then(r => r.data),
  })

  const { data: regUpdates } = useQuery({
    queryKey: ['reg-updates', { size: 5 }],
    queryFn: () => complianceApi.getRegulatoryUpdates({ size: 5, unread_only: true }).then(r => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: () => complianceApi.triggerSanctionsUpdate(),
    onSuccess: () => { toast.success('Sanctions update triggered'); qc.invalidateQueries({ queryKey: ['sanction-lists'] }) },
    onError: () => toast.error('Failed to trigger update'),
  })

  const refreshRegMutation = useMutation({
    mutationFn: () => complianceApi.refreshRegulatoryUpdates(),
    onSuccess: () => { toast.success('Regulatory feed refreshed'); qc.invalidateQueries({ queryKey: ['reg-updates'] }) },
    onError: () => toast.error('Failed to refresh'),
  })

  async function handleScreen() {
    if (!screenName.trim()) return
    setScreening(true)
    try {
      const res = await complianceApi.screenName(screenName.trim())
      setScreenResults(res.data.matches)
    } catch {
      toast.error('Screening failed')
    } finally {
      setScreening(false)
    }
  }

  const sourceLabels: Record<string, string> = {
    OFAC_SDN: '🇺🇸 OFAC SDN',
    OFAC_CONS: '🇺🇸 OFAC Consolidated',
    UN: '🌐 UN Security Council',
    EU: '🇪🇺 EU Sanctions',
    UK_HMT: '🇬🇧 UK UKSL',
    CANADA_SEMA: '🇨🇦 Canada SEMA',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-primary-950 dark:text-white">Compliance</h1>
          <p className="text-sm text-primary-500 mt-0.5">Sanctions screening · KYC/AML · Regulatory updates</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => refreshRegMutation.mutate()}
            disabled={refreshRegMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-primary-200 dark:border-primary-700 rounded hover:bg-primary-50 dark:hover:bg-primary-800 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={refreshRegMutation.isPending ? 'animate-spin' : ''} />
            Refresh Feeds
          </button>
          <button
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-primary-950 dark:bg-white text-white dark:text-primary-950 rounded hover:opacity-90 disabled:opacity-50"
          >
            <RefreshCw size={14} className={updateMutation.isPending ? 'animate-spin' : ''} />
            Update Sanctions
          </button>
        </div>
      </div>

      {/* Alert stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Open Alerts" value={alertStats?.total_open ?? '—'} danger={(alertStats?.total_open ?? 0) > 0} icon={<ShieldAlert size={16} />} />
        <StatCard label="Critical" value={alertStats?.open_by_severity?.critical ?? 0} danger={(alertStats?.open_by_severity?.critical ?? 0) > 0} icon={<AlertTriangle size={16} />} />
        <StatCard label="Under Review" value={alertStats?.by_status?.under_review ?? 0} icon={<Clock size={16} />} />
        <StatCard label="Resolved (Total)" value={alertStats?.by_status?.resolved ?? 0} icon={<CheckCircle size={16} />} />
      </div>

      {/* Name screening */}
      <Card>
        <h2 className="text-sm font-semibold text-primary-700 dark:text-primary-300 mb-4">
          <Search size={14} className="inline mr-1.5" />
          Real-time Sanctions Screening
        </h2>
        <div className="flex gap-2">
          <input
            value={screenName}
            onChange={e => setScreenName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleScreen()}
            placeholder="Enter name to screen against all lists..."
            className="flex-1 px-3 py-2 text-sm border border-primary-200 dark:border-primary-700 rounded bg-white dark:bg-primary-900 text-primary-950 dark:text-white placeholder-primary-400 focus:outline-none focus:ring-1 focus:ring-primary-950 dark:focus:ring-white"
          />
          <button
            onClick={handleScreen}
            disabled={screening}
            className="px-4 py-2 text-sm bg-primary-950 dark:bg-white text-white dark:text-primary-950 rounded hover:opacity-90 disabled:opacity-50 flex items-center gap-1.5"
          >
            {screening ? <RefreshCw size={14} className="animate-spin" /> : <Search size={14} />}
            Screen
          </button>
        </div>

        {screenResults.length > 0 && (
          <div className="mt-4 space-y-2">
            <p className="text-xs font-medium text-primary-500">
              Found {screenResults.length} match{screenResults.length !== 1 ? 'es' : ''}
            </p>
            {screenResults.map((m, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20">
                <div>
                  <p className="text-sm font-medium text-red-900 dark:text-red-300">{m.matched_name}</p>
                  <p className="text-xs text-red-700 dark:text-red-400 mt-0.5">
                    {sourceLabels[m.source] || m.source} · {m.entity_type}
                    {m.programs?.length > 0 && ` · ${m.programs.join(', ')}`}
                  </p>
                </div>
                <span className="text-sm font-mono font-semibold text-red-700 dark:text-red-400">
                  {(m.score * 100).toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        )}

        {screenResults.length === 0 && screenName && !screening && (
          <div className="mt-4 p-3 rounded border border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20">
            <p className="text-sm text-green-800 dark:text-green-300">
              <CheckCircle size={14} className="inline mr-1.5" />
              No matches found — name is clear across all lists
            </p>
          </div>
        )}
      </Card>

      {/* Sanction lists status */}
      <Card padding={false}>
        <div className="px-5 py-4 border-b border-primary-100 dark:border-primary-800">
          <h2 className="text-sm font-semibold text-primary-700 dark:text-primary-300">
            <Globe size={14} className="inline mr-1.5" />
            Sanction Lists Status
          </h2>
        </div>
        <div className="divide-y divide-primary-100 dark:divide-primary-800">
          {(sanctionLists || []).map((list: any) => (
            <div key={list.id} className="flex items-center justify-between px-5 py-3">
              <div>
                <p className="text-sm font-medium text-primary-900 dark:text-white">
                  {sourceLabels[list.source] || list.source}
                </p>
                <p className="text-xs text-primary-500 mt-0.5">
                  {list.entry_count.toLocaleString()} entries ·{' '}
                  {list.last_updated
                    ? `Updated ${new Date(list.last_updated).toLocaleDateString()}`
                    : 'Never updated'}
                </p>
              </div>
              <Badge variant={list.is_current ? 'success' : 'warning'}>
                {list.is_current ? 'Current' : 'Outdated'}
              </Badge>
            </div>
          ))}
          {(!sanctionLists || sanctionLists.length === 0) && (
            <p className="px-5 py-6 text-sm text-primary-400 text-center">
              No sanctions lists loaded yet. Click "Update Sanctions" to fetch.
            </p>
          )}
        </div>
      </Card>

      {/* Regulatory updates */}
      <Card padding={false}>
        <div className="flex items-center justify-between px-5 py-4 border-b border-primary-100 dark:border-primary-800">
          <h2 className="text-sm font-semibold text-primary-700 dark:text-primary-300">
            Unread Regulatory Updates
          </h2>
          <a href="/compliance/regulatory" className="text-xs text-primary-500 hover:text-primary-700 dark:hover:text-primary-300">
            View all →
          </a>
        </div>
        <div className="divide-y divide-primary-100 dark:divide-primary-800">
          {(regUpdates?.items || []).map((u: any) => (
            <div key={u.id} className="px-5 py-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-primary-900 dark:text-white line-clamp-1">{u.title}</p>
                  <p className="text-xs text-primary-500 mt-0.5">
                    {u.jurisdiction} · {u.category} · {new Date(u.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div className="flex gap-1.5 shrink-0">
                  <Badge variant={severityVariant(u.severity)}>{u.severity}</Badge>
                  {u.requires_action && <Badge variant="danger">Action Required</Badge>}
                </div>
              </div>
            </div>
          ))}
          {(!regUpdates?.items || regUpdates.items.length === 0) && (
            <p className="px-5 py-6 text-sm text-primary-400 text-center">All caught up!</p>
          )}
        </div>
      </Card>
    </div>
  )
}
