import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import { ArrowRight } from 'lucide-react'

const FAULT_LOGS = [
  '[14:32:01] Input: V=415V I=8.2A T=32°C',
  '[14:32:01] Score: 0.02 → BELOW THRESHOLD',
  '[14:32:01] Decision: NORMAL · passing to LoadForecaster',
  '[14:32:03] Input: V=414.8V I=8.19A T=31.9°C',
  '[14:32:03] Score: 0.03 → NORMAL',
]

const LOAD_LOGS = [
  '[14:32:01] Historical load window: 7 days loaded',
  '[14:32:02] LSTM inference: next_2h=3.8kW',
  '[14:32:02] Current load: 3.4kW → Trend: RISING',
  '[14:32:04] Demand spike flagged at 16:00',
]

const ALERT_LOGS = [
  '[14:30:05] Consensus received: FAULT=false, LOAD=normal',
  '[14:30:05] AlertDispatcher: STANDBY — no action needed',
  '[14:28:00] Previous alert: Inverter overheat warning',
  '[14:28:01] Bedrock Claude: message generated in Kannada',
  '[14:28:02] Twilio: WhatsApp sent to +91-XXXXXXXXXX',
]

function LogBlock({ lines, color = '#4ade80' }) {
  return (
    <div className="card-dark" style={{ borderRadius: 10, padding: '14px 18px', marginTop: 14 }}>
      {lines.map((l, i) => (
        <div key={i} className="font-mono-e" style={{ fontSize: 11.5, color: i === 0 ? color : `${color}66`, marginBottom: 5, lineHeight: 1.5 }}>{l}</div>
      ))}
    </div>
  )
}

