import { useEffect, useState, useCallback } from 'react'
import { getTransactions } from '../api/api'

const PAGE_SIZE = 20

export default function Transactions() {
  const [txs, setTxs] = useState([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('timestamp')
  const [sortOrder, setSortOrder] = useState('desc')

  const fetchPage = useCallback((p, s, sb, so) => {
    setLoading(true)
    const params = { limit: PAGE_SIZE, offset: p * PAGE_SIZE }
    if (s) params.search = s
    if (sb) params.sort_by = sb
    if (so) params.sort_order = so

    getTransactions(params)
      .then((res) => {
        setTxs(res.data || [])
        setTotal(res.total || 0)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    setPage(0)
    fetchPage(0, search, sortBy, sortOrder)
  }, [search, sortBy, sortOrder])

  useEffect(() => {
    fetchPage(page, search, sortBy, sortOrder)
  }, [page])

  const handleSort = (col) => {
    if (sortBy === col) {
      setSortOrder((o) => (o === 'desc' ? 'asc' : 'desc'))
    } else {
      setSortBy(col)
      setSortOrder('desc')
    }
  }

  const sortArrow = (col) => {
    if (sortBy !== col) return ''
    return sortOrder === 'desc' ? ' ↓' : ' ↑'
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold text-white">Transactions</h1>
          <p className="text-sm text-gray-500 mt-0.5">View and search credit card transactions</p>
        </div>
        <input
          type="text"
          placeholder="Search ID, merchant, or category..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input w-72"
        />
      </div>

      {loading ? (
        <div className="card p-8 flex items-center justify-center">
          <div className="animate-spin w-6 h-6 border-2 border-fraud-500 border-t-transparent rounded-full" />
        </div>
      ) : !txs.length ? (
        <div className="card p-8 text-center text-gray-500">
          {search ? 'No transactions match your search' : 'No transactions found'}
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-800/50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <th className="px-5 py-3">Transaction ID</th>
                  <th
                    className="px-5 py-3 cursor-pointer hover:text-gray-300 select-none"
                    onClick={() => handleSort('amount')}
                  >
                    Amount{sortArrow('amount')}
                  </th>
                  <th
                    className="px-5 py-3 cursor-pointer hover:text-gray-300 select-none"
                    onClick={() => handleSort('merchant')}
                  >
                    Merchant{sortArrow('merchant')}
                  </th>
                  <th className="px-5 py-3">Category</th>
                  <th
                    className="px-5 py-3 cursor-pointer hover:text-gray-300 select-none"
                    onClick={() => handleSort('timestamp')}
                  >
                    Timestamp{sortArrow('timestamp')}
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {txs.map((t) => (
                  <tr key={t.transaction_id} className="table-row">
                    <td className="px-5 py-3 font-mono text-xs text-gray-400">{t.transaction_id}</td>
                    <td className="px-5 py-3 font-medium text-gray-200 font-mono">${parseFloat(t.amount).toFixed(2)}</td>
                    <td className="px-5 py-3 text-gray-400">{t.merchant}</td>
                    <td className="px-5 py-3 text-gray-400">{t.category || '--'}</td>
                    <td className="px-5 py-3 text-gray-500 text-xs font-mono">
                      {t.timestamp?.slice(0, 19).replace('T', ' ')}
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
