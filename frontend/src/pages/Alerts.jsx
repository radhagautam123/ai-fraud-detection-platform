import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAlerts } from '../api/api'

const STATUSES = ['ALL', 'NEW', 'ASSIGNED', 'INVESTIGATING', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'CLOSED']
const TIERS = ['ALL', 'HIGH', 'CRITICAL']

const investigationBadge = {
  NEW: 'badge-unresolved',
  ASSIGNED: 'badge-investigating',
  INVESTIGATING: 'badge-investigating',
  CONFIRMED_FRAUD: 'badge-critical',
  FALSE_POSITIVE: 'badge-resolved',
  CLOSED: 'badge-resolved',
}

const tierBadge = {
  HIGH: 'badge-high',
  CRITICAL: 'badge-critical',
}

const PAGE_SIZE = 20

export default function Alerts() {
  const navigate = useNavigate()
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)

  const [statusFilter, setStatusFilter] = useState('ALL')
  const [tierFilter, setTierFilter] = useState('ALL')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const params = {}
  if (statusFilter !== 'ALL') params.investigation_status = statusFilter
  if (tierFilter !== 'ALL') params.risk_tier = tierFilter
  if (dateFrom) params.date_from = dateFrom
  if (dateTo) params.date_to = dateTo

  const fetchPage = useCallback((p) => {
    setLoading(true)
    getAlerts({ limit: PAGE_SIZE, offset: p * PAGE_SIZE, ...params })
      .then((res) => {
        setAlerts(res.data || [])
        setTotal(res.total || 0)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [params])

  useEffect(() => {
    setPage(0)
    fetchPage(0)
  }, [statusFilter, tierFilter, dateFrom, dateTo])

  useEffect(() => {
    fetchPage(page)
  }, [page])

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Alerts</h1>
        <p className="text-sm text-gray-500 mt-0.5">Monitor, investigate, and manage fraud alerts</p>
      </div>

      <div className="card p-4 space-y-4">
        <div className="flex flex-wrap gap-2">
          {STATUSES.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={statusFilter === s ? 'btn-ghost-active' : 'btn-ghost'}
            >
              {s === 'ALL' ? 'All' : s.replace(/_/g, ' ')}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Tier:</span>
            {TIERS.map((t) => (
              <button
                key={t}
                onClick={() => setTierFilter(t)}
                className={tierFilter === t ? 'btn-ghost-active text-xs px-3 py-1' : 'btn-ghost text-xs px-3 py-1'}
              >
                {t}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">From:</span>
            <input type="date" className="input w-40" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
            <span className="text-xs text-gray-500">To:</span>
            <input type="date" className="input w-40" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="card p-8 flex items-center justify-center">
          <div className="animate-spin w-6 h-6 border-2 border-fraud-500 border-t-transparent rounded-full" />
        </div>
      ) : !alerts.length ? (
        <div className="card p-8 text-center text-gray-500">No alerts match the current filters</div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-800/50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-5 py-3">Alert ID</th>
                  <th className="px-5 py-3">Risk Tier</th>
                  <th className="px-5 py-3">Investigation Status</th>
                  <th className="px-5 py-3">Created At</th>
                  <th className="px-5 py-3">Updated At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {alerts.map((a) => (
                  <tr
                    key={a.alert_id}
                    className="table-row cursor-pointer"
                    onClick={() => navigate(`/alerts/${a.alert_id}`)}
                  >
                    <td className="px-5 py-3 font-mono text-xs text-gray-400">#{a.alert_id}</td>
                    <td className="px-5 py-3">
                      <span className={tierBadge[a.risk_tier] || 'badge'}>{a.risk_tier}</span>
                    </td>
                    <td className="px-5 py-3">
                      <span className={investigationBadge[a.investigation_status || a.status] || 'badge'}>
                        {(a.investigation_status || a.status || '').replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-gray-500 text-xs font-mono">
                      {a.created_at?.slice(0, 19).replace('T', ' ')}
                    </td>
                    <td className="px-5 py-3 text-gray-600 text-xs font-mono">
                      {a.updated_at?.slice(0, 19).replace('T', ' ') || '--'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between px-5 py-3 border-t border-gray-800">
              <span className="text-xs text-gray-500">
                Page {page + 1} of {totalPages} ({total} total)
              </span>
              <div className="flex gap-1">
                <button
                  disabled={page === 0}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  className="btn-ghost text-xs px-3 py-1 disabled:opacity-30"
                >
                  Previous
                </button>
                <button
                  disabled={page >= totalPages - 1}
                  onClick={() => setPage((p) => p + 1)}
                  className="btn-ghost text-xs px-3 py-1 disabled:opacity-30"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