function MetricRow({ items }) {
  return (
    <div style={{ display: 'flex', gap: 0, marginTop: 16, marginBottom: 4, borderTop: '1px solid var(--eliyonix-hairline)', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--eliyonix-hairline)' }}>
      {items.map(({ label, value }, i) => (
        <div key={label} style={{ flex: 1, padding: '12px 16px', borderRight: i < items.length - 1 ? '1px solid var(--eliyonix-hairline)' : 'none' }}>
          <div className="mono-label" style={{ fontSize: 9.5, color: 'var(--eliyonix-muted)', marginBottom: 5 }}>{label}</div>
          <div className="font-mono-e" style={{ fontSize: 14, color: 'var(--eliyonix-ink)', fontWeight: 600 }}>{value}</div>
        </div>
      ))}
    </div>
  )
}

export default function AgentMonitor() {
  const [time, setTime] = useState(new Date().toLocaleTimeString('en-GB', { hour12: false }))

  useEffect(() => {
    const t = setInterval(() => setTime(new Date().toLocaleTimeString('en-GB', { hour12: false })), 1000)
    return () => clearInterval(t)
  }, [])

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8f8f8' }}>
      <Sidebar />

      <main className="main-with-sidebar" style={{ marginLeft: 230, flex: 1 }}>

        {/* Header band */}
        <div style={{ background: 'var(--eliyonix-green)', padding: '60px 48px 56px' }}>
          <div style={{ maxWidth: 1100, margin: '0 auto' }}>
            <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 16 }}>Agent Runtime</div>
            <h1 className="text-section" style={{ color: '#fff', marginBottom: 18, maxWidth: 520 }}>
              Live agent<br />intelligence layer.
            </h1>
            <p style={{ fontSize: 15.5, color: 'rgba(255,255,255,0.6)', lineHeight: 1.7, maxWidth: 480, marginBottom: 28 }}>
              LangGraph orchestrates state. AgentScope manages memory. Bedrock Claude generates alerts.
            </p>
            <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
              {[
                { label: 'LangGraph: ACTIVE', chipClass: 'chip-green' },
                { label: 'AgentScope: RUNNING', chipClass: 'chip-blue' },
                { label: 'Bedrock: CONNECTED', chipClass: 'chip-white' },
              ].map(({ label, chipClass }) => (
                <span key={label} className={`chip ${chipClass}`} style={{ fontSize: 11 }}>{label}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Agent cards */}
        <div style={{ padding: '40px 48px 56px', maxWidth: 1200, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* Card 1 — Fault Detector */}
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ background: 'var(--eliyonix-pale-green)', padding: '28px 32px', borderBottom: '1px solid var(--eliyonix-hairline)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <div className="font-mono-e" style={{ fontSize: 40, color: 'var(--eliyonix-coral)', fontWeight: 300, lineHeight: 1, marginBottom: 12 }}>01</div>
                  <div className="font-grotesk" style={{ fontSize: 24, color: 'var(--eliyonix-ink)', letterSpacing: '-0.5px', marginBottom: 6 }}>Fault Detector Agent</div>
                  <div style={{ fontSize: 14, color: 'var(--eliyonix-muted)' }}>Isolation Forest · Real-time Anomaly Detection</div>
                </div>
                <span className="chip chip-green" style={{ fontSize: 11, marginTop: 4 }}>ACTIVE · {time}</span>
              </div>
            </div>
            <div style={{ padding: '28px 32px' }}>
              <div className="mono-label" style={{ color: 'var(--eliyonix-muted)', marginBottom: 10, fontSize: 10 }}>How it works</div>
              <p style={{ fontSize: 15, color: 'var(--eliyonix-ink)', opacity: 0.72, lineHeight: 1.7, maxWidth: 640, marginBottom: 4 }}>
                Reads voltage, current, and temperature from MQTT stream. Runs Isolation Forest model trained on normal
                operating data. Returns anomaly score (0 = normal, 1 = critical fault).
              </p>
              <MetricRow items={[
                { label: 'Current Score', value: '0.02' },
                { label: 'Threshold',     value: '0.60' },
                { label: 'Status',        value: 'NORMAL' },
              ]} />
              <LogBlock lines={FAULT_LOGS} color="#4ade80" />
              <div className="font-mono-e" style={{ fontSize: 11, color: 'var(--eliyonix-muted)', marginTop: 12 }}>
                Framework: AgentScope + scikit-learn
              </div>
            </div>
          </div>

          {/* Card 2 — Load Forecaster */}
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ background: 'var(--eliyonix-pale-blue)', padding: '28px 32px', borderBottom: '1px solid var(--eliyonix-hairline)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <div className="font-mono-e" style={{ fontSize: 40, color: 'var(--eliyonix-coral)', fontWeight: 300, lineHeight: 1, marginBottom: 12 }}>02</div>
                  <div className="font-grotesk" style={{ fontSize: 24, color: 'var(--eliyonix-ink)', letterSpacing: '-0.5px', marginBottom: 6 }}>Load Forecaster Agent</div>
                  <div style={{ fontSize: 14, color: 'var(--eliyonix-muted)' }}>LSTM · TimescaleDB · Demand Prediction</div>
                </div>
                <span className="chip chip-blue" style={{ fontSize: 11, marginTop: 4 }}>RUNNING</span>
              </div>
            </div>
            <div style={{ padding: '28px 32px' }}>
              <div className="mono-label" style={{ color: 'var(--eliyonix-muted)', marginBottom: 10, fontSize: 10 }}>How it works</div>
              <p style={{ fontSize: 15, color: 'var(--eliyonix-ink)', opacity: 0.72, lineHeight: 1.7, maxWidth: 640, marginBottom: 4 }}>
                LSTM trained on 7 days of historical load data. Predicts demand for the next 2 hours. Helps FaultDetector
                distinguish a demand spike from an actual fault — eliminating false alarms.
              </p>
              <MetricRow items={[
                { label: 'Forecast 2h', value: '3.8 kW' },
                { label: 'Current',     value: '3.4 kW' },
                { label: 'Trend',       value: 'RISING' },
              ]} />
              <LogBlock lines={LOAD_LOGS} color="#60a5fa" />
              <div className="font-mono-e" style={{ fontSize: 11, color: 'var(--eliyonix-muted)', marginTop: 12 }}>
                Framework: AgentScope + TensorFlow/Keras · TimescaleDB
              </div>
            </div>
          </div>

          {/* Card 3 — Alert Dispatcher */}
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ background: 'var(--eliyonix-stone)', padding: '28px 32px', borderBottom: '1px solid var(--eliyonix-hairline)' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <div className="font-mono-e" style={{ fontSize: 40, color: 'var(--eliyonix-coral)', fontWeight: 300, lineHeight: 1, marginBottom: 12 }}>03</div>
                  <div className="font-grotesk" style={{ fontSize: 24, color: 'var(--eliyonix-ink)', letterSpacing: '-0.5px', marginBottom: 6 }}>Alert Dispatcher Agent</div>
                  <div style={{ fontSize: 14, color: 'var(--eliyonix-muted)' }}>Bedrock Claude · Twilio · Local Language Alerts</div>
                </div>
                <span className="chip chip-muted" style={{ fontSize: 11, marginTop: 4 }}>STANDBY</span>
              </div>
            </div>
            <div style={{ padding: '28px 32px' }}>
              <div className="mono-label" style={{ color: 'var(--eliyonix-muted)', marginBottom: 10, fontSize: 10 }}>How it works</div>
              <p style={{ fontSize: 15, color: 'var(--eliyonix-ink)', opacity: 0.72, lineHeight: 1.7, maxWidth: 640, marginBottom: 16 }}>
                Receives consensus from FaultDetector + LoadForecaster. If fault confirmed (not a demand spike),
                calls Bedrock Claude to generate a natural language alert in Kannada or Hindi. Sends via Twilio WhatsApp.
              </p>

              {/* Kannada alert preview */}
              <div className="card-dark" style={{ borderRadius: 10, padding: '16px 20px', marginBottom: 10 }}>
                <div className="font-mono-e" style={{ fontSize: 13, color: '#fb923c', marginBottom: 8, lineHeight: 1.6 }}>
                  ನಿಮ್ಮ ಇನ್ವರ್ಟರ್ ಅಧಿಕ ತಾಪಮಾನದಲ್ಲಿದೆ.
                </div>
                <div style={{ fontSize: 12.5, color: 'rgba(255,255,255,0.4)' }}>
                  "Your inverter is overheating." — Kannada (auto-translated by Bedrock Claude)
                </div>
              </div>

              <MetricRow items={[
                { label: 'Last Alert',  value: '2 days ago' },
                { label: 'Channel',     value: 'WhatsApp' },
                { label: 'Language',    value: 'Kannada' },
              ]} />
              <LogBlock lines={ALERT_LOGS} color="#fb923c" />
              <div className="font-mono-e" style={{ fontSize: 11, color: 'var(--eliyonix-muted)', marginTop: 12 }}>
                Framework: Bedrock Claude · Twilio WhatsApp API · AgentScope
              </div>
            </div>
          </div>

          {/* LangGraph Flow Diagram */}
          <div style={{ background: 'var(--eliyonix-near-black)', borderRadius: 16, padding: '40px 40px', marginTop: 8 }}>
            <div style={{ textAlign: 'center', marginBottom: 36 }}>
              <div className="font-grotesk" style={{ fontSize: 26, color: '#fff', letterSpacing: '-0.5px', marginBottom: 8 }}>Agent State Machine</div>
              <div style={{ fontSize: 13.5, color: 'rgba(255,255,255,0.4)' }}>Orchestrated by LangGraph · State managed by AgentScope</div>
            </div>

            {/* Flow SVG */}
            <div style={{ overflowX: 'auto', paddingBottom: 8 }}>
              <svg viewBox="0 0 900 160" style={{ width: '100%', maxWidth: 900, display: 'block', margin: '0 auto', minWidth: 560 }}>
                {/* Nodes */}
                {[
                  { x: 20,  y: 55, w: 110, label: 'Sensor\nData' },
                  { x: 175, y: 55, w: 130, label: 'FaultDetector' },
                  { x: 355, y: 55, w: 140, label: 'LoadForecaster' },
                  { x: 545, y: 55, w: 140, label: 'Consensus\nCheck' },
                  { x: 545, y: 115, w: 140, label: 'Log + Wait' },
                  { x: 735, y: 30, w: 145, label: 'AlertDispatcher' },
                  { x: 735, y: 90, w: 145, label: 'SMS / WhatsApp' },
                ].map(({ x, y, w, label }, i) => (
                  <g key={i}>
                    <rect x={x} y={y} width={w} height={38} rx={7} fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={1} />
                    {label.split('\n').map((line, li) => (
                      <text key={li} x={x + w / 2} y={y + (label.includes('\n') ? 14 + li * 14 : 23)} textAnchor="middle"
                        fill="rgba(255,255,255,0.75)" fontSize={10.5} fontFamily="JetBrains Mono, monospace" letterSpacing="0.2">
                        {line}
                      </text>
                    ))}
                  </g>
                ))}

                {/* Arrows */}
                <defs>
                  <marker id="arrowW" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L6,3 L0,6 Z" fill="rgba(255,255,255,0.3)" />
                  </marker>
                  <marker id="arrowC" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                    <path d="M0,0 L6,3 L0,6 Z" fill="#ff7759" />
                  </marker>
                </defs>

                {/* Sensor → Fault */}
                <line x1={130} y1={74} x2={172} y2={74} stroke="rgba(255,255,255,0.25)" strokeWidth={1} markerEnd="url(#arrowW)" />
                {/* Fault → Load */}
                <line x1={305} y1={74} x2={352} y2={74} stroke="rgba(255,255,255,0.25)" strokeWidth={1} markerEnd="url(#arrowW)" />
                {/* Load → Consensus */}
                <line x1={495} y1={74} x2={542} y2={74} stroke="rgba(255,255,255,0.25)" strokeWidth={1} markerEnd="url(#arrowW)" />
                {/* Consensus → AlertDispatcher */}
                <line x1={685} y1={65} x2={732} y2={48} stroke="#ff7759" strokeWidth={1} markerEnd="url(#arrowC)" />
                {/* Consensus → Log */}
                <line x1={685} y1={83} x2={732} y2={128} stroke="rgba(255,255,255,0.2)" strokeWidth={1} markerEnd="url(#arrowW)" />
                {/* AlertDispatcher → SMS */}
                <line x1={807} y1={68} x2={807} y2={87} stroke="rgba(255,255,255,0.25)" strokeWidth={1} markerEnd="url(#arrowW)" />

                {/* Labels */}
                <text x={683} y={56} textAnchor="middle" fill="#ff7759" fontSize={9} fontFamily="JetBrains Mono, monospace">FAULT</text>
                <text x={683} y={96} textAnchor="middle" fill="rgba(255,255,255,0.3)" fontSize={9} fontFamily="JetBrains Mono, monospace">NORMAL</text>
              </svg>
            </div>
          </div>

          {/* Back link */}
          <div style={{ textAlign: 'center', paddingTop: 8 }}>
            <Link to="/dashboard" className="btn-primary" style={{ fontSize: 13, display: 'inline-flex' }}>
              <ArrowRight size={14} /> Back to Dashboard
            </Link>
          </div>
        </div>
      </main>
    </div>
  )
}
