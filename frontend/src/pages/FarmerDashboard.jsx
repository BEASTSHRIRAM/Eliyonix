import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Activity, ArrowLeft, Bell, CheckCircle, ChevronRight, Phone, RefreshCw, Sun, Thermometer, Zap } from 'lucide-react'
import { getLiveGridState } from '../services/api'

const EMPTY_SENSOR = {
  voltage: null,
  current: null,
  temperature: null,
  ldr: null,
  power_kw: null,
  village_id: 'KA_001',
  inverter_id: 'INV_001',
}

function formatValue(value, suffix = '') {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '--'
  return `${Number(value).toFixed(suffix === ' kW' ? 2 : 1)}${suffix}`
}

function HealthGauge({ value, color }) {
  const radius = 72
  const stroke = 10
  const circumference = 2 * Math.PI * radius
  const dashOffset = circumference - (value / 100) * circumference

  return (
    <div className="farmer-gauge">
      <svg width="184" height="184" viewBox="0 0 184 184">
        <circle cx="92" cy="92" r={radius} fill="none" stroke="var(--eliyonix-hairline)" strokeWidth={stroke} />
        <circle
          cx="92"
          cy="92"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          transform="rotate(-90 92 92)"
        />
      </svg>
      <div className="farmer-gauge-value">
        <span className="font-grotesk">{value}</span>
        <small>%</small>
      </div>
    </div>
  )
}

function StatusCard({ icon: Icon, title, value, subtitle, color }) {
  return (
    <div className="farmer-status-card" style={{ borderLeftColor: color }}>
      <Icon size={22} strokeWidth={1.6} color={color} />
      <div>
        <div className="mono-label" style={{ fontSize: 10, color: 'var(--eliyonix-muted)', marginBottom: 7 }}>{title}</div>
        <div className="font-grotesk" style={{ fontSize: 28, color: 'var(--eliyonix-ink)', letterSpacing: '-0.6px', lineHeight: 1 }}>{value}</div>
        <div style={{ fontSize: 13, color: 'var(--eliyonix-muted)', marginTop: 6 }}>{subtitle}</div>
      </div>
    </div>
  )
}

function AgentDot({ label, ok }) {
  return (
    <div className="farmer-agent-dot">
      <span className="pulse-dot" style={{ background: ok ? '#00b464' : '#f5a623' }} />
      <span>{label}</span>
      <span className={`chip ${ok ? 'chip-green' : 'chip-coral'}`}>{ok ? 'READY' : 'WAITING'}</span>
    </div>
  )
}

