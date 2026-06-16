import { useEffect, useState } from 'react'
import { getTransactions } from '../api/api'

export default function RecentTransactionsTable() {
  const [txs, setTxs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getTransactions({ limit: 10 })
      .then((res) => setTxs(res.data || []))
      .catch(setError)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="card p-5"><div className="text-gray-500 text-sm">Loading transactions...</div></div>
  if (error) return <div className="card p-5"><div className="text-red-400 text-sm">Failed to load transactions</div></div>
  if (!txs.length) return <div className="card p-5"><div className="text-gray-500 text-sm">No transactions found</div></div>

  return (
    <div className="card overflow-hidden">
      <div className="card-header">
        <h3 className="text-sm font-semibold text-gray-200">Recent Transactions</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-800/50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              <th className="px-5 py-3">ID</th>
              <th className="px-5 py-3">Amount</th>
              <th className="px-5 py-3">Merchant</th>
              <th className="px-5 py-3">Timestamp</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {txs.map((t) => (
              <tr key={t.transaction_id} className="table-row">
                <td className="px-5 py-3 font-mono text-xs text-gray-400">{t.transaction_id?.slice(0, 12)}...</td>
                <td className="px-5 py-3 font-medium text-gray-200 font-mono">${parseFloat(t.amount).toFixed(2)}</td>
                <td className="px-5 py-3 text-gray-400">{t.merchant}</td>
                <td className="px-5 py-3 text-gray-500 text-xs font-mono">{t.timestamp?.slice(0, 19).replace('T', ' ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
