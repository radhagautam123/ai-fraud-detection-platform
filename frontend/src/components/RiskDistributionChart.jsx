import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { getRiskDistribution } from '../api/api'

const COLORS = { HIGH: '#f59e0b', CRITICAL: '#ef4444' }

export default function RiskDistributionChart() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getRiskDistribution()
      .then((raw) => {
        const chartData = Object.entries(raw).map(([name, value]) => ({ name, value }))
        setData(chartData)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="card p-5"><div className="text-gray-500 text-sm">Loading chart...</div></div>
  if (error) return <div className="card p-5"><div className="text-red-400 text-sm">Failed to load risk distribution</div></div>
  if (!data.length) return <div className="card p-5"><div className="text-gray-500 text-sm">No risk data available</div></div>

  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-gray-200 mb-4">Risk Distribution</h3>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#6b7280' }} tickLine={false} />
          <YAxis tick={{ fontSize: 12, fill: '#6b7280' }} tickLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#e5e7eb', fontSize: '12px' }}
          />
          <Bar dataKey="value" radius={[6, 6, 0, 0]}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={COLORS[entry.name] || '#6b7280'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
