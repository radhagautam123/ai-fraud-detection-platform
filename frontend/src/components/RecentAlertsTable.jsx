import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getAlerts } from '../api/api'

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

export default function RecentAlertsTable({ filter = {} }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    getAlerts({ limit: 10, ...filter })
      .then((res) => setAlerts(res.data || []))
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="card p-5"><div className="text-gray-500 text-sm">Loading alerts...</div></div>
  if (error) return <div className="card p-5"><div className="text-red-400 text-sm">Failed to load alerts</div></div>
  if (!alerts.length) return <div className="card p-5"><div className="text-gray-500 text-sm">No alerts found</div></div>

  return (
    <div className="card overflow-hidden">
      <div className="card-header flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-200">Recent Alerts</h3>
        <button
          onClick={() => navigate('/alerts')}
          className="text-xs text-fraud-400 hover:text-fraud-300 transition-colors"
        >
          View all
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-800/50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="px-5 py-3">ID</th>
              <th className="px-5 py-3">Risk</th>
              <th className="px-5 py-3">Investigation</th>
              <th className="px-5 py-3">Created</th>
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
                  <span className={investigationBadge[a.investigation_status] || 'badge'}>
                    {(a.investigation_status || a.status || '').replace(/_/g, ' ')}
                  </span>
                </td>
                <td className="px-5 py-3 text-gray-500 text-xs font-mono">
                  {a.created_at?.slice(0, 19).replace('T', ' ')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
