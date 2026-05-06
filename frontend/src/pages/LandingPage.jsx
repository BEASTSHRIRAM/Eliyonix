import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Nav from '../components/Nav'
import UserTypeModal from '../components/UserTypeModal'
import { ArrowRight, Wifi, Database, Cloud, Server, ChevronRight } from 'lucide-react'

const LOG_LINES = [
  '[14:32:01] Sensor INV_001: V=415.2V I=8.21A T=31.8°C',
  '[14:32:03] FaultAgent: score=0.02 → NORMAL',
  '[14:32:05] LoadAgent: forecast_2h=3.4kW → ON TRACK',
  '[14:32:07] Sensor INV_001: V=414.8V I=8.19A T=32.0°C',
  '[14:32:09] FaultAgent: score=0.03 → NORMAL',
  '[14:32:11] AlertDispatcher: STANDBY · No alerts',
  '[14:32:13] Sensor INV_001: V=416.1V I=8.24A T=32.1°C',
  '[14:32:15] LoadAgent: demand_peak=16:00 · 3.8kW',
]

function AgentConsole() {
  const [visibleLines, setVisibleLines] = useState([LOG_LINES[0]])
  const scrollRef = useRef(null)

  useEffect(() => {
    let i = 1
    const t = setInterval(() => {
      setVisibleLines(prev => {
        const next = [LOG_LINES[i % LOG_LINES.length], ...prev].slice(0, 10)
        return next
      })
      i++
    }, 2000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = 0
  }, [visibleLines])

  return (
    <div className="card-dark dot-grid-bg" style={{ borderRadius: 22, overflow: 'hidden', position: 'relative' }}>
      {/* Header */}
      <div style={{ padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="font-mono-e" style={{ fontSize: 11, color: 'rgba(255,255,255,0.55)', letterSpacing: '0.4px' }}>
          ELIYONIX · LIVE AGENT CONSOLE
        </span>
        <div style={{ display: 'flex', gap: 6 }}>
          {['#ff5f57','#febc2e','#28c840'].map(c => (
            <div key={c} style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />
          ))}
        </div>
      </div>

      {/* Agent status rows */}
      <div style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {[
          { dot: '#00b464', label: 'Fault Detector Agent',   status: 'Monitoring · Village KA_001',    chipColor: 'chip-green' },
          { dot: '#f5a623', label: 'Load Forecaster Agent',  status: 'Predicting · Next 2h demand',    chipColor: 'chip-coral' },
          { dot: '#1863dc', label: 'Alert Dispatcher Agent', status: 'Standby · No alerts',            chipColor: 'chip-blue' },
        ].map(({ dot, label, status, chipColor }) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: dot, flexShrink: 0 }} />
              <span className="font-mono-e" style={{ fontSize: 11, color: 'rgba(255,255,255,0.75)', letterSpacing: '0.2px' }}>{label}</span>
            </div>
            <span className={`chip ${chipColor}`} style={{ fontSize: 9.5, whiteSpace: 'nowrap' }}>{status}</span>
          </div>
        ))}
      </div>

      {/* Log */}
      <div ref={scrollRef} className="log-scroll" style={{ padding: '14px 20px', height: 160, overflowY: 'auto' }}>
        {visibleLines.map((line, i) => (
          <div key={i} className="font-mono-e" style={{ fontSize: 11.5, color: i === 0 ? '#4ade80' : 'rgba(74,222,128,0.45)', marginBottom: 5, transition: 'color 0.5s' }}>
            {line}
          </div>
        ))}
      </div>

      {/* Bottom pill */}
      <div style={{ padding: '12px 20px', borderTop: '1px solid rgba(255,255,255,0.07)', display: 'flex', gap: 8 }}>
        <span className="chip chip-green">MQTT CONNECTED</span>
        <span className="chip chip-coral">EDGE ONLINE</span>
      </div>
    </div>
  )
}

function StatCard({ value, label }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.12)',
      borderRadius: 16, padding: '28px 24px', textAlign: 'center', flex: 1,
    }}>
      <div className="font-grotesk" style={{ fontSize: 52, fontWeight: 400, color: '#fff', letterSpacing: '-1px', lineHeight: 1 }}>{value}</div>
      <div className="font-dm" style={{ fontSize: 14, color: 'rgba(255,255,255,0.55)', marginTop: 10, lineHeight: 1.45 }}>{label}</div>
    </div>
  )
}

