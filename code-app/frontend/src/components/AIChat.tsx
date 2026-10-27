import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, Sparkles } from 'lucide-react'
import { aiApi } from '../api/ai'
import { toast } from './toast'

interface Msg { role: 'user' | 'assistant'; text: string; path?: string; label?: string }

export default function AIChat() {
  const navigate = useNavigate()
  const [messages, setMessages] = useState<Msg[]>([
    { role: 'assistant', text: '我是本地规则助手（不调用外部大模型）。试试问：“会议室有哪些”“预定统计”或“BOO0001 预定情况”。' },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return
    setMessages((m) => [...m, { role: 'user', text }])
    setInput('')
    setLoading(true)
    try {
      const res = await aiApi.chat(text)
      setMessages((m) => [...m, { role: 'assistant', text: res.reply, path: res.action?.path, label: res.action?.label }])
    } catch (err: any) {
      toast(err.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="chat-header">
        <div className="chat-logo"><Sparkles size={16} /></div>
        <span className="chat-title">AI 智能助理（本地规则版）</span>
      </div>
      <div className="chat-body" style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 12 }}>
        {messages.map((m, i) => (
          <div key={i} style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', maxWidth: '90%' }}>
            <div style={{ whiteSpace: 'pre-wrap', background: m.role === 'user' ? '#e0f2fe' : '#f1f5f9', padding: '8px 12px', borderRadius: 8 }}>
              {m.text}
            </div>
            {m.path && (
              <button className="btn btn-secondary btn-sm" style={{ marginTop: 6 }} onClick={() => navigate(m.path!)}>
                {m.label || '打开'}
              </button>
            )}
          </div>
        ))}
        {loading && <div className="text-secondary">思考中…</div>}
      </div>
      <div style={{ display: 'flex', gap: 8, padding: 12, borderTop: '1px solid var(--divider-color)' }}>
        <input
          style={{ flex: 1 }}
          value={input}
          placeholder="问问预定、会议室或统计…"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') send() }}
        />
        <button className="btn btn-primary" onClick={send} disabled={loading}>
          <Send size={14} />
        </button>
      </div>
    </div>
  )
}
