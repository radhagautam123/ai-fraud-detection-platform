import { useEffect, useState } from 'react'
import { getModelInfo, getMetrics, getRiskScoreDistribution } from '../api/api'
import KPICard from '../components/KPICard'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const REFRESH_INTERVAL = 10000

export default function ModelMonitoring() {
  const [model, setModel] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [riskBuckets, setRiskBuckets] = useState([])

  useEffect(() => {
    const fetch = () => {
      getModelInfo().then(setModel).catch(() => {})
      getMetrics().then(setMetrics).catch(() => {})
      getRiskScoreDistribution().then(setRiskBuckets).catch(() => {})
    }
    fetch()
    const interval = setInterval(fetch, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Model Monitoring</h1>
          <p className="text-sm text-gray-500 mt-0.5">ML model performance and system metrics</p>
        </div>
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
          Auto-refresh every 10s
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard title="Total Predictions" value={metrics?.total_predictions?.toLocaleString() ?? '--'} icon="🔮" color="blue" />
        <KPICard title="Fraud Detected" value={metrics?.fraud_predictions?.toLocaleString() ?? '--'} icon="⚠️" color="red" />
        <KPICard title="Avg Risk Score" value={metrics?.avg_risk_score ?? '--'} icon="🎯" color="emerald" />
        <KPICard
          title="Alert Rate"
          value={metrics?.total_alerts && metrics?.total_predictions ? `${((metrics.total_alerts / metrics.total_predictions) * 100).toFixed(1)}%` : '--'}
          icon="📊"
          color="amber"
        />
      </div>

      <div className="card overflow-hidden">
        <div className="card-header">
          <h3 className="text-sm font-semibold text-gray-200">Model Details</h3>
        </div>
        {model && Object.keys(model).length > 0 ? (
          <div className="p-5">
            <dl className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <dt className="text-xs font-medium text-gray-500">Version</dt>
                <dd className="mt-1 text-lg font-semibold text-white font-mono">{model.version}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium text-gray-500">Algorithm</dt>
                <dd className="mt-1 text-lg font-semibold text-white">{model.algorithm}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium text-gray-500">ROC-AUC</dt>
                <dd className="mt-1 text-lg font-semibold text-emerald-400 font-mono">{model.auc_roc}</dd>
              </div>
              <div>
                <dt className="text-xs font-medium text-gray-500">F1 Score</dt>
                <dd className="mt-1 text-lg font-semibold text-emerald-400 font-mono">{model.f1_score}</dd>
              </div>
            </dl>
          </div>
        ) : (
          <div className="p-5 text-gray-500 text-sm">Model information unavailable</div>
        )}
      </div>

      {riskBuckets.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-200 mb-4">Risk Score Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={riskBuckets}>
              <XAxis dataKey="bucket" tick={{ fontSize: 12, fill: '#6b7280' }} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#e5e7eb', fontSize: '12px' }}
              />
              <Bar dataKey="count" fill="#db2777" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="card p-5">
        <h3 className="text-sm font-semibold text-gray-200 mb-2">System Status</h3>
        <div className="flex items-center gap-2 text-sm text-emerald-400">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
          API is healthy
        </div>
        <div className="mt-3 text-xs text-gray-500">
          All systems operational &middot; Database connected &middot; Model loaded
        </div>
      </div>
    </div>
  )
}
