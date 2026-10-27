import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { RotateCcw, Save, Send } from 'lucide-react'
import { bookingApi } from '../../api/booking'
import { roomApi, type Room } from '../../api/room'
import { toast } from '../../components/toast'
import { Badge } from '../../utils/status'

const emptyForm = {
  room_id: '',
  booking_date: '',
  start_time: '',
  end_time: '',
  purpose: '',
  participants: '',
}

export default function BookingApply() {
  const [searchParams, setSearchParams] = useSearchParams()
  const id = searchParams.get('id')
  const [form, setForm] = useState({ ...emptyForm })
  const [bookingId, setBookingId] = useState<number | null>(id ? Number(id) : null)
  const [status, setStatus] = useState('')
  const [rooms, setRooms] = useState<Room[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    roomApi.list('在用').then(setRooms).catch(() => {})
  }, [])

  useEffect(() => {
    if (bookingId) {
      bookingApi.get(bookingId).then((b) => {
        setForm({
          room_id: String(b.room_id),
          booking_date: b.booking_date,
          start_time: b.start_time,
          end_time: b.end_time,
          purpose: b.purpose,
          participants: String(b.participants),
        })
        setStatus(b.status)
      }).catch(() => {})
    }
  }, [bookingId])

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))
  const editable = status === '' || status === '草稿' || status === '已驳回'

  const saveDraft = async (): Promise<number | null> => {
    if (!form.room_id || !form.booking_date || !form.start_time || !form.end_time || !form.purpose || !form.participants) {
      toast('请填写会议室、日期、时段、主题与参会人数', 'error')
      return null
    }
    const payload = {
      room_id: Number(form.room_id),
      booking_date: form.booking_date,
      start_time: form.start_time,
      end_time: form.end_time,
      purpose: form.purpose,
      participants: Number(form.participants),
    }
    try {
      if (bookingId) {
        await bookingApi.updateDraft(bookingId, payload)
        return bookingId
      }
      const b = await bookingApi.createDraft(payload)
      setBookingId(b.id)
      setSearchParams({ id: String(b.id) })
      return b.id
    } catch (err: any) {
      toast(err.message, 'error')
      return null
    }
  }

  const handleDraft = async () => {
    const savedId = await saveDraft()
    if (savedId) toast('暂存成功')
  }

  const handleSubmit = async () => {
    setLoading(true)
    try {
      const savedId = await saveDraft()
      if (!savedId) return
      const b = await bookingApi.submit(savedId)
      setStatus(b.status)
      toast('提交成功，已启动预定审批流')
    } catch (err: any) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setForm({ ...emptyForm })
    setBookingId(null)
    setStatus('')
    setSearchParams({})
  }

  return (
    <div className="card">
      <div className="card-title">
        <h2>预定申请</h2>
        <div className="toolbar">
          {status && status !== '草稿' && status !== '已驳回' && <Badge status={status} />}
          <button className="btn btn-secondary" onClick={handleReset}>
            <RotateCcw size={14} /> 重置
          </button>
          <button className="btn btn-secondary" onClick={handleDraft} disabled={!editable}>
            <Save size={14} /> 暂存
          </button>
          <button className="btn btn-primary" onClick={handleSubmit} disabled={!editable || loading}>
            <Send size={14} /> 提交
          </button>
        </div>
      </div>
      <p className="text-secondary" style={{ marginBottom: 16 }}>
        规则提示：结束时间须晚于开始时间；参会人数不得超过会议室容量；同室同日已提交时段不得重叠；
        参会人数达到 20 人及以上时，部门主管通过后还需行政经理复核。
      </p>
      <div className="form-grid-2">
        <div className="form-item">
          <label className="field-label required">会议室</label>
          <div className="field-control">
            <select value={form.room_id} onChange={(e) => set('room_id', e.target.value)} disabled={!editable}>
              <option value="">请选择</option>
              {rooms.map((r) => (
                <option key={r.id} value={r.id}>{r.room_name}（容纳 {r.capacity} 人，{r.location || ''}）</option>
              ))}
            </select>
          </div>
        </div>
        <div className="form-item">
          <label className="field-label required">预定日期</label>
          <div className="field-control">
            <input type="date" value={form.booking_date} onChange={(e) => set('booking_date', e.target.value)} disabled={!editable} />
          </div>
        </div>
        <div className="form-item">
          <label className="field-label required">开始时间</label>
          <div className="field-control">
            <input type="time" value={form.start_time} onChange={(e) => set('start_time', e.target.value)} disabled={!editable} />
          </div>
        </div>
        <div className="form-item">
          <label className="field-label required">结束时间</label>
          <div className="field-control">
            <input type="time" value={form.end_time} onChange={(e) => set('end_time', e.target.value)} disabled={!editable} />
          </div>
        </div>
        <div className="form-item">
          <label className="field-label required">会议主题</label>
          <div className="field-control">
            <input value={form.purpose} onChange={(e) => set('purpose', e.target.value)} disabled={!editable} />
          </div>
        </div>
        <div className="form-item">
          <label className="field-label required">参会人数</label>
          <div className="field-control">
            <input type="number" min={1} value={form.participants} onChange={(e) => set('participants', e.target.value)} disabled={!editable} />
          </div>
        </div>
      </div>
    </div>
  )
}
