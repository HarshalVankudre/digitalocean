import { Link, useNavigate } from 'react-router-dom'

export default function Nav(){
  const nav = useNavigate()
  const logout = () => { localStorage.removeItem('token'); nav('/login') }
  return (
    <header className="border-b bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="font-semibold">Gradient Chat</Link>
        <nav className="flex gap-4 text-sm">
          <Link to="/">Chat</Link>
          <Link to="/admin">Admin</Link>
          <button onClick={logout} className="rounded-lg bg-slate-900 px-3 py-1.5 text-white">Logout</button>
        </nav>
      </div>
    </header>
  )
}
