import { Routes, Route, Navigate } from 'react-router-dom'
import Nav from './components/Nav'
import Login from './pages/Login'
import Chat from './pages/Chat'
import AdminDashboard from './pages/AdminDashboard'

function Private({ children }:{children: JSX.Element}){
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

export default function App(){
  return (
    <div>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Private><><Nav /><Chat /></></Private>} />
        <Route path="/admin" element={<Private><><Nav /><AdminDashboard /></></Private>} />
      </Routes>
    </div>
  )
}
