import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { X, Menu } from 'lucide-react'
import LogoIcon from './LogoIcon'

export default function Nav() {
  const [barClosed, setBarClosed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const isLanding = location.pathname === '/'

  return (
    <>
      {!barClosed && (
        <div style={{
          background: 'var(--eliyonix-near-black)', height: 36,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          position: 'relative', padding: '0 48px',
        }}>
          <span className="font-mono-e" style={{ fontSize: 11.5, color: 'rgba(255,255,255,0.75)', letterSpacing: '0.4px' }}>
            Eliyonix is live at Cognizant GenAI Hackathon 2026 · Built for Rural India
          </span>
          <button onClick={() => setBarClosed(true)} style={{
            position: 'absolute', right: 16, background: 'none', border: 'none',
            cursor: 'pointer', color: 'rgba(255,255,255,0.45)', display: 'flex', alignItems: 'center',
          }}>
            <X size={13} />
          </button>
        </div>
      )}

      <nav className="site-nav">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', maxWidth: 1280, margin: '0 auto', padding: '0 32px' }}>
          {/* Wordmark */}
          <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 9, textDecoration: 'none' }}>
            <div style={{ width: 30, height: 30, background: 'var(--eliyonix-green)', borderRadius: 7, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <LogoIcon size={18} color="#ffffff" />
            </div>
            <span className="font-grotesk" style={{ fontSize: 17, fontWeight: 700, color: 'var(--eliyonix-ink)', letterSpacing: '-0.5px' }}>
              Eliyonix
            </span>
          </Link>

          {/* Desktop links */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 34 }} className="desktop-links">
            {isLanding ? (
              <>
                <a href="#how-it-works" className="nav-link-item">How it Works</a>
                <a href="#agents" className="nav-link-item">Agents</a>
                <a href="#discom" className="nav-link-item">DISCOM View</a>
                <Link to="/dashboard" className="nav-link-item">Demo</Link>
              </>
            ) : (
              <>
                <Link to="/" className="nav-link-item">Home</Link>
                <Link to="/dashboard" className="nav-link-item">Dashboard</Link>
                <Link to="/agents" className="nav-link-item">Agents</Link>
              </>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Link to="/dashboard" className="btn-primary" style={{ fontSize: 13.5, padding: '9px 22px' }}>
              View Demo
            </Link>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'none' }}
              className="mobile-menu-btn"
            >
              <Menu size={20} color="var(--eliyonix-ink)" />
            </button>
          </div>
        </div>
      </nav>

      {mobileOpen && (
        <div style={{ background: '#fff', borderBottom: '1px solid var(--eliyonix-hairline)', padding: '16px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Link to="/" onClick={() => setMobileOpen(false)} style={{ textDecoration: 'none', color: 'var(--eliyonix-ink)', fontSize: 14, fontWeight: 500 }}>Home</Link>
          <Link to="/dashboard" onClick={() => setMobileOpen(false)} style={{ textDecoration: 'none', color: 'var(--eliyonix-ink)', fontSize: 14, fontWeight: 500 }}>Dashboard</Link>
          <Link to="/agents" onClick={() => setMobileOpen(false)} style={{ textDecoration: 'none', color: 'var(--eliyonix-ink)', fontSize: 14, fontWeight: 500 }}>Agents</Link>
        </div>
      )}

      <style>{`
        .nav-link-item { text-decoration: none; color: var(--eliyonix-ink); font-size: 13.5px; font-weight: 500; opacity: 0.65; transition: opacity 0.2s; font-family: 'DM Sans', sans-serif; }
        .nav-link-item:hover { opacity: 1; }
        @media (max-width: 720px) { .desktop-links { display: none !important; } .mobile-menu-btn { display: flex !important; } }
      `}</style>
    </>
  )
}