export default function FarmerDashboard() {
  const [liveState, setLiveState] = useState(null)
  const [error, setError] = useState('')
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    let active = true

    async function loadLiveState() {
      try {
        const data = await getLiveGridState('KA_001')
        if (!active) return
        setLiveState(data)
        setError('')
      } catch (err) {
        if (!active) return
        setError('Waiting for backend live grid state')
      }
    }

    loadLiveState()
    const poll = setInterval(loadLiveState, 3000)
    const clock = setInterval(() => setNow(new Date()), 1000)

    return () => {
      active = false
      clearInterval(poll)
      clearInterval(clock)
    }
  }, [])

  const latest = liveState?.latest
  const sensor = latest?.sensor_data || EMPTY_SENSOR
  const derived = latest?.derived || {}
  const agent = latest?.agent_result || {}
  const powerKw = sensor.power_kw ?? ((Number(sensor.voltage) * Number(sensor.current)) / 1000)
  const panelHealth = derived.panel_health ?? 0
  const hasData = Boolean(latest)
  const isFault = Boolean(agent.fault_detected)
  const gaugeColor = isFault ? '#ff7759' : panelHealth >= 70 ? '#00b464' : '#f5a623'
  const healthLabel = !hasData ? 'Waiting for MQTT' : isFault ? 'Needs Attention' : 'Healthy'
  const alerts = liveState?.alerts || []
  const logs = liveState?.logs || []

  const feedText = useMemo(() => {
    if (!hasData) return 'MQTT subscriber has not published a sensor reading yet'
    return `Panel is generating ${formatValue(powerKw, ' kW')} from inverter ${sensor.inverter_id}`
  }, [hasData, powerKw, sensor.inverter_id])

  return (
    <div className="farmer-dashboard">
      <header className="farmer-topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Link to="/" className="farmer-back-link"><ArrowLeft size={18} /></Link>
          <div>
            <h1 className="font-grotesk">Munnar Village</h1>
            <div className="font-mono-e">KA_001 · {now.toLocaleTimeString('en-GB', { hour12: true, hour: '2-digit', minute: '2-digit' })}</div>
          </div>
        </div>
        <Link to="/enterprise-dashboard" className="farmer-switch-btn">
          Enterprise View <ChevronRight size={14} />
        </Link>
      </header>

      <main className="farmer-main">
        <div className="farmer-ticker">
          <Activity size={14} />
          <span>{error || feedText}</span>
          <span className={`chip ${hasData ? 'chip-green' : 'chip-coral'}`}>{hasData ? 'MQTT LIVE' : 'WAITING'}</span>
        </div>

        <section className="card-stone farmer-health-card">
          <div>
            <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 10 }}>Solar Health</div>
            <h2 className="font-grotesk">{healthLabel}</h2>
            <p>{hasData ? 'Live readings are coming from the backend MQTT publish stream.' : 'Start the MQTT subscriber or publish a sensor message to update this dashboard.'}</p>
          </div>
          <HealthGauge value={panelHealth} color={gaugeColor} />
        </section>

        <section className="farmer-cards-row">
          <StatusCard icon={Sun} title="Today's Power" value={formatValue(powerKw, ' kW')} subtitle={hasData ? 'Live inverter output' : 'No reading received'} color="#00b464" />
          <StatusCard icon={CheckCircle} title="Panel Status" value={isFault ? 'Check Panel' : hasData ? 'All Good' : 'Waiting'} subtitle={agent.fault_type || 'Fault detector status'} color={isFault ? '#ff7759' : '#00b464'} />
          <StatusCard icon={Bell} title="Next Alert" value={alerts.length ? 'Active' : 'None'} subtitle={alerts[0]?.message || 'No active alert from dispatcher'} color={alerts.length ? '#ff7759' : '#93939f'} />
        </section>

        <section className="farmer-section-card">
          <div className="farmer-section-header">
            <span className="font-grotesk">Agent Status</span>
          </div>
          <AgentDot label="Fault Check" ok={hasData && !isFault} />
          <AgentDot label="Power Forecast" ok={hasData} />
          <AgentDot label="Alert System" ok={hasData && !agent.should_alert} />
        </section>

        <section className="farmer-sensor-strip">
          <div className="farmer-sensor-item"><Zap size={18} color="#1863dc" /><span>Voltage</span><strong>{formatValue(sensor.voltage, 'V')}</strong></div>
          <div className="farmer-sensor-divider" />
          <div className="farmer-sensor-item"><Activity size={18} color="#1863dc" /><span>Current</span><strong>{formatValue(sensor.current, 'A')}</strong></div>
          <div className="farmer-sensor-divider" />
          <div className="farmer-sensor-item"><Thermometer size={18} color="#ff7759" /><span>Temperature</span><strong>{formatValue(sensor.temperature, '°C')}</strong></div>
        </section>

        <section className="farmer-section-card">
          <div className="farmer-section-header">
            <span className="font-grotesk">Recent Alerts</span>
          </div>
          {alerts.length ? alerts.slice(0, 5).map((alert, index) => (
            <div className="farmer-alert-item" key={`${alert.timestamp}-${index}`}>
              <span className={`chip ${alert.severity === 'critical' ? 'chip-coral' : 'chip-blue'}`}>{alert.severity}</span>
              <span>{alert.message}</span>
            </div>
          )) : (
            <div className="farmer-alert-item muted">No alerts from the MQTT-fed agent pipeline.</div>
          )}
        </section>

        <section className="card-dark farmer-live-feed">
          <div className="font-grotesk">Live Sensor Feed</div>
          {logs.slice(0, 5).map((log, index) => (
            <div className="font-mono-e" key={`${log.timestamp}-${index}`}>
              V={formatValue(log.voltage, 'V')} I={formatValue(log.current, 'A')} T={formatValue(log.temperature, '°C')} P={formatValue(log.power_kw, ' kW')}
            </div>
          ))}
          {!logs.length && <div className="font-mono-e">Waiting for MQTT topic village/ka_001/sensors/inv_001</div>}
        </section>

        <section className="farmer-actions">
          <button className="farmer-action-btn primary"><Phone size={18} /> Call Technician</button>
          <button className="farmer-action-btn secondary"><RefreshCw size={18} /> Request Maintenance</button>
        </section>
      </main>
    </div>
  )
}
