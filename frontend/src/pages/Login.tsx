import { useState } from 'react'
import { api } from '../lib/api'
import FormField from '../components/FormField'
import { useNavigate } from 'react-router-dom'

export default function Login(){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const nav = useNavigate()

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErr('')
    try{
      const r = await api.post('/auth/login', null, { params: { email, password } })
      localStorage.setItem('token', r.data.access_token)
      nav('/')
    }catch(e:any){ setErr(e?.response?.data?.detail || 'Login failed') }
  }

  return (
    <div className="grid min-h-screen place-items-center bg-slate-50">
      <form onSubmit={submit} className="w-[380px] space-y-4 rounded-2xl bg-white p-6 shadow-lg">
        <h1 className="text-xl font-semibold">Sign in</h1>
        {err && <p className="rounded-lg bg-red-50 p-2 text-sm text-red-700">{err}</p>}
        <FormField label="Email" value={email} onChange={setEmail} type="email" />
        <FormField label="Password" value={password} onChange={setPassword} type="password" />
        <button className="w-full rounded-xl bg-slate-900 px-3 py-2 text-white">Continue</button>
      </form>
    </div>
  )
}
