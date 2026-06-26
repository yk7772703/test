import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, DollarSign, Users, Building2,
  ShieldCheck, FileText, BarChart3, Package,
  Bell, Settings, ChevronRight, X
} from 'lucide-react'
import clsx from 'clsx'

const NAV = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/' },
  {
    label: 'Finance', icon: DollarSign, to: '/finance',
    children: [
      { label: 'Overview', to: '/finance' },
      { label: 'Invoices', to: '/finance/invoices' },
      { label: 'Accounts', to: '/finance/accounts' },
      { label: 'Tax Rates', to: '/finance/tax-rates' },
    ],
  },
  {
    label: 'HR & Payroll', icon: Users, to: '/hr',
    children: [
      { label: 'Employees', to: '/hr/employees' },
      { label: 'Departments', to: '/hr/departments' },
      { label: 'Leave Requests', to: '/hr/leave' },
      { label: 'Payroll', to: '/hr/payroll' },
    ],
  },
  {
    label: 'CRM', icon: Building2, to: '/crm',
    children: [
      { label: 'Customers', to: '/crm/customers' },
      { label: 'Pipeline', to: '/crm/pipeline' },
      { label: 'Contacts', to: '/crm/contacts' },
    ],
  },
  {
    label: 'Compliance', icon: ShieldCheck, to: '/compliance',
    children: [
      { label: 'Dashboard', to: '/compliance' },
      { label: 'Sanctions Lists', to: '/compliance/sanctions' },
      { label: 'Alerts', to: '/compliance/alerts' },
      { label: 'KYC Records', to: '/compliance/kyc' },
      { label: 'Regulatory Updates', to: '/compliance/regulatory' },
      { label: 'Audit Log', to: '/compliance/audit' },
    ],
  },
  { label: 'Inventory', icon: Package, to: '/inventory' },
  { label: 'Reports', icon: BarChart3, to: '/reports' },
]

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-20 bg-black/50 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={clsx(
          'fixed top-0 left-0 z-30 h-full w-64 flex flex-col',
          'bg-white dark:bg-primary-950 border-r border-primary-200 dark:border-primary-800',
          'transition-transform duration-200 ease-in-out',
          open ? 'translate-x-0' : '-translate-x-full',
          'lg:translate-x-0 lg:static lg:z-auto'
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-primary-200 dark:border-primary-800">
          <div className="flex items-center gap-2">
            <ShieldCheck size={20} className="text-primary-950 dark:text-white" />
            <span className="font-semibold text-sm tracking-tight text-primary-950 dark:text-white">
              ComplianceERP
            </span>
          </div>
          <button onClick={onClose} className="lg:hidden p-1 rounded hover:bg-primary-100 dark:hover:bg-primary-800">
            <X size={16} className="text-primary-500" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-4 px-3">
          {NAV.map((item) => (
            <NavItem key={item.to} item={item} />
          ))}
        </nav>

        {/* Bottom links */}
        <div className="border-t border-primary-200 dark:border-primary-800 p-3 space-y-1">
          <SideLink to="/notifications" icon={Bell} label="Notifications" />
          <SideLink to="/settings" icon={Settings} label="Settings" />
        </div>
      </aside>
    </>
  )
}

function NavItem({ item }: { item: typeof NAV[0] }) {
  const Icon = item.icon

  if (!item.children) {
    return (
      <NavLink
        to={item.to}
        end
        className={({ isActive }) =>
          clsx(
            'flex items-center gap-3 px-3 py-2 rounded text-sm font-medium mb-0.5 transition-colors',
            isActive
              ? 'bg-primary-950 dark:bg-white text-white dark:text-primary-950'
              : 'text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-800 hover:text-primary-950 dark:hover:text-white'
          )
        }
      >
        <Icon size={16} />
        {item.label}
      </NavLink>
    )
  }

  return (
    <div className="mb-1">
      <div className="flex items-center gap-3 px-3 py-2 text-xs font-semibold uppercase tracking-wider text-primary-400 dark:text-primary-500 mb-1">
        <Icon size={14} />
        {item.label}
      </div>
      <div className="pl-4 space-y-0.5">
        {item.children.map((child) => (
          <NavLink
            key={child.to}
            to={child.to}
            end={child.to === item.to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-2 px-3 py-1.5 rounded text-sm transition-colors',
                isActive
                  ? 'bg-primary-950 dark:bg-white text-white dark:text-primary-950 font-medium'
                  : 'text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-800 hover:text-primary-950 dark:hover:text-white'
              )
            }
          >
            <ChevronRight size={12} className="opacity-50" />
            {child.label}
          </NavLink>
        ))}
      </div>
    </div>
  )
}

function SideLink({ to, icon: Icon, label }: { to: string; icon: any; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-3 px-3 py-2 rounded text-sm transition-colors',
          isActive
            ? 'bg-primary-950 dark:bg-white text-white dark:text-primary-950'
            : 'text-primary-600 dark:text-primary-400 hover:bg-primary-100 dark:hover:bg-primary-800'
        )
      }
    >
      <Icon size={16} />
      {label}
    </NavLink>
  )
}
