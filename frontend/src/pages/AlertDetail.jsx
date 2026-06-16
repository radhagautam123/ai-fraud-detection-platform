import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getAlertDetail, getUsers, assignAlert, updateAlertStatus, updateAlertNotes, resolveAlert } from '../api/api'
import { useAuth } from '../auth/AuthContext'

const investigationBadge = {
  NEW: 'badge-unresolved',
  ASSIGNED: 'badge-investigating',
  INVESTIGATING: 'badge-investigating',
  CONFIRMED_FRAUD: 'badge-critical',
  FALSE_POSITIVE: 'badge-resolved',
  CLOSED: 'badge-resolved',
}

const STATUS_OPTIONS = ['NEW', 'ASSIGNED', 'INVESTIGATING', 'CONFIRMED_FRAUD', 'FALSE_POSITIVE', 'CLOSED']
const RESOLUTION_OPTIONS = ['CONFIRMED_FRAUD', 'FALSE_POSITIVE']

const statusColors = {
  NEW: 'text-red-400',
  ASSIGNED: 'text-amber-400',
  INVESTIGATING: 'text-amber-400',
  CONFIRMED_FRAUD: 'text-red-400',
  FALSE_POSITIVE: 'text-emerald-400',
  CLOSED: 'text-gray-400',
}

