import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { X, Sun, Building2, ArrowRight, Leaf, BarChart3 } from 'lucide-react'

export default function UserTypeModal({ isOpen, onClose }) {
  const navigate = useNavigate()
  const [hoveredCard, setHoveredCard] = useState(null)

  if (!isOpen) return null

  const handleSelect = (type) => {
    onClose()
    if (type === 'farmer') {
      navigate('/farmer-dashboard')
    } else {
      navigate('/enterprise-dashboard')
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Close button */}
        <button className="modal-close-btn" onClick={onClose}>
          <X size={20} />
        </button>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 14, fontSize: 11 }}>
            Choose Your Experience
          </div>
          <h2 className="font-grotesk" style={{
            fontSize: 'clamp(28px, 4vw, 42px)',
            fontWeight: 400,
            color: '#fff',
            letterSpacing: '-1px',
            lineHeight: 1.1,
            marginBottom: 12,
          }}>
            How will you use<br />Eliyonix?
          </h2>
          <p style={{ fontSize: 15, color: 'rgba(255,255,255,0.5)', maxWidth: 400, margin: '0 auto', lineHeight: 1.6 }}>
            We'll tailor the dashboard experience to match your needs
          </p>
        </div>

        {/* Cards */}
        <div className="user-type-cards">
          {/* Farmer Card */}
          <button
            className={`user-type-card ${hoveredCard === 'farmer' ? 'hovered' : ''}`}
            onMouseEnter={() => setHoveredCard('farmer')}
            onMouseLeave={() => setHoveredCard(null)}
            onClick={() => handleSelect('farmer')}
          >
            <div className="user-type-card-glow farmer-glow" />
            <div className="user-type-card-icon farmer-icon">
              <Sun size={32} strokeWidth={1.5} />
            </div>
            <div className="user-type-card-badge">
              <Leaf size={10} />
              <span>Simple & Visual</span>
            </div>
            <h3 className="font-grotesk user-type-card-title">
              Farmer / End User
            </h3>
            <p className="user-type-card-desc">
              Monitor your solar panel health with simple visual alerts. No technical jargon — just clear status updates.
            </p>
            <ul className="user-type-card-features">
              <li>☀️ Panel health at a glance</li>
              <li>🔔 Simple alert notifications</li>
              <li>📱 Mobile-friendly design</li>
              <li>🌾 Made for village use</li>
            </ul>
            <div className="user-type-card-cta">
              <span>Enter as Farmer</span>
              <ArrowRight size={16} />
            </div>
          </button>

          {/* Enterprise Card */}
          <button
            className={`user-type-card ${hoveredCard === 'enterprise' ? 'hovered' : ''}`}
            onMouseEnter={() => setHoveredCard('enterprise')}
            onMouseLeave={() => setHoveredCard(null)}
            onClick={() => handleSelect('enterprise')}
          >
            <div className="user-type-card-glow enterprise-glow" />
            <div className="user-type-card-icon enterprise-icon">
              <Building2 size={32} strokeWidth={1.5} />
            </div>
            <div className="user-type-card-badge enterprise-badge">
              <BarChart3 size={10} />
              <span>Data & Analytics</span>
            </div>
            <h3 className="font-grotesk user-type-card-title">
              Enterprise / DISCOM
            </h3>
            <p className="user-type-card-desc">
              Fleet-level analytics, multi-site monitoring, AI recommendations, and exportable reports.
            </p>
            <ul className="user-type-card-features">
              <li>📊 Multi-site fleet monitoring</li>
              <li>🤖 AI-powered recommendations</li>
              <li>⚡ Real-time agent decisions</li>
              <li>📋 DISCOM grid visibility</li>
            </ul>
            <div className="user-type-card-cta enterprise-cta">
              <span>Enter as Enterprise</span>
              <ArrowRight size={16} />
            </div>
          </button>
        </div>

        {/* Footer hint */}
        <div style={{ textAlign: 'center', marginTop: 36 }}>
          <span className="font-mono-e" style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', letterSpacing: '0.3px' }}>
            You can switch anytime from the dashboard
          </span>
        </div>
      </div>
    </div>
  )
}
