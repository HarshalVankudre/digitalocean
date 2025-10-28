import { useEffect, useState } from 'react'
import ConversationList from '../components/ConversationList'
import ChatMessage from '../components/ChatMessage'
import { api } from '../lib/api'

export default function Chat(){
  const [cid, setCid] = useState<string>('')
  const [messages, setMessages] = useState<any[]>([])
  const [input, setInput] = useState('')
  const [busy, setBusy] = useState(false)

  // ---- NEW: smarter init (no auto-create on refresh)
  useEffect(() => {
    const init = async () => {
      // 1) try last opened
      const saved = localStorage.getItem('cid')
      if (saved) {
        const ok = await tryOpen(saved)
        if (ok) return
      }
      // 2) try most recent existing
      try {
        const r = await api.get('/conversations')
        if (Array.isArray(r.data) && r.data.length > 0) {
          await open(r.data[0].id)
          return
        }
      } catch {}
      // 3) none exist -> create first one
      await newChat()
    }
    init()
  }, [])

  const tryOpen = async (id: string) => {
    try {
      await open(id)
      return true
    } catch {
      return false
    }
  }

  const newChat = async () => {
    const r = await api.post('/conversations', { title: 'New chat' })
    const newId = r.data.id as string
    localStorage.setItem('cid', newId)
    setCid(newId)
    setMessages([])
  }

  const open = async (id: string) => {
    const r = await api.get(`/conversations/${id}`)
    localStorage.setItem('cid', id)
    setCid(id)
    setMessages(r.data.messages)
  }

  const send = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !cid) return
    const localUserMsg = { role: 'user', content: input }
    setMessages(m => [...m, { id: 'local-u-'+Date.now(), ...localUserMsg }])
    setInput(''); setBusy(true)
    try {
      const r = await api.post(`/conversations/${cid}/messages`, { content: localUserMsg.content })
      setMessages(m => [...m, r.data])
    } finally { setBusy(false) }
  }

  return (
    <div className="flex h-[calc(100vh-56px)]">
      <ConversationList
        selected={cid}
        onSelect={(id)=>open(id)}
        onNew={newChat}
      />
      <main className="flex-1">
        <div className="mx-auto flex h-full max-w-3xl flex-col px-4">
          <div className="flex-1 overflow-y-auto py-6">
            {messages.map(m=> <ChatMessage key={m.id} role={m.role} content={m.content} />)}
          </div>
          <form onSubmit={send} className="mb-6 flex gap-2">
            <input
              value={input}
              onChange={e=>setInput(e.target.value)}
              placeholder="Ask anything…"
              className="flex-1 rounded-2xl border px-4 py-3 shadow-sm"
            />
            <button
              disabled={busy || !cid}
              className="rounded-2xl bg-slate-900 px-6 py-3 text-white disabled:opacity-60"
            >
              Send
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}
