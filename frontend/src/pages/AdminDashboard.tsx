import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import FormField from '../components/FormField'

export default function AdminDashboard(){
  const [baseUrl, setBaseUrl] = useState('')
  const [key, setKey] = useState('')
  const [retrieval, setRetrieval] = useState(true)
  const [functions, setFunctions] = useState(false)
  const [guardrails, setGuardrails] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(()=>{ api.get('/settings').then(r=>{
    setBaseUrl(r.data.do_agent_base_url||'')
    setKey(r.data.do_agent_access_key||'')
    setRetrieval(r.data.include_retrieval_info)
    setFunctions(r.data.include_functions_info)
    setGuardrails(r.data.include_guardrails_info)
  }) },[])

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setMsg('')
    await api.put('/settings', {
      do_agent_base_url: baseUrl,
      do_agent_access_key: key,
      include_retrieval_info: retrieval,
      include_functions_info: functions,
      include_guardrails_info: guardrails,
    })
    setMsg('Saved!')
  }

  return (
    <div className="mx-auto max-w-3xl p-6">
      <h1 className="mb-4 text-xl font-semibold">Agent Settings</h1>
      {msg && <p className="mb-3 rounded-lg bg-green-50 p-2 text-green-700">{msg}</p>}
      <form onSubmit={save} className="space-y-4">
        <FormField label="Agent Base URL" value={baseUrl} onChange={setBaseUrl} placeholder="https://<agent>.ondigitalocean.app" />
        <FormField label="Agent Access Key" value={key} onChange={setKey} placeholder="sk-..." />
        <div className="grid grid-cols-3 gap-4">
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={retrieval} onChange={e=>setRetrieval(e.target.checked)} /> Retrieval info</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={functions} onChange={e=>setFunctions(e.target.checked)} /> Functions info</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={guardrails} onChange={e=>setGuardrails(e.target.checked)} /> Guardrails info</label>
        </div>
        <button className="rounded-xl bg-slate-900 px-4 py-2 text-white">Save</button>
      </form>

      <div className="mt-10">
        <h2 className="mb-2 font-medium">User Management</h2>
        <CreateUserForm />
      </div>
    </div>
  )
}

function CreateUserForm(){
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState<'admin'|'user'>('user')
  const [msg, setMsg] = useState('')

  const create = async (e: React.FormEvent) => {
    e.preventDefault(); setMsg('')
    await api.post('/auth/register', { email, name, password, role })
    setMsg('User created')
    setEmail(''); setName(''); setPassword(''); setRole('user')
  }

  return (
    <form onSubmit={create} className="space-y-3 rounded-2xl border bg-white p-4">
      {msg && <p className="rounded bg-green-50 p-2 text-green-700">{msg}</p>}
      <div className="grid grid-cols-2 gap-4">
        <FormField label="Email" value={email} onChange={setEmail} />
        <FormField label="Name" value={name} onChange={setName} />
        <FormField label="Password" value={password} onChange={setPassword} type="password" />
        <label className="block text-sm">
          <span className="text-slate-600">Role</span>
          <select value={role} onChange={e=>setRole(e.target.value as any)} className="mt-1 w-full rounded-xl border px-3 py-2">
            <option value="user">User</option>
            <option value="admin">Admin</option>
          </select>
        </label>
      </div>
      <button className="rounded-xl bg-slate-900 px-4 py-2 text-white">Create User</button>
    </form>
  )
}
