import { useEffect, useState } from 'react'
import { RotateCcw, Search } from 'lucide-react'
import { reportApi, type RoomSummaryRow } from '../../api/report'

export default function RoomSummary() {
  const [filters, setFilters] = useState({ date_from: '', date_to: '' })
  const [data, setData] = useState<RoomSummaryRow[]>([])

  const load = async () => {
    const rows = await reportApi.roomSummary({
      date_from: filters.date_from || undefined,
      date_to: filters.date_to || undefined,
    })
    setData(rows)
  }

  useEffect(() => { load().catch(() => {}) }, [])

  return (
    <div>
      <div className="card" style={{ padding: '20px' }}>
        <div className="form-grid-3">
          <div className="form-item">
            <label className="field-label">预定日期起</label>
            <div className="field-control">
              <input type="date" value={filters.date_from} onChange={(e) => setFilters({ ...filters, date_from: e.target.value })} />
            </div>
          </div>
          <div className="form-item">
            <label className="field-label">预定日期止</label>
            <div className="field-control">
              <input type="date" value={filters.date_to} onChange={(e) => setFilters({ ...filters, date_to: e.target.value })} />
            </div>
          </div>
        </div>
        <div className="toolbar-right">
          <button className="btn btn-primary" onClick={load}>
            <Search size={14} /> 查询
          </button>
          <button className="btn btn-secondary" onClick={() => setFilters({ date_from: '', date_to: '' })}>
            <RotateCcw size={14} /> 重置
          </button>
        </div>
      </div>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--divider-color)' }}>
          <h3 style={{ fontWeight: 700 }}>会议室预定统计（M7 REP-BOOKING-ROOM-SUMMARY）</h3>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr><th>会议室编号</th><th>会议室名称</th><th>容纳人数</th><th>位置</th><th>预定单数</th><th>已通过单数</th></tr>
            </thead>
            <tbody>
              {data.map((r) => (
                <tr key={r.id}>
                  <td>{r.room_no}</td><td>{r.room_name}</td><td>{r.capacity}</td>
                  <td>{r.location || '-'}</td><td>{r.total_count}</td><td>{r.approved_count}</td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr><td colSpan={6} style={{ textAlign: 'center', color: '#94a3b8' }}>暂无数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