function HowStep({ num, title, body, icon: Icon }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ width: 52, height: 52, border: '1.5px solid var(--eliyonix-hairline)', borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon size={22} strokeWidth={1.4} color="var(--eliyonix-ink)" />
      </div>
      <div className="font-mono-e" style={{ fontSize: 28, color: 'var(--eliyonix-coral)', fontWeight: 300, lineHeight: 1 }}>{num}</div>
      <div className="text-card-heading" style={{ color: 'var(--eliyonix-ink)' }}>{title}</div>
      <div style={{ fontSize: 15, lineHeight: 1.65, color: 'var(--eliyonix-ink)', opacity: 0.68 }}>{body}</div>
    </div>
  )
}

function AgentCard({ num, title, sub, metric, chipLabel, chipClass }) {
  return (
    <div style={{
      background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)',
      borderRadius: 16, padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: 10,
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div>
          <div className="font-mono-e" style={{ fontSize: 13, color: 'var(--eliyonix-coral)', marginBottom: 6 }}>{num}</div>
          <div className="font-grotesk" style={{ fontSize: 17, color: '#fff', letterSpacing: '-0.3px' }}>{title}</div>
          <div style={{ fontSize: 12.5, color: 'rgba(255,255,255,0.45)', marginTop: 3 }}>{sub}</div>
        </div>
        <span className={`chip ${chipClass}`}>{chipLabel}</span>
      </div>
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 10 }}>
        <div className="font-mono-e" style={{ fontSize: 11.5, color: 'rgba(255,255,255,0.65)', lineHeight: 1.5 }}>{metric}</div>
      </div>
    </div>
  )
}

