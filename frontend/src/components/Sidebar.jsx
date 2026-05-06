import { Link, useLocation } from 'react-router-dom'
import { LayoutDashboard, Bot, Radio, Bell, Building2, Wifi, Cpu } from 'lucide-react'
import LogoIcon from './LogoIcon'

const navItems = [
  { icon: LayoutDashboard, label: 'Overview',    path: '/dashboard' },
  { icon: Bot,             label: 'Agents',      path: '/agents' },
  { icon: Radio,           label: 'Sensor Feed', path: '/dashboard' },
  { icon: Bell,            label: 'Alerts',      path: '/dashboard' },
  { icon: Building2,       label: 'DISCOM View', path: '/dashboard' },
]

export default function Sidebar() {
  const { pathname } = useLocation()

  return (
    <aside className="sidebar">
      <div style={{ padding: '22px 18px 18px', borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none' }}>
          <div style={{ width: 30, height: 30, background: 'var(--eliyonix-green)', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <LogoIcon size={18} color="#ffffff" />
          </div>
          <span className="font-grotesk" style={{ fontSize: 16, fontWeight: 700, color: '#fff', letterSpacing: '-0.4px' }}>Eliyonix</span>
        </Link>
      </div>

      <nav style={{ padding: '10px 0', flex: 1 }}>
        {navItems.map(({ icon: Icon, label, path }) => (
          <Link
            key={label}
            to={path}
            className={`sidebar-item ${pathname === path ? 'active' : ''}`}
          >
            <Icon size={15} strokeWidth={1.6} />
            {label}
          </Link>
        ))}
      </nav>

      <div style={{ padding: '14px 18px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
        <div className="mono-label" style={{ color: 'rgba(255,255,255,0.3)', marginBottom: 10, fontSize: 10 }}>Connection</div>
        {[
          { icon: <Wifi size={11} />, label: 'MQTT', status: 'CONNECTED', ok: true },
          { icon: <Cpu size={11} />,  label: 'Edge', status: 'ONLINE',    ok: true },
          { icon: <Bot size={11} />,  label: 'Bedrock', status: 'READY',  ok: true },
        ].map(({ icon, label, status, ok }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 7 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ color: ok ? '#00b464' : '#ff7759' }}>{icon}</span>
              <span className="font-mono-e" style={{ fontSize: 10.5, color: 'rgba(255,255,255,0.45)' }}>{label}</span>
            </div>
            <span className="font-mono-e" style={{ fontSize: 10, color: ok ? '#00b464' : '#ff7759' }}>{status}</span>
          </div>
        ))}
        <div style={{ display: 'flex', alignItems: 'center', gap: 7, marginTop: 10, paddingTop: 10, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="pulse-dot" style={{ background: '#00b464' }} />
          <span className="font-mono-e" style={{ fontSize: 10.5, color: 'rgba(255,255,255,0.5)' }}>3 agents active</span>
        </div>
      </div>
    </aside>
  )
}
