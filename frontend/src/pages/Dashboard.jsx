import { useEffect, useState, useCallback } from 'react'
import { getMetrics, getModelInfo, getFraudTrend, getTopMerchants, getSystemHealth, getSystemMetrics } from '../api/api'
import KPICard from '../components/KPICard'
import FraudTrendChart from '../components/FraudTrendChart'
import RiskDistributionChart from '../components/RiskDistributionChart'
import RecentAlertsTable from '../components/RecentAlertsTable'
import RecentTransactionsTable from '../components/RecentTransactionsTable'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'

const REFRESH_INTERVAL = 5000

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null)
  const [model, setModel] = useState(null)
  const [topMerchants, setTopMerchants] = useState([])
  const [health, setHealth] = useState(null)
  const [sysMetrics, setSysMetrics] = useState(null)
  const [time, setTime] = useState(new Date())

  const fetchAll = useCallback(() => {
    getMetrics().then(setMetrics).catch(() => {})
    getModelInfo().then(setModel).catch(() => {})
    getTopMerchants(8).then(setTopMerchants).catch(() => {})
    getSystemHealth().then(setHealth).catch(() => {})
    getSystemMetrics().then(setSysMetrics).catch(() => {})
  }, [])

  useEffect(() => {
    fetchAll()
    const interval = setInterval(fetchAll, REFRESH_INTERVAL)
    return () => clearInterval(interval)
  }, [fetchAll])

  useEffect(() => {
    const tick = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(tick)
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">Real-time fraud detection overview</p>
        </div>
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
            Live
          </span>
          <span className="font-mono">{time.toLocaleTimeString()}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard title="Transactions" value={metrics?.total_transactions?.toLocaleString() ?? '--'} icon="💳" color="blue" />
        <KPICard title="Predictions" value={metrics?.total_predictions?.toLocaleString() ?? '--'} icon="🔮" color="indigo" />
        <KPICard title="Alerts" value={metrics?.total_alerts?.toLocaleString() ?? '--'} icon="🚨" color="red" />
        <KPICard title="Fraud Detected" value={metrics?.fraud_predictions?.toLocaleString() ?? '--'} icon="⚠️" color="amber" />
        <KPICard title="Avg Risk Score" value={metrics?.avg_risk_score ?? '--'} icon="🎯" color="emerald" />
      </div>

      {model && Object.keys(model).length > 0 && (
        <div className="card p-4 flex items-center gap-3 text-sm">
          <span className="text-lg">🧠</span>
          <span className="text-gray-400">
            <span className="text-gray-200 font-medium">{model.algorithm}</span> v{model.version}
            <span className="mx-2 text-gray-600">|</span>
            ROC-AUC: <span className="text-emerald-400 font-mono">{model.auc_roc}</span>
            <span className="mx-2 text-gray-600">|</span>
            F1: <span className="text-emerald-400 font-mono">{model.f1_score}</span>
          </span>
        </div>
      )}

      {(health || sysMetrics) && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500 uppercase tracking-wider">API Status</span>
              <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-500' : 'bg-red-500'}`} />
            </div>
            <p className="text-lg font-semibold text-white">{health?.status ?? '--'}</p>
            <p className="text-[10px] text-gray-600 mt-0.5">Uptime: {health?.uptime_seconds ? `${Math.floor(health.uptime_seconds / 3600)}h ${Math.floor((health.uptime_seconds % 3600) / 60)}m` : '--'}</p>
          </div>
          <div className="card p-4">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500 uppercase tracking-wider">Database</span>
              <span className={`w-2 h-2 rounded-full ${health?.database === 'connected' ? 'bg-emerald-500' : 'bg-red-500'}`} />
            </div>
            <p className="text-lg font-semibold text-white">{health?.database ?? '--'}</p>
            <p className="text-[10px] text-gray-600 mt-0.5">API v{health?.api_version ?? '--'}</p>
          </div>
          <div className="card p-4">
            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Fraud Rate</span>
            <p className="text-lg font-semibold text-white">{sysMetrics?.fraud_rate != null ? `${(sysMetrics.fraud_rate * 100).toFixed(2)}%` : '--'}</p>
            <p className="text-[10px] text-gray-600 mt-0.5">{sysMetrics?.fraud_count?.toLocaleString() ?? '--'} fraud predictions</p>
          </div>
          <div className="card p-4">
            <span className="text-xs text-gray-500 uppercase tracking-wider block mb-1">Resolved Alerts</span>
            <p className="text-lg font-semibold text-white">{sysMetrics?.resolved_alerts?.toLocaleString() ?? '--'}</p>
            <p className="text-[10px] text-gray-600 mt-0.5">{sysMetrics?.audit_log_count?.toLocaleString() ?? '--'} audit entries</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <FraudTrendChart />
        </div>
        <RiskDistributionChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RecentAlertsTable />
        <RecentTransactionsTable />
      </div>

      {topMerchants.length > 0 && (
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-200 mb-4">Top Merchants (Fraud Count)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={topMerchants} layout="vertical">
              <XAxis type="number" tick={{ fontSize: 11, fill: '#6b7280' }} tickLine={false} />
              <YAxis type="category" dataKey="merchant" tick={{ fontSize: 11, fill: '#6b7280' }} tickLine={false} width={140} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#e5e7eb', fontSize: '12px' }}
              />
              <Bar dataKey="count" fill="#db2777" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
