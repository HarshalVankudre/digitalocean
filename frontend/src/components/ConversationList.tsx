import { useEffect, useState } from 'react'
import { api } from '../lib/api'

type Conversation = { id: string; title?: string }

type Props = {
  selected?: string
  onSelect: (id: string)=>void
  onNew: ()=>void
}

export default function ConversationList({selected, onSelect, onNew}: Props){
  const [items, setItems] = useState<Conversation[]>([])
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')

  const load = async ()=> {
    const r = await api.get('/conversations')
    setItems(r.data)
  }
  useEffect(()=>{ load() },[])

  const beginRename = (c: Conversation) => {
    setRenamingId(c.id)
    setRenameValue(c.title || 'Chat')
  }

  const submitRename = async (c: Conversation) => {
    const title = renameValue.trim()
    if (!title) return
    await api.patch(`/conversations/${c.id}`, { title })
    setRenamingId(null)
    await load()
  }

  const cancelRename = () => {
    setRenamingId(null)
    setRenameValue('')
  }

  const remove = async (c: Conversation) => {
  await api.delete(`/conversations/${c.id}`)
  if (selected === c.id) {
    onNew()
  }
  await load()
}


  return (
    <aside className="h-full w-64 border-r bg-slate-50/70 p-3">
      <button onClick={onNew} className="mb-3 w-full rounded-xl bg-slate-900 px-3 py-2 text-white">New chat</button>
      <ul className="space-y-1 text-sm">
        {items.map(c=> {
          const isActive = selected===c.id
          const isRenaming = renamingId===c.id
          return (
            <li key={c.id} className="group">
              <div className={`flex items-center gap-2 rounded-lg px-2 py-1 ${isActive ? 'bg-white shadow' : ''}`}>
                <button
                  onClick={()=>onSelect(c.id)}
                  className="flex-1 truncate text-left"
                  title={c.title || 'Chat'}
                >
                  {isRenaming ? (
                    <input
                      autoFocus
                      value={renameValue}
                      onChange={e=>setRenameValue(e.target.value)}
                      onKeyDown={(e)=> {
                        if (e.key==='Enter') submitRename(c)
                        if (e.key==='Escape') cancelRename()
                      }}
                      className="w-full rounded border px-2 py-1"
                    />
                  ) : (
                    <span>{c.title || 'Chat'}</span>
                  )}
                </button>

                {isRenaming ? (
                  <>
                    <button
                      onClick={()=>submitRename(c)}
                      className="rounded bg-emerald-600 px-2 py-1 text-white"
                      title="Save"
                    >Save</button>
                    <button
                      onClick={cancelRename}
                      className="rounded bg-slate-200 px-2 py-1"
                      title="Cancel"
                    >Cancel</button>
                  </>
                ) : (
                  <div className="invisible ml-auto flex gap-1 group-hover:visible">
                    <button
                      onClick={()=>beginRename(c)}
                      className="rounded bg-slate-200 px-2 py-1"
                      title="Rename"
                    >Rename</button>
                    <button
                      onClick={()=>remove(c)}
                      className="rounded bg-red-600 px-2 py-1 text-white"
                      title="Delete"
                    >Del</button>
                  </div>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}