export default function LandingPage() {
  const [showModal, setShowModal] = useState(false)

  return (
    <div style={{ background: 'var(--eliyonix-canvas)' }}>
      <Nav onDemoClick={() => setShowModal(true)} />
      <UserTypeModal isOpen={showModal} onClose={() => setShowModal(false)} />

      {/* ── HERO ── */}
      <section style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', padding: '80px 32px 80px', maxWidth: 1280, margin: '0 auto' }}>
        <div className="hero-flex" style={{ display: 'flex', gap: 60, alignItems: 'center', width: '100%' }}>
          {/* Left */}
          <div style={{ flex: '0 0 58%', maxWidth: '58%' }}>
            <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 24 }}>
              Grid Modernisation · Rural India
            </div>
            <h1 className="text-hero" style={{ color: 'var(--eliyonix-ink)', marginBottom: 28 }}>
              Solar mini-grids<br />run blind.<br />Not anymore.
            </h1>
            <p style={{ fontSize: 17, lineHeight: 1.7, color: 'var(--eliyonix-ink)', opacity: 0.7, maxWidth: 460, marginBottom: 36 }}>
              Eliyonix puts a 5-agent AI layer on existing rural solar hardware.
              Fault detection, load forecasting, and real-time alerts — before the village goes dark.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: 20, marginBottom: 52, flexWrap: 'wrap' }}>
              <button onClick={() => setShowModal(true)} className="btn-primary">
                See Live Demo <ArrowRight size={15} />
              </button>
              <a href="#how-it-works" className="btn-text-blue">How it works ↓</a>
            </div>

            {/* Trust strip */}
            <div style={{ borderTop: '1px solid var(--eliyonix-hairline)', paddingTop: 24 }}>
              <div className="mono-label" style={{ color: 'var(--eliyonix-muted)', marginBottom: 16, fontSize: 10 }}>Built With</div>
              <div style={{ display: 'flex', gap: 28, alignItems: 'center', flexWrap: 'wrap' }}>
                {['AWS Bedrock', 'AgentScope', 'LangGraph', 'Supabase'].map(t => (
                  <span key={t} style={{ fontSize: 13, fontWeight: 600, color: 'var(--eliyonix-muted)', letterSpacing: '0.2px', fontFamily: "'DM Sans', sans-serif" }}>{t}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Right – Agent Console */}
          <div style={{ flex: '0 0 40%', maxWidth: '40%' }}>
            <AgentConsole />
          </div>
        </div>
      </section>

      {/* ── PROBLEM BAND ── */}
      <section style={{ background: 'var(--eliyonix-green)', padding: '90px 32px' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', textAlign: 'center' }}>
          <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 20 }}>The Problem</div>
          <h2 className="text-section" style={{ color: '#fff', marginBottom: 20, maxWidth: 680, margin: '0 auto 20px' }}>
            60% of India's rural solar<br />installations are dark.
          </h2>
          <p style={{ fontSize: 16.5, color: 'rgba(255,255,255,0.65)', maxWidth: 580, margin: '0 auto 56px', lineHeight: 1.7 }}>
            Panels lose 40% output from dust. Batteries degrade silently.
            Nobody knows until the village goes dark.
            The hardware is there. The intelligence layer is not.
          </p>
          <div className="font-mono-e" style={{ fontSize: 11, color: 'rgba(255,255,255,0.35)', marginBottom: 56, letterSpacing: '0.3px' }}>
            — IEA Global Renewable Capacity Report
          </div>

          {/* Stat cards */}
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', justifyContent: 'center' }}>
            <StatCard value="40%" label="Solar output lost to dust annually" />
            <StatCard value="60%" label="Rural mini-grids non-functional or degraded" />
            <StatCard value="3-5 days" label="Early fault warning with Eliyonix agents" />
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="how-it-works" style={{ padding: '100px 32px', background: 'var(--eliyonix-canvas)' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 64 }}>
            <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 16 }}>How It Works</div>
            <h2 className="text-section" style={{ color: 'var(--eliyonix-ink)' }}>
              From blind hardware<br />to intelligent grid.
            </h2>
          </div>
          <div className="three-col" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 48 }}>
            <HowStep
              num="01" title="Sense" icon={Wifi}
              body="ESP32 sensors stream voltage, current, and temperature from inverters every 2 seconds. MQTT buffered locally on Raspberry Pi — works even when 3G is down."
            />
            <HowStep
              num="02" title="Think" icon={Cloud}
              body="Three AI agents analyze in parallel: Fault Detector (Isolation Forest), Load Forecaster (LSTM), Alert Dispatcher (Bedrock Claude). They vote before deciding — zero false alarms."
            />
            <HowStep
              num="03" title="Act" icon={Server}
              body="Technician gets WhatsApp alert in Kannada or Hindi before failure happens. DISCOM sees real-time village grid health. No app needed. Works on 2G."
            />
          </div>
        </div>
      </section>

      {/* ── AGENT ARCHITECTURE BAND ── */}
      <section id="agents" style={{ background: 'var(--eliyonix-green)', padding: '90px 32px' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto', display: 'flex', gap: 72, alignItems: 'flex-start', flexWrap: 'wrap' }}>
          {/* Left text */}
          <div style={{ flex: '0 0 42%', minWidth: 280 }}>
            <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 18 }}>Multi-Agent System</div>
            <h2 className="text-section" style={{ color: '#fff', marginBottom: 22 }}>
              Three agents.<br />One consensus.<br />Zero false alarms.
            </h2>
            <p style={{ fontSize: 16, color: 'rgba(255,255,255,0.62)', lineHeight: 1.7, marginBottom: 32, maxWidth: 400 }}>
              Eliyonix agents collaborate before acting. If solar output drops 40%, all three agents vote:
              is this a fault, dust, or just a cloudy day?
              LangGraph orchestrates the state machine. AgentScope manages agent memory.
            </p>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <Link to="/agents" className="btn-outline">View Architecture <ChevronRight size={14} /></Link>
              <button className="btn-text-white">Read Docs</button>
            </div>
          </div>

          {/* Agent cards */}
          <div style={{ flex: 1, minWidth: 280, display: 'flex', flexDirection: 'column', gap: 14 }}>
            <AgentCard num="01" title="Fault Detector Agent" sub="Isolation Forest · AWS Bedrock"
              metric="Anomaly score: 0.87 → FAULT CONFIRMED" chipLabel="ACTIVE" chipClass="chip-green" />
            <AgentCard num="02" title="Load Forecaster Agent" sub="LSTM · TimescaleDB"
              metric="Next 2h: 3.8kW demand spike predicted" chipLabel="RUNNING" chipClass="chip-blue" />
            <AgentCard num="03" title="Alert Dispatcher Agent" sub="Bedrock Claude · Twilio"
              metric="WhatsApp → 'Inverter fail predicted. Visit Thu.'" chipLabel="SENT" chipClass="chip-coral" />
          </div>
        </div>
      </section>

      {/* ── MARKET BAND ── */}
      <section id="discom" style={{ background: 'var(--eliyonix-navy)', padding: '90px 32px' }}>
        <div style={{ maxWidth: 900, margin: '0 auto', textAlign: 'center' }}>
          <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 18 }}>Market Opportunity</div>
          <h2 className="text-section" style={{ color: '#fff', marginBottom: 22 }}>
            10 lakh installations.<br />One missing layer.
          </h2>
          <p style={{ fontSize: 16, color: 'rgba(255,255,255,0.6)', lineHeight: 1.7, maxWidth: 560, margin: '0 auto 56px' }}>
            PM Kusum Phase C is deploying solar across rural India at scale.
            Eliyonix is the monitoring and intelligence middleware that makes that investment actually work.
          </p>
          <div style={{ display: 'flex', gap: 32, justifyContent: 'center', flexWrap: 'wrap' }}>
            {[
              { val: '₹50/month', desc: 'Per installation SaaS' },
              { val: '6 months',  desc: 'ROI per installation' },
              { val: 'USD 4.2B',  desc: 'Global off-grid solar market by 2030' },
            ].map(({ val, desc }) => (
              <div key={val} style={{ textAlign: 'center' }}>
                <div className="font-grotesk" style={{ fontSize: 40, color: '#fff', letterSpacing: '-1px', lineHeight: 1 }}>{val}</div>
                <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.45)', marginTop: 8 }}>{desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer style={{ background: 'var(--eliyonix-near-black)', padding: '64px 32px 32px' }}>
        <div style={{ maxWidth: 1280, margin: '0 auto' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 40, marginBottom: 52 }}>
            {/* Brand */}
            <div>
              <div className="font-grotesk" style={{ fontSize: 18, fontWeight: 700, color: '#fff', marginBottom: 8 }}>Eliyonix</div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)', lineHeight: 1.6 }}>Intelligent grids<br />for rural India</div>
            </div>
            {/* Product */}
            <div>
              <div className="mono-label" style={{ color: 'rgba(255,255,255,0.3)', marginBottom: 14, fontSize: 10 }}>Product</div>
              {['Dashboard', 'Agents', 'DISCOM View', 'API Docs'].map(l => (
                <div key={l} style={{ marginBottom: 9 }}>
                  <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', cursor: 'pointer' }}>{l}</span>
                </div>
              ))}
            </div>
            {/* Hackathon */}
            <div>
              <div className="mono-label" style={{ color: 'rgba(255,255,255,0.3)', marginBottom: 14, fontSize: 10 }}>Hackathon</div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', lineHeight: 1.7 }}>
                Cognizant GenAI 2026<br />
                Team BeastDevs<br />
                Sriram Kulkarni<br />
                Sukruthindra HP
              </div>
            </div>
            {/* Subscribe */}
            <div>
              <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 14, fontSize: 10 }}>Stay Updated</div>
              <div style={{ display: 'flex', gap: 0 }}>
                <input
                  type="email"
                  placeholder="your@email.com"
                  style={{
                    flex: 1, padding: '9px 14px', borderRadius: '8px 0 0 8px',
                    border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)',
                    color: '#fff', fontSize: 13, fontFamily: "'DM Sans', sans-serif", outline: 'none',
                  }}
                />
                <button style={{
                  padding: '9px 14px', borderRadius: '0 8px 8px 0',
                  background: 'var(--eliyonix-coral)', border: 'none', cursor: 'pointer',
                  display: 'flex', alignItems: 'center',
                }}>
                  <ArrowRight size={15} color="#fff" />
                </button>
              </div>
            </div>
          </div>

          <div style={{ borderTop: '1px solid rgba(255,255,255,0.07)', paddingTop: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)' }}>© 2026 Eliyonix. All rights reserved.</span>
            <span className="font-mono-e" style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', letterSpacing: '0.3px' }}>
              Built with AWS Bedrock · AgentScope · LangGraph
            </span>
          </div>
        </div>
      </footer>
    </div>
  )
}
