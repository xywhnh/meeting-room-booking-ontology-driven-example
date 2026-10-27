import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, RotateCcw, Search } from 'lucide-react'
import { bookingApi, type Booking } from '../../api/booking'
import { roomApi, type Room } from '../../api/room'
import { metaApi } from '../../api/meta'
import Pagination from '../../components/Pagination'
import { Badge } from '../../utils/status'

export default function BookingQuery() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState({ booking_no: '', room_id: '', booking_date: '', status: '' })
  const [page, setPage] = useState(1)
  const [size] = useState(10)
  const [data, setData] = useState<Booking[]>([])
  const [total, setTotal] = useState(0)
  const [rooms, setRooms] = useState<Room[]>([])
  const [statuses, setStatuses] = useState<string[]>([])

  useEffect(() => {
    roomApi.list().then(setRooms).catch(() => {})
    metaApi.bookingStatus().then(setStatuses).catch(() => {})
  }, [])

  useEffect(() => {
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page])

  const load = async () => {
    const res = await bookingApi.list({
      page, size,
      booking_no: filters.booking_no || undefined,
      room_id: filters.room_id ? Number(filters.room_id) : undefined,
      booking_date: filters.booking_date || undefined,
      status: filters.status || undefined,
    })
    setData(res.list)
    setTotal(res.total)
  }

  const handleQuery = () => {
    setPage(1)
    load()
  }

  const handleReset = () => {
    setFilters({ booking_no: '', room_id: '', booking_date: '', status: '' })
    setPage(1)
  }

  return (
    <div>
      <div className="card" style={{ padding: '20px' }}>
        <div className="form-grid-3">
          <div className="form-item">
            <label className="field-label">预定编号</label>
            <div className="field-control">
              <input value={filters.booking_no} onChange={(e) => setFilters({ ...filters, booking_no: e.target.value })} />
            </div>
          </div>
          <div className="form-item">
            <label className="field-label">会议室</label>
            <div className="field-control">
              <select value={filters.room_id} onChange={(e) => setFilters({ ...filters, room_id: e.target.value })}>
                <option value="">全部</option>
                {rooms.map((r) => (<option key={r.id} value={r.id}>{r.room_name}</option>))}
              </select>
            </div>
          </div>
          <div className="form-item">
            <label className="field-label">预定日期</label>
            <div className="field-control">
              <input type="date" value={filters.booking_date} onChange={(e) => setFilters({ ...filters, booking_date: e.target.value })} />
            </div>
          </div>
          <div className="form-item">
            <label className="field-label">审批状态</label>
            <div className="field-control">
              <select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
                <option value="">全部</option>
                {statuses.map((s) => (<option key={s} value={s}>{s}</option>))}
              </select>
            </div>
          </div>
        </div>
        <div className="toolbar-right">
          <button className="btn btn-primary" onClick={handleQuery}>
            <Search size={14} /> 查询
          </button>
          <button className="btn btn-secondary" onClick={handleReset}>
            <RotateCcw size={14} /> 重置
          </button>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--divider-color)' }}>
          <h3 style={{ fontWeight: 700 }}>查询结果</h3>
        </div>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>预定编号</th><th>会议室</th><th>日期</th><th>时段</th>
                <th>会议主题</th><th>人数</th><th>审批状态</th><th>申请人</th><th>操作</th>
              </tr>
            </thead>
            <tbody>
              {data.map((b) => (
                <tr key={b.id}>
                  <td>{b.booking_no}</td>
                  <td>{b.room_name || '-'}</td>
                  <td>{b.booking_date}</td>
                  <td>{b.start_time}–{b.end_time}</td>
                  <td>{b.purpose}</td>
                  <td>{b.participants}</td>
                  <td><Badge status={b.status} /></td>
                  <td>{b.applicant_name || '-'}</td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/booking/apply?id=${b.id}`)}>
                      <Eye size={14} /> 查看
                    </button>
                  </td>
                </tr>
              ))}
              {data.length === 0 && (
                <tr><td colSpan={9} style={{ textAlign: 'center', color: '#94a3b8' }}>暂无数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
        <div style={{ padding: '14px 20px', display: 'flex', justifyContent: 'flex-end' }}>
          <Pagination page={page} size={size} total={total} onChange={setPage} />
        </div>
      </div>
    </div>
  )
}
