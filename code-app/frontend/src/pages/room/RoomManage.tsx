import { useEffect, useState } from 'react'
import { Plus } from 'lucide-react'
import { roomApi, type Room } from '../../api/room'
import { toast } from '../../components/toast'
import { Badge } from '../../utils/status'

export default function RoomManage() {
  const [rooms, setRooms] = useState<Room[]>([])
  const [form, setForm] = useState({ room_name: '', capacity: '', location: '' })

  const load = () => roomApi.list().then(setRooms).catch(() => {})

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!form.room_name || !form.capacity) {
      toast('请填写会议室名称与容纳人数', 'error')
      return
    }
    try {
      await roomApi.create({ room_name: form.room_name, capacity: Number(form.capacity), location: form.location })
      toast('新增成功')
      setForm({ room_name: '', capacity: '', location: '' })
      load()
    } catch (err: any) {
      toast(err.message, 'error')
    }
  }

  return (
    <div>
      <div className="card" style={{ padding: '20px' }}>
        <h3 style={{ fontWeight: 700, marginBottom: 16 }}>新增会议室（仅管理员可见该菜单；接口同样校验 room:create 权限）</h3>
        <div className="form-grid-3">
          <div className="form-item">
            <label className="field-label required">会议室名称</label>
            <div className="field-control">
              <input value={form.room_name} onChange={(e) => setForm({ ...form, room_name: e.target.value })} />
            </div>
          </div>
          <div className="form-item">
            <label className="field-label required">容纳人数</label>
            <div className="field-control">
              <input type="number" min={1} value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} />
            </div>
          </div>
          <div className="form-item">
            <label className="field-label">位置</label>
            <div className="field-control">
              <input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
            </div>
          </div>
        </div>
        <div className="toolbar-right">
          <button className="btn btn-primary" onClick={handleCreate}>
            <Plus size={14} /> 新增
          </button>
        </div>
      </div>
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="table-container">
          <table>
            <thead>
              <tr><th>会议室编号</th><th>会议室名称</th><th>容纳人数</th><th>位置</th><th>状态</th></tr>
            </thead>
            <tbody>
              {rooms.map((r) => (
                <tr key={r.id}>
                  <td>{r.room_no}</td><td>{r.room_name}</td><td>{r.capacity}</td>
                  <td>{r.location || '-'}</td><td><Badge status={r.status} /></td>
                </tr>
              ))}
              {rooms.length === 0 && (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: '#94a3b8' }}>暂无数据</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
