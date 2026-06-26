export interface PaginatedResponse<T> {
  total: number
  page?: number
  size?: number
  items: T[]
}

export interface Invoice {
  id: string
  invoice_number: string
  invoice_type: string
  date: string
  due_date: string
  status: string
  total: number
  paid_amount: number
  currency: string
  jurisdiction: string
}

export interface Employee {
  id: string
  employee_number: string
  full_name: string
  email: string
  department_id: string | null
  employment_type: string
  hire_date: string
  salary: number | null
  salary_currency: string
  jurisdiction: string
  is_active: boolean
}

export interface Customer {
  id: string
  customer_number: string
  name: string
  customer_type: string
  email: string | null
  country: string | null
  jurisdiction: string
  kyc_status: string
  risk_level: string
  is_sanctioned: boolean
  credit_limit: number | null
}

export interface ComplianceAlert {
  id: string
  alert_type: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  status: string
  title: string
  description: string | null
  match_score: number | null
  created_at: string
}

export interface RegulatoryUpdate {
  id: string
  jurisdiction: string
  category: string
  title: string
  summary: string | null
  source_url: string | null
  severity: string
  requires_action: boolean
  is_read: boolean
  created_at: string
}

export interface SanctionList {
  id: string
  source: string
  last_updated: string | null
  entry_count: number
  is_current: boolean
}
