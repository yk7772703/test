import clsx from 'clsx'
import { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  padding?: boolean
}

export function Card({ children, className, padding = true }: CardProps) {
  return (
    <div
      className={clsx(
        'bg-white dark:bg-primary-900 border border-primary-200 dark:border-primary-800 rounded-lg shadow-subtle',
        padding && 'p-5',
        className
      )}
    >
      {children}
    </div>
  )
}

interface StatCardProps {
  label: string
  value: string | number
  sub?: string
  trend?: 'up' | 'down' | 'neutral'
  icon?: ReactNode
  danger?: boolean
}

export function StatCard({ label, value, sub, icon, danger }: StatCardProps) {
  return (
    <Card>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-primary-500 dark:text-primary-400 uppercase tracking-wider mb-1">
            {label}
          </p>
          <p className={clsx(
            'text-2xl font-semibold tabular-nums',
            danger ? 'text-red-600 dark:text-red-400' : 'text-primary-950 dark:text-white'
          )}>
            {value}
          </p>
          {sub && <p className="text-xs text-primary-400 mt-1">{sub}</p>}
        </div>
        {icon && (
          <div className="p-2 bg-primary-100 dark:bg-primary-800 rounded">
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
}
