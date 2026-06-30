import clsx from 'clsx'

type Variant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'ghost'

const variants: Record<Variant, string> = {
  default: 'bg-primary-100 dark:bg-primary-800 text-primary-700 dark:text-primary-300',
  success: 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800',
  warning: 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-800',
  danger: 'bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-800',
  info: 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 border border-blue-200 dark:border-blue-800',
  ghost: 'border border-primary-200 dark:border-primary-700 text-primary-600 dark:text-primary-400',
}

interface BadgeProps {
  children: React.ReactNode
  variant?: Variant
  className?: string
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded text-xs font-medium', variants[variant], className)}>
      {children}
    </span>
  )
}

export function severityVariant(severity: string): Variant {
  switch (severity) {
    case 'critical': return 'danger'
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'info'
    default: return 'default'
  }
}

export function statusVariant(status: string): Variant {
  switch (status) {
    case 'open': return 'danger'
    case 'under_review': return 'warning'
    case 'resolved': return 'success'
    case 'false_positive': return 'ghost'
    case 'escalated': return 'danger'
    case 'paid': return 'success'
    case 'draft': return 'ghost'
    case 'sent': return 'info'
    case 'overdue': return 'danger'
    case 'approved': return 'success'
    case 'pending': return 'warning'
    case 'rejected': return 'danger'
    default: return 'default'
  }
}
