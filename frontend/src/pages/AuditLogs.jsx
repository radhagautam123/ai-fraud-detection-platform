import { useEffect, useState } from 'react'
import { getAuditLogs } from '../api/api'

const actionColors = {
  LOGIN: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  LOGOUT: 'text-gray-400 bg-gray-500/10 border-gray-500/20',
  ALERT_CREATED: 'text-red-400 bg-red-500/10 border-red-500/20',
  ALERT_STATUS_CHANGE: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/20',
  ALERT_ASSIGN: 'text-blue-400 bg-blue-500/10 border-blue-500/20',
  ALERT_NOTE_UPDATED: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  ALERT_RESOLVED: 'text-green-400 bg-green-500/10 border-green-500/20',
}

export default function AuditLogs() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [offset, setOffset] = useState(0)
  const [actionFilter, setActionFilter] = useState('')
  const limit = 25

  const fetchLogs = () => {
    setLoading(true)
    const params = { limit, offset }
    if (actionFilter) params.action = actionFilter
    getAuditLogs(params)
      .then((data) => {
        setLogs(data.logs || data)
        setTotal(data.total ?? 0)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchLogs()
  }, [offset, actionFilter])

  const totalPages = Math.ceil(total / limit)
  const currentPage = Math.floor(offset / limit) + 1

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Audit Logs</h1>
          <p className="text-sm text-gray-500 mt-0.5">Track all user actions across the platform</p>
        </div>
        <div className="text-xs text-gray-500">{total} total entries</div>
      </div>

      <div className="flex items-center gap-3">
        <select
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setOffset(0) }}
          className="input max-w-xs"
        >
          <option value="">All Actions</option>
          {Object.keys(actionColors).map((a) => (
            <option key={a} value={a}>{a.replace(/_/g, ' ')}</option>
          ))}
        </select>
        <span className="text-xs text-gray-600">Showing page {currentPage} of {totalPages || 1}</span>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
                <th className="text-left px-4 py-3 font-medium">Timestamp</th>
                <th className="text-left px-4 py-3 font-medium">User</th>
                <th className="text-left px-4 py-3 font-medium">Action</th>
                <th className="text-left px-4 py-3 font-medium">Resource</th>
                <th className="text-left px-4 py-3 font-medium">IP Address</th>
                <th className="text-left px-4 py-3 font-medium">Details</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading...</td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-gray-500">No audit logs found</td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="border-b border-gray-800/50 hover:bg-gray-800/20">
                    <td className="px-4 py-3 text-gray-400 font-mono text-xs whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-gray-200">{log.username}</span>
                      <span className="text-gray-600 text-xs ml-1">({log.user_id})</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-block text-[10px] px-2 py-0.5 rounded border font-medium ${actionColors[log.action] || 'text-gray-400 bg-gray-500/10 border-gray-500/20'}`}>
                        {log.action.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">
                      {log.resource_type}{log.resource_id ? ` #${log.resource_id}` : ''}
                    </td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs">{log.ip_address || '--'}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs max-w-xs truncate">{log.details || '--'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-800">
            <button
              onClick={() => setOffset(Math.max(0, offset - limit))}
              disabled={offset === 0}
              className="btn btn-sm disabled:opacity-30"
            >
              Previous
            </button>
            <span className="text-xs text-gray-500">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setOffset(offset + limit)}
              disabled={offset + limit >= total}
              className="btn btn-sm disabled:opacity-30"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