export default function AlertDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const canEdit = user && (user.role === 'ADMIN' || user.role === 'ANALYST')

  const [alert, setAlert] = useState(null)
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')
  const [notesDraft, setNotesDraft] = useState('')

  useEffect(() => {
    getAlertDetail(id)
      .then((data) => {
        setAlert(data)
        setNotesDraft(data.case_notes || '')
      })
      .catch(() => navigate('/alerts'))
      .finally(() => setLoading(false))

    if (canEdit) {
      getUsers().then(setUsers).catch(() => {})
    }
  }, [id])

  const doAssign = async (userId) => {
    setSaving(true)
    try {
      const res = await assignAlert(id, userId || null)
      setAlert((prev) => ({ ...prev, assigned_to: res.assigned_to, investigation_status: res.investigation_status }))
      setMessage('Assignment updated')
    } catch { setMessage('Failed to assign') }
    setSaving(false)
  }

  const doStatus = async (status) => {
    setSaving(true)
    try {
      const res = await updateAlertStatus(id, status)
      setAlert((prev) => ({ ...prev, investigation_status: res.investigation_status, status: res.alert_status }))
      setMessage(`Status changed to ${status.replace(/_/g, ' ')}`)
    } catch { setMessage('Failed to update status') }
    setSaving(false)
  }

  const doNotes = async () => {
    setSaving(true)
    try {
      const res = await updateAlertNotes(id, notesDraft)
      setAlert((prev) => ({ ...prev, case_notes: res.case_notes }))
      setMessage('Notes saved')
    } catch { setMessage('Failed to save notes') }
    setSaving(false)
  }

  const doResolve = async (resolution) => {
    setSaving(true)
    try {
      const res = await resolveAlert(id, resolution)
      setAlert((prev) => ({ ...prev, resolution: res.resolution, investigation_status: res.investigation_status, resolved_at: res.resolved_at }))
      setMessage(`Alert resolved as ${resolution.replace(/_/g, ' ')}`)
    } catch { setMessage('Failed to resolve') }
    setSaving(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin w-8 h-8 border-2 border-fraud-500 border-t-transparent rounded-full" />
      </div>
    )
  }

  if (!alert || !alert.alert_id) {
    return <div className="card p-8 text-center text-gray-500">Alert not found</div>
  }

  const isClosed = alert.investigation_status === 'CLOSED'

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/alerts')} className="text-gray-500 hover:text-gray-300 transition-colors text-lg">
            &larr;
          </button>
          <div>
            <h1 className="text-xl font-bold text-white">Alert #{alert.alert_id}</h1>
            <p className="text-sm text-gray-500">Fraud investigation case</p>
          </div>
        </div>
        <span className={investigationBadge[alert.investigation_status] || 'badge'}>
          {(alert.investigation_status || alert.status || '').replace(/_/g, ' ')}
        </span>
      </div>

      {message && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm rounded-lg px-4 py-2 flex items-center justify-between">
          {message}
          <button onClick={() => setMessage('')} className="text-emerald-400/70 hover:text-emerald-400">&times;</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Alert Info */}
        <div className="card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Alert Details</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-xs text-gray-500">Risk Tier</dt>
              <dd className={`text-sm font-semibold ${alert.risk_tier === 'CRITICAL' ? 'text-red-400' : 'text-orange-400'}`}>
                {alert.risk_tier}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Investigation Status</dt>
              <dd className={`text-sm font-semibold ${statusColors[alert.investigation_status] || 'text-gray-300'}`}>
                {(alert.investigation_status || '').replace(/_/g, ' ')}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Created</dt>
              <dd className="text-sm text-gray-300 font-mono">{alert.created_at?.slice(0, 19).replace('T', ' ')}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Updated</dt>
              <dd className="text-sm text-gray-300 font-mono">{alert.updated_at?.slice(0, 19).replace('T', ' ') || '--'}</dd>
            </div>
            {alert.resolved_at && (
              <div>
                <dt className="text-xs text-gray-500">Resolved At</dt>
                <dd className="text-sm text-gray-300 font-mono">{alert.resolved_at?.slice(0, 19).replace('T', ' ')}</dd>
              </div>
            )}
            {alert.resolution && (
              <div>
                <dt className="text-xs text-gray-500">Resolution</dt>
                <dd className="text-sm font-semibold text-emerald-400">{alert.resolution.replace(/_/g, ' ')}</dd>
              </div>
            )}
            <div>
              <dt className="text-xs text-gray-500">Assigned To</dt>
              <dd className="text-sm text-gray-300">
                {alert.assigned_user ? (
                  <span>{alert.assigned_user.username} <span className="text-xs text-gray-500">({alert.assigned_user.role})</span></span>
                ) : (
                  <span className="text-gray-500">Unassigned</span>
                )}
              </dd>
            </div>
          </dl>
        </div>

        {/* Fraud Prediction */}
        <div className="card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Fraud Analysis</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-xs text-gray-500">Fraud Probability</dt>
              <dd className="text-lg font-bold font-mono">
                <span className={alert.fraud_probability > 0.8 ? 'text-red-400' : alert.fraud_probability > 0.5 ? 'text-amber-400' : 'text-emerald-400'}>
                  {(alert.fraud_probability * 100).toFixed(1)}%
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Risk Score</dt>
              <dd className="text-lg font-bold font-mono text-white">{alert.risk_score}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Prediction</dt>
              <dd className={`text-sm font-semibold ${alert.is_fraud ? 'text-red-400' : 'text-emerald-400'}`}>
                {alert.is_fraud ? 'Fraudulent' : 'Legitimate'}
              </dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Model Version</dt>
              <dd className="text-sm text-gray-300 font-mono">{alert.model_version}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Prediction Timestamp</dt>
              <dd className="text-sm text-gray-300 font-mono">{alert.prediction_timestamp?.slice(0, 19).replace('T', ' ')}</dd>
            </div>
          </dl>
        </div>

        {/* Transaction */}
        <div className="card p-5 space-y-4">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Transaction</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-xs text-gray-500">Transaction ID</dt>
              <dd className="text-sm text-gray-300 font-mono break-all">{alert.transaction_id}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Amount</dt>
              <dd className="text-lg font-bold font-mono text-white">${alert.amount?.toFixed(2)}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Merchant</dt>
              <dd className="text-sm text-gray-300">{alert.merchant}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Category</dt>
              <dd className="text-sm text-gray-300">{alert.category}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Card Holder</dt>
              <dd className="text-sm text-gray-300 font-mono">{alert.card_holder_id}</dd>
            </div>
            <div>
              <dt className="text-xs text-gray-500">Timestamp</dt>
              <dd className="text-sm text-gray-300 font-mono">{alert.transaction_timestamp?.slice(0, 19).replace('T', ' ')}</dd>
            </div>
          </dl>
        </div>
      </div>

      {canEdit && !isClosed && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Assignment + Status */}
          <div className="card p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Case Management</h2>

            <div>
              <label className="block text-xs text-gray-500 mb-1">Assign Analyst</label>
              <select
                className="select"
                value={alert.assigned_to || ''}
                onChange={(e) => doAssign(e.target.value ? Number(e.target.value) : null)}
                disabled={saving}
              >
                <option value="">Unassigned</option>
                {users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.username} ({u.role})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1">Update Status</label>
              <div className="flex flex-wrap gap-1.5">
                {STATUS_OPTIONS.filter((s) => s !== 'CLOSED').map((s) => (
                  <button
                    key={s}
                    onClick={() => doStatus(s)}
                    disabled={saving || alert.investigation_status === s}
                    className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                      alert.investigation_status === s
                        ? 'bg-fraud-600/20 text-fraud-400 border-fraud-500/30'
                        : 'bg-gray-800 text-gray-400 border-gray-700 hover:bg-gray-700'
                    }`}
                  >
                    {s.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-2">Resolution</label>
              <div className="flex gap-2">
                {RESOLUTION_OPTIONS.map((r) => (
                  <button
                    key={r}
                    onClick={() => doResolve(r)}
                    disabled={saving}
                    className={`btn text-xs px-4 ${
                      r === 'CONFIRMED_FRAUD'
                        ? 'bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20'
                    }`}
                  >
                    Resolve as {r.replace(/_/g, ' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Investigation Notes */}
          <div className="card p-5 space-y-4">
            <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Investigation Notes</h2>
            <textarea
              className="input min-h-[160px] resize-y"
              placeholder="Add investigation notes..."
              value={notesDraft}
              onChange={(e) => setNotesDraft(e.target.value)}
            />
            <button
              onClick={doNotes}
              disabled={saving}
              className="btn-primary flex items-center gap-2"
            >
              {saving && <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />}
              Save Notes
            </button>
          </div>
        </div>
      )}

      {isClosed && (
        <div className="card p-5">
          <div className="flex items-center gap-3 text-sm text-gray-400">
            <span className="text-lg">🔒</span>
            This case is <strong className="text-gray-200">CLOSED</strong>
            {alert.resolution && (
              <>
                <span className="text-gray-600">|</span>
                Resolution: <span className="text-emerald-400 font-medium">{alert.resolution.replace(/_/g, ' ')}</span>
              </>
            )}
          </div>
        </div>
      )}

      {alert.case_notes && (
        <div className="card p-5 space-y-3">
          <h2 className="text-sm font-semibold text-gray-200 uppercase tracking-wider">Case Notes</h2>
          <div className="text-sm text-gray-300 whitespace-pre-wrap bg-gray-800/50 rounded-lg p-4 border border-gray-800">
            {alert.case_notes}
          </div>
        </div>
      )}
    </div>
  )
}
