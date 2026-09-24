import { Outlet } from 'react-router-dom'
import Sidebar from '../components/layout/Sidebar'
import TopBar from '../components/layout/TopBar'

export default function AppLayout() {
  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
