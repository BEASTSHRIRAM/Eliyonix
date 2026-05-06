import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import { ChevronDown, Play, Download, Map } from 'lucide-react'
import { sendSensorData, healthCheck } from '../services/api'

const BASE_SENSORS = { v: 415.2, i: 8.21, t: 31.8, ldr: 812 }
const FAULT_SENSORS = { v: 380.0, i: 12.5,  t: 68.4, ldr: 720 }
let backendResponse = null
let backendHealthy = false

function rand(base, pct) { return (base * (1 + (Math.random() - 0.5) * pct)).toFixed(base < 10 ? 2 : 1) }

function generateLog(sensors) {
  const ts = new Date().toLocaleTimeString('en-GB', { hour12: false })
  return `[${ts}] V=${sensors.v}V  I=${sensors.i}A  T=${sensors.t}°C  LDR=${sensors.ldr}`
}

function StatCard({ label, value, sub, subColor, mono, accentColor }) {
  return (
    <div className="card-stone" style={{ padding: '24px 22px', position: 'relative', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', top: 0, left: 0, width: 3, height: '100%', background: accentColor || 'var(--eliyonix-hairline)', borderRadius: '12px 0 0 12px' }} />
      <div className="mono-label" style={{ color: 'var(--eliyonix-muted)', marginBottom: 12, fontSize: 10 }}>{label}</div>
      <div className="font-grotesk stat-value" style={{ fontSize: 38, fontWeight: 400, color: 'var(--eliyonix-ink)', letterSpacing: '-1px', lineHeight: 1, marginBottom: 8 }}>{value}</div>
      <div style={{ fontSize: 13, color: subColor || 'var(--eliyonix-muted)', marginBottom: 8 }}>{sub}</div>
      <div className="font-mono-e" style={{ fontSize: 10, color: 'var(--eliyonix-muted)', letterSpacing: '0.4px', textTransform: 'uppercase' }}>{mono}</div>
    </div>
  )
}

function AgentDecisionCard({ name, statusChip, chipClass, metricLine, footerLine, accent }) {
  return (
    <div className="card" style={{ padding: '16px 18px', borderLeft: `3px solid ${accent}` }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <span className="font-mono-e" style={{ fontSize: 11, color: 'var(--eliyonix-muted)', letterSpacing: '0.3px' }}>{name}</span>
        <span className={`chip ${chipClass}`}>{statusChip}</span>
      </div>
      <div className="font-mono-e" style={{ fontSize: 20, color: 'var(--eliyonix-ink)', marginBottom: 8, letterSpacing: '-0.5px' }}>{metricLine}</div>
      <div style={{ fontSize: 12.5, color: 'var(--eliyonix-muted)' }}>{footerLine}</div>
    </div>
  )
}

const VILLAGES = [
  { id: 'KA_001', loc: 'Munnar, Kerala',      kw: '3.4 kW', score: '0.02', status: 'HEALTHY',  alert: '—',                 statusColor: '#00b464', chipClass: 'chip-green' },
  { id: 'KA_002', loc: 'Wayanad, Kerala',     kw: '1.8 kW', score: '0.65', status: 'WARNING',  alert: 'Dust detected',     statusColor: '#f5a623', chipClass: 'chip-coral' },
  { id: 'KA_003', loc: 'Kodagu, Karnataka',   kw: '0.0 kW', score: '0.95', status: 'CRITICAL', alert: 'Inverter offline',  statusColor: '#ff7759', chipClass: 'chip-coral' },
  { id: 'KA_004', loc: 'Hassan, Karnataka',   kw: '2.9 kW', score: '0.11', status: 'HEALTHY',  alert: '—',                 statusColor: '#00b464', chipClass: 'chip-green' },
  { id: 'KA_005', loc: 'Chitradurga, KA',     kw: '3.1 kW', score: '0.08', status: 'HEALTHY',  alert: '—',                 statusColor: '#00b464', chipClass: 'chip-green' },
]

export default function Dashboard() {
  const [scenario, setScenario] = useState('normal')
  const [logs, setLogs] = useState([])
  const [sensorVals, setSensorVals] = useState(BASE_SENSORS)
  const logRef = useRef(null)

  const isFault = scenario === 'fault'
  const isDust  = scenario === 'dust'

  const faultScore   = isFault ? '0.87' : isDust ? '0.41' : '0.02'
  const faultStatus  = isFault ? 'FAULT DETECTED' : isDust ? 'WARNING' : 'NORMAL'
  const faultChip    = isFault ? 'chip-coral' : isDust ? 'chip-coral' : 'chip-green'
  const faultAccent  = isFault ? '#ff7759' : isDust ? '#f5a623' : '#00b464'
  const alertStatus  = isFault ? 'ALERT SENT' : 'STANDBY'
  const alertChip    = isFault ? 'chip-coral' : 'chip-muted'
  const alertAccent  = isFault ? '#ff7759' : '#93939f'
  const alertBody    = isFault ? '[ALERT] Inverter stress detected. WhatsApp sent.' : 'No alerts triggered'
  const solarOutput  = isFault ? '1.8 kW' : isDust ? '2.1 kW' : '3.4 kW'
  const activeAlerts = isFault ? '1' : '0'

  useEffect(() => {
    const sensors = isFault ? FAULT_SENSORS : BASE_SENSORS
    const first = generateLog({ v: sensors.v, i: sensors.i, t: sensors.t, ldr: sensors.ldr })
    setLogs([first])
    setSensorVals(sensors)

    const t = setInterval(() => {
      setSensorVals(prev => {
        const pct = isFault ? 0.04 : 0.01
        const v   = rand(parseFloat(prev.v), pct)
        const i   = rand(parseFloat(prev.i), pct)
        const tp  = rand(parseFloat(prev.t), pct)
        const ldr = Math.round(parseFloat(prev.ldr) * (1 + (Math.random() - 0.5) * 0.02))
        const next = { v, i, t: tp, ldr }
        const line = generateLog(next)
        setLogs(prev2 => [line, ...prev2].slice(0, 30))
        return next
      })
    }, 2000)
    return () => clearInterval(t)
  }, [scenario])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = 0
  }, [logs])

  // Check backend health and send sensor data
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const isHealthy = await healthCheck()
        backendHealthy = isHealthy
        if (isHealthy) {
          console.log('✅ VidyutSeva backend is healthy')
          // Send current sensor data
          const response = await sendSensorData(sensorVals)
          backendResponse = response
          console.log('📊 Backend response:', response)
        } else {
          console.log('⚠️ VidyutSeva backend is not responding')
        }
      } catch (error) {
        console.log('❌ Backend error:', error.message)
      }
    }
    checkBackend()
  }, [])

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8f8f8' }}>
      <Sidebar />

      {/* Main */}
      <main className="main-with-sidebar" style={{ marginLeft: 230, flex: 1, padding: '0 0 48px' }}>
        {/* Top bar */}
        <div style={{
          background: '#fff', borderBottom: '1px solid var(--eliyonix-hairline)',
          padding: '0 32px', height: 62, display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 40,
        }}>
          <h1 className="font-grotesk" style={{ fontSize: 22, fontWeight: 500, letterSpacing: '-0.4px', color: 'var(--eliyonix-ink)' }}>Grid Overview</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 14px', border: '1px solid var(--eliyonix-hairline)', borderRadius: 8, background: '#fff', cursor: 'pointer' }}>
              <span style={{ fontSize: 13, color: 'var(--eliyonix-ink)' }}>Village: KA_001 — Munnar</span>
              <ChevronDown size={13} color="var(--eliyonix-muted)" />
            </div>
            <span className="font-mono-e" style={{ fontSize: 11, color: 'var(--eliyonix-muted)' }}>
              Last updated: {new Date().toLocaleTimeString('en-GB', { hour12: false })}
            </span>
            <Link to="/agents" className="btn-primary" style={{ fontSize: 13, padding: '8px 18px' }}>
              <Play size={12} /> Run All Agents
            </Link>
          </div>
        </div>

        <div style={{ padding: '28px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* Stat cards */}
          <div className="four-col" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16 }}>
            <StatCard label="Solar Output" value={solarOutput}
              sub={isFault ? '↓ 47% — fault active' : '↑ 12% vs yesterday'} subColor={isFault ? '#ff7759' : '#00b464'}
              mono="Panel Efficiency: 87%" accentColor="#00b464" />
            <StatCard label="Fault Score" value={faultScore}
              sub={faultStatus} subColor={isFault ? '#ff7759' : '#00b464'}
              mono="Isolation Forest · Live" accentColor={faultAccent} />
            <StatCard label="Load Forecast" value="3.8 kW"
              sub="Peak expected at 16:00" mono="LSTM · Next 2 Hours" accentColor="#1863dc" />
            <StatCard label="Active Alerts" value={activeAlerts}
              sub={isFault ? 'Inverter stress — act now' : 'All systems nominal'} subColor={isFault ? '#ff7759' : 'var(--eliyonix-muted)'}
              mono="Alert Dispatcher · Standby" accentColor={isFault ? '#ff7759' : '#93939f'} />
          </div>

          {/* Live feed + Agent decisions */}
          <div className="two-col-flex" style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
            {/* Sensor log */}
            <div style={{ flex: '0 0 58%' }}>
              <div className="card-dark" style={{ borderRadius: 16, overflow: 'hidden' }}>
                <div style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="font-grotesk" style={{ fontSize: 15, color: '#fff', letterSpacing: '-0.3px' }}>Live Sensor Feed</span>
                  <span className="chip chip-green">LIVE</span>
                </div>
                <div ref={logRef} className="log-scroll" style={{ height: 220, overflowY: 'auto', padding: '14px 20px' }}>
                  {logs.map((l, i) => (
                    <div key={i} className="font-mono-e" style={{ fontSize: 12, color: i === 0 ? '#4ade80' : 'rgba(74,222,128,0.4)', marginBottom: 5, transition: 'color 0.3s' }}>
                      {l}
                    </div>
                  ))}
                </div>
                <div style={{ padding: '10px 20px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                  <span className="font-mono-e" style={{ fontSize: 10.5, color: 'rgba(255,255,255,0.35)' }}>
                    village/ka_001/sensors/inv001
                  </span>
                </div>
                <div style={{ padding: '10px 20px', borderTop: '1px solid rgba(255,255,255,0.07)', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {['Voltage','Current','Temperature','LDR'].map(t => (
                    <span key={t} className="filter-pill active">{t}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Agent decisions */}
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ fontSize: 15, fontWeight: 500, color: 'var(--eliyonix-ink)', fontFamily: "'Space Grotesk', sans-serif", letterSpacing: '-0.3px', marginBottom: 2 }}>Agent Decisions</div>
              <AgentDecisionCard
                name="FaultDetectorAgent" statusChip={faultStatus} chipClass={faultChip}
                metricLine={`Anomaly score: ${faultScore}`}
                footerLine={`Decision: ${faultStatus} · Confidence: ${isFault ? '94' : '99'}%`}
                accent={faultAccent}
              />
              <AgentDecisionCard
                name="LoadForecasterAgent" statusChip="RUNNING" chipClass="chip-blue"
                metricLine="Forecast 2h: 3.8 kW"
                footerLine="Trend: INCREASING · Demand spike at 16:00"
                accent="#1863dc"
              />
              <AgentDecisionCard
                name="AlertDispatcherAgent" statusChip={alertStatus} chipClass={alertChip}
                metricLine={alertBody}
                footerLine={isFault ? 'Sent via Twilio WhatsApp · Just now' : 'Last alert: 2 days ago'}
                accent={alertAccent}
              />
            </div>
          </div>

          {/* Scenario Simulator */}
          <div className="card-stone" style={{ padding: '28px 28px' }}>
            <div style={{ marginBottom: 18 }}>
              <div className="font-grotesk" style={{ fontSize: 18, color: 'var(--eliyonix-ink)', letterSpacing: '-0.3px', marginBottom: 6 }}>Scenario Simulator</div>
              <div style={{ fontSize: 13.5, color: 'var(--eliyonix-muted)' }}>Test agent response on different fault scenarios</div>
            </div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {[
                { key: 'normal', label: 'Normal Operation' },
                { key: 'dust',   label: 'Dust / Efficiency Drop' },
                { key: 'fault',  label: 'Inverter Fault' },
              ].map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setScenario(key)}
                  className="filter-pill"
                  style={{
                    padding: '9px 22px', fontSize: 12, fontFamily: "'DM Sans', sans-serif",
                    fontWeight: 500, letterSpacing: '0',
                    borderColor: scenario === key ? 'var(--eliyonix-coral)' : 'var(--eliyonix-hairline)',
                    color: scenario === key ? 'var(--eliyonix-coral)' : 'var(--eliyonix-ink)',
                    background: scenario === key ? 'rgba(255,119,89,0.06)' : 'transparent',
                    transition: 'all 0.3s ease',
                  }}
                >
                  {label}
                </button>
              ))}
            </div>
            {isFault && (
              <div className="font-mono-e" style={{
                marginTop: 16, padding: '12px 16px', background: 'rgba(255,119,89,0.08)',
                border: '1px solid rgba(255,119,89,0.25)', borderRadius: 8,
                fontSize: 12, color: '#ff7759', lineHeight: 1.6,
                transition: 'all 0.3s ease',
              }}>
                [ALERT] Inverter stress detected. Anomaly score jumped to 0.87. WhatsApp alert sent to field technician.
              </div>
            )}
          </div>

          {/* DISCOM Table */}
          <div style={{ background: 'var(--eliyonix-pale-blue)', borderRadius: 16, padding: '28px 28px' }}>
            <div style={{ marginBottom: 20 }}>
              <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 8 }}>DISCOM Grid View</div>
              <div className="font-grotesk" style={{ fontSize: 20, color: 'var(--eliyonix-ink)', letterSpacing: '-0.3px' }}>District-Level Solar Visibility</div>
            </div>

            <div style={{ background: '#fff', borderRadius: 10, border: '1px solid var(--eliyonix-hairline)', overflow: 'hidden' }}>
              {/* Table header */}
              <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr 110px 110px 130px 1fr', padding: '10px 18px', borderBottom: '1px solid var(--eliyonix-hairline)', background: 'var(--eliyonix-stone)' }}>
                {['Village ID','Location','Solar Output','Fault Score','Status','Last Alert'].map(h => (
                  <span key={h} className="mono-label" style={{ fontSize: 9.5, color: 'var(--eliyonix-muted)' }}>{h}</span>
                ))}
              </div>

              {VILLAGES.map((v, i) => (
                <div key={v.id} className="table-row" style={{
                  display: 'grid', gridTemplateColumns: '100px 1fr 110px 110px 130px 1fr',
                  padding: '13px 18px', borderBottom: i < VILLAGES.length - 1 ? '1px solid var(--eliyonix-hairline)' : 'none',
                  alignItems: 'center', transition: 'background 0.15s',
                }}>
                  <span className="font-mono-e" style={{ fontSize: 12, color: 'var(--eliyonix-ink)', fontWeight: 600 }}>{v.id}</span>
                  <span style={{ fontSize: 13.5, color: 'var(--eliyonix-ink)' }}>{v.loc}</span>
                  <span style={{ fontSize: 13.5, color: 'var(--eliyonix-ink)' }}>{v.kw}</span>
                  <span className="font-mono-e" style={{ fontSize: 12, color: parseFloat(v.score) > 0.6 ? '#ff7759' : parseFloat(v.score) > 0.35 ? '#f5a623' : 'var(--eliyonix-ink)' }}>{v.score}</span>
                  <span className={`chip ${v.chipClass}`}>{v.status}</span>
                  <span style={{ fontSize: 13, color: v.alert === '—' ? 'var(--eliyonix-muted)' : 'var(--eliyonix-ink)' }}>{v.alert}</span>
                </div>
              ))}
            </div>

            <div style={{ marginTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <span style={{ fontSize: 12.5, color: 'var(--eliyonix-muted)' }}>Showing 5 of 127 monitored installations</span>
              <div style={{ display: 'flex', gap: 20 }}>
                <button className="btn-text-blue" style={{ fontSize: 13 }}><Download size={13} /> Export to CSV</button>
                <button className="btn-text-blue" style={{ fontSize: 13 }}><Map size={13} /> View Full Map</button>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  )
}
