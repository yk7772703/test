import axios from 'axios'
import { useAuthStore } from '../store/authStore'

export const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Finance
export const financeApi = {
  getDashboard: () => api.get('/finance/dashboard'),
  getAccounts: (params?: object) => api.get('/finance/accounts', { params }),
  getInvoices: (params?: object) => api.get('/finance/invoices', { params }),
  createInvoice: (data: object) => api.post('/finance/invoices', data),
  getInvoice: (id: string) => api.get(`/finance/invoices/${id}`),
  getTaxRates: (params?: object) => api.get('/finance/tax-rates', { params }),
}

// HR
export const hrApi = {
  getDashboard: () => api.get('/hr/dashboard'),
  getEmployees: (params?: object) => api.get('/hr/employees', { params }),
  createEmployee: (data: object) => api.post('/hr/employees', data),
  getEmployee: (id: string) => api.get(`/hr/employees/${id}`),
  getDepartments: () => api.get('/hr/departments'),
  getLeaveRequests: (params?: object) => api.get('/hr/leave-requests', { params }),
  createLeaveRequest: (data: object) => api.post('/hr/leave-requests', data),
  approveLeave: (id: string) => api.patch(`/hr/leave-requests/${id}/approve`),
}

// CRM
export const crmApi = {
  getDashboard: () => api.get('/crm/dashboard'),
  getCustomers: (params?: object) => api.get('/crm/customers', { params }),
  createCustomer: (data: object) => api.post('/crm/customers', data),
  getCustomer: (id: string) => api.get(`/crm/customers/${id}`),
  screenCustomer: (id: string) => api.post(`/crm/customers/${id}/screen-sanctions`),
  getOpportunities: (params?: object) => api.get('/crm/opportunities', { params }),
}

// Compliance
export const complianceApi = {
  getSanctionLists: () => api.get('/compliance/sanctions/lists'),
  triggerSanctionsUpdate: () => api.post('/compliance/sanctions/update'),
  screenName: (name: string, threshold?: number) =>
    api.post('/compliance/sanctions/screen', { name, threshold }),
  getAlerts: (params?: object) => api.get('/compliance/alerts', { params }),
  getAlertStats: () => api.get('/compliance/alerts/stats'),
  updateAlert: (id: string, data: object) => api.patch(`/compliance/alerts/${id}`, data),
  getRegulatoryUpdates: (params?: object) => api.get('/compliance/regulatory-updates', { params }),
  refreshRegulatoryUpdates: () => api.post('/compliance/regulatory-updates/refresh'),
  markUpdateRead: (id: string) => api.patch(`/compliance/regulatory-updates/${id}/read`),
  getAuditLog: (params?: object) => api.get('/compliance/audit-log', { params }),
  getKYCRecords: (params?: object) => api.get('/compliance/kyc', { params }),
}

// Auth
export const authApi = {
  login: (email: string, password: string) => {
    const form = new FormData()
    form.append('username', email)
    form.append('password', password)
    return api.post('/auth/login', form)
  },
  register: (data: object) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
}
