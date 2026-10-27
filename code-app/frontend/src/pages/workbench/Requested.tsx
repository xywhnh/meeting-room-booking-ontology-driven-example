import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, Undo2 } from 'lucide-react'
import { workbenchApi, type RequestedItem } from '../../api/workbench'
import { bookingApi } from '../../api/booking'
import Pagination from '../../components/Pagination'
import { toast } from '../../components/toast'
import { Badge } from '../../utils/status'

export default function Requested() {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [size] = useState(10)
  const [data, setData] = useState<RequestedItem[]>([])
  const [total, setTotal] = useState(0)

  const load = async () => {
    const res = await workbenchApi.requested({ page, size })
    setData(res.list)
    setTotal(res.total)
  }

  useEffect(() => { load() }, [page])

  const handleWithdraw = async (b: RequestedItem) => {
    if (!window.confirm(`确认撤回预定「${b.purpose}」吗？`)) return
    try {
      await bookingApi.withdraw(b.id)
      toast('已撤回')
      load()
    } catch (err: any) {
      toast(err.message, 'error')
    }
  }

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
      <div style={{ padding: '14px 20px', borderBottom: '1px solid var(--divider-color)' }}>
        <h3 style={{ fontWeight: 700 }}>我的申请</h3>
      </div>
      <div className="table-container">
        <table>
          <thead>
            <tr><th>预定编号</th><th>会议室</th><th>会议主题</th><th>日期时段</th><th>审批状态</th><th>申请时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            {data.map((b) => (
              <tr key={b.id}>
                <td>{b.booking_no}</td>
                <td>{b.room_name || '-'}</td>
                <td>{b.purpose}</td>
                <td>{b.booking_date} {b.start_time}–{b.end_time}</td>
                <td><Badge status={b.status} /></td>
                <td>{b.created_at}</td>
                <td>
                  <button className="btn btn-secondary btn-sm" onClick={() => navigate(`/booking/apply?id=${b.id}`)}>
                    <Eye size={14} /> 查看
                  </button>
                  {b.status === '待部门主管审批' && (
                    <button className="btn btn-secondary btn-sm" style={{ marginLeft: 8 }} onClick={() => handleWithdraw(b)}>
                      <Undo2 size={14} /> 撤回
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr><td colSpan={7} style={{ textAlign: 'center', color: '#94a3b8' }}>暂无申请</td></tr>
            )}
          </tbody>
        </table>
      </div>
      <div style={{ padding: '14px 20px', display: 'flex', justifyContent: 'flex-end' }}>
        <Pagination page={page} size={size} total={total} onChange={setPage} />
      </div>
    </div>
  )
}
