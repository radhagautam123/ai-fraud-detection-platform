import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { getFraudTrend } from '../api/api'

export default function FraudTrendChart() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getFraudTrend('day', 30)
      .then(setData)
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="card p-5"><div className="text-gray-500 text-sm">Loading trend...</div></div>
  if (error) return <div className="card p-5"><div className="text-red-400 text-sm">Failed to load trend data</div></div>
  if (!data.length) return <div className="card p-5"><div className="text-gray-500 text-sm">No trend data available</div></div>

  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-gray-200 mb-4">Fraud Alert Trend (30 days)</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#6b7280' }} tickLine={false} />
          <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} allowDecimals={false} tickLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px', color: '#e5e7eb', fontSize: '12px' }}
          />
          <Line type="monotone" dataKey="count" stroke="#ec4899" strokeWidth={2} dot={{ r: 3, fill: '#ec4899' }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
