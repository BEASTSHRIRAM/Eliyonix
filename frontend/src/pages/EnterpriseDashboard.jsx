import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import RecommendationCard from '../components/RecommendationCard'
import { ChevronDown, Download, Map, Play } from 'lucide-react'
import { getLiveGridState } from '../services/api'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function formatNumber(value, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '--'
  return Number(value).toFixed(digits)
}

function StatCard({ label, value, sub, accentColor }) {
  return (
    <div className="card-stone enterprise-stat">
      <div style={{ background: accentColor }} />
      <span className="mono-label">{label}</span>
      <strong className="font-grotesk">{value}</strong>
      <small>{sub}</small>
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

export default function EnterpriseDashboard() {
  const [liveState, setLiveState] = useState(null)
  const [recommendations, setRecommendations] = useState({})
  const logRef = useRef(null)

  useEffect(() => {
    let active = true

    async function loadLiveState() {
      try {
        const data = await getLiveGridState()
        if (active) setLiveState(data)
      } catch {
        if (active) setLiveState({ status: 'offline', logs: [], alerts: [], sites: [] })
      }
    }

    async function loadRecommendations() {
      try {
        const response = await fetch(`${API_BASE_URL}/recommendations`)
        const data = await response.json()
        if (active) setRecommendations(data.recommendations || {})
      } catch {
        if (active) setRecommendations({})
      }
    }

    loadLiveState()
    loadRecommendations()
    const livePoll = setInterval(loadLiveState, 3000)
    const recPoll = setInterval(loadRecommendations, 30000)

    return () => {
      active = false
      clearInterval(livePoll)
      clearInterval(recPoll)
    }
  }, [])

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = 0
  }, [liveState])

  const latest = liveState?.latest
  const sensor = latest?.sensor_data || {}
  const agent = latest?.agent_result || {}
  const derived = latest?.derived || {}
  const logs = liveState?.logs || []
  const alerts = liveState?.alerts || []
  const sites = liveState?.sites || []
  const hasData = Boolean(latest)
  const faultDetected = Boolean(agent.fault_detected)
  const powerKw = derived.power_kw ?? sensor.power_kw
  const anomalyScore = formatNumber(agent.anomaly_score || 0, 2)
  const totalPower = sites.reduce((sum, site) => sum + Number(site.derived?.power_kw || 0), 0)
  const avgHealth = sites.length
    ? Math.round(sites.reduce((sum, site) => sum + Number(site.derived?.panel_health || 0), 0) / sites.length)
    : 0

  const tableRows = sites.length ? sites : latest ? [latest] : []

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8f8f8' }}>
      <Sidebar />

      <main className="main-with-sidebar" style={{ marginLeft: 230, flex: 1, padding: '0 0 48px' }}>
        <div style={{
          background: '#fff', borderBottom: '1px solid var(--eliyonix-hairline)',
          padding: '0 32px', minHeight: 62, display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 40, gap: 18, flexWrap: 'wrap',
        }}>
          <h1 className="font-grotesk" style={{ fontSize: 22, fontWeight: 500, letterSpacing: '-0.4px', color: 'var(--eliyonix-ink)' }}>Enterprise Grid Overview</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
            <span className={`chip ${hasData ? 'chip-green' : 'chip-coral'}`}>{hasData ? 'MQTT LIVE' : 'WAITING FOR MQTT'}</span>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '7px 14px', border: '1px solid var(--eliyonix-hairline)', borderRadius: 8, background: '#fff' }}>
              <span style={{ fontSize: 13, color: 'var(--eliyonix-ink)' }}>Village: {sensor.village_id || 'KA_001'}</span>
              <ChevronDown size={13} color="var(--eliyonix-muted)" />
            </div>
            <Link to="/agents" className="btn-primary" style={{ fontSize: 13, padding: '8px 18px' }}>
              <Play size={12} /> Run All Agents
            </Link>
          </div>
        </div>

        <div style={{ padding: '28px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>
          <div className="four-col" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: 16 }}>
            <StatCard label="Total Sites" value={String(Math.max(sites.length, hasData ? 1 : 0))} sub="MQTT publishing sites" accentColor="#1863dc" />
            <StatCard label="Active Faults" value={String(alerts.length || (faultDetected ? 1 : 0))} sub={faultDetected ? agent.fault_type || 'Fault detected' : 'No active alert'} accentColor={faultDetected ? '#ff7759' : '#93939f'} />
            <StatCard label="Avg Efficiency" value={`${avgHealth || derived.panel_health || 0}%`} sub="From latest agent score" accentColor="#00b464" />
            <StatCard label="Total Power" value={`${formatNumber(totalPower || powerKw, 2)} kW`} sub="Live inverter output" accentColor="#00b464" />
          </div>

          <div className="two-col-flex" style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
            <div style={{ flex: '0 0 58%' }}>
              <div className="card-dark" style={{ borderRadius: 16, overflow: 'hidden' }}>
                <div style={{ padding: '14px 20px', borderBottom: '1px solid rgba(255,255,255,0.07)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="font-grotesk" style={{ fontSize: 15, color: '#fff', letterSpacing: '-0.3px' }}>Live Sensor Feed</span>
                  <span className={`chip ${hasData ? 'chip-green' : 'chip-coral'}`}>{hasData ? 'LIVE' : 'EMPTY'}</span>
                </div>
                <div ref={logRef} className="log-scroll" style={{ height: 220, overflowY: 'auto', padding: '14px 20px' }}>
                  {logs.map((log, i) => (
                    <div key={`${log.timestamp}-${i}`} className="font-mono-e" style={{ fontSize: 12, color: i === 0 ? '#4ade80' : 'rgba(74,222,128,0.4)', marginBottom: 5 }}>
                      [{new Date((log.timestamp || 0) * 1000).toLocaleTimeString('en-GB', { hour12: false })}] {log.village_id}/{log.inverter_id} V={formatNumber(log.voltage)}V I={formatNumber(log.current)}A T={formatNumber(log.temperature)}°C P={formatNumber(log.power_kw, 2)}kW
                    </div>
                  ))}
                  {!logs.length && (
                    <div className="font-mono-e" style={{ fontSize: 12, color: 'rgba(255,255,255,0.45)' }}>
                      Waiting for MQTT topic village/ka_001/sensors/inv_001
                    </div>
                  )}
                </div>
                <div style={{ padding: '10px 20px', borderTop: '1px solid rgba(255,255,255,0.07)' }}>
                  <span className="font-mono-e" style={{ fontSize: 10.5, color: 'rgba(255,255,255,0.35)' }}>
                    {latest?.topic || 'village/ka_001/sensors/inv_001'}
                  </span>
                </div>
              </div>
            </div>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div style={{ fontSize: 15, fontWeight: 500, color: 'var(--eliyonix-ink)', fontFamily: "'Space Grotesk', sans-serif", letterSpacing: '-0.3px', marginBottom: 2 }}>Agent Decisions</div>
              <AgentDecisionCard name="FaultDetectorAgent" statusChip={faultDetected ? 'FAULT DETECTED' : hasData ? 'NORMAL' : 'WAITING'} chipClass={faultDetected ? 'chip-coral' : hasData ? 'chip-green' : 'chip-muted'} metricLine={`Anomaly score: ${anomalyScore}`} footerLine={`Decision from latest MQTT payload · ${sensor.inverter_id || 'No inverter yet'}`} accent={faultDetected ? '#ff7759' : '#00b464'} />
              <AgentDecisionCard name="LoadForecasterAgent" statusChip={agent.is_demand_spike ? 'SPIKE' : hasData ? 'RUNNING' : 'WAITING'} chipClass={agent.is_demand_spike ? 'chip-coral' : hasData ? 'chip-blue' : 'chip-muted'} metricLine={`Forecast 2h: ${formatNumber(agent.demand_forecast?.demand_2h, 2)} kW`} footerLine="Updated by backend load forecaster" accent="#1863dc" />
              <AgentDecisionCard name="AlertDispatcherAgent" statusChip={agent.should_alert ? 'ALERT SENT' : 'STANDBY'} chipClass={agent.should_alert ? 'chip-coral' : 'chip-muted'} metricLine={agent.alert_message || 'No alerts triggered'} footerLine="Dispatcher output from agent pipeline" accent={agent.should_alert ? '#ff7759' : '#93939f'} />
            </div>
          </div>

          <div className="card-stone" style={{ padding: '28px 28px' }}>
            <div style={{ marginBottom: 18 }}>
              <div className="font-grotesk" style={{ fontSize: 18, color: 'var(--eliyonix-ink)', letterSpacing: '-0.3px', marginBottom: 6 }}>Recommendations</div>
              <div style={{ fontSize: 13.5, color: 'var(--eliyonix-muted)' }}>AI-powered insights generated from backend state</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
              {['solar', 'fault', 'forecast', 'alerts', 'sensor', 'agents'].map(component => (
                <RecommendationCard
                  key={component}
                  component={component}
                  componentLabel={component.toUpperCase()}
                  icon=""
                  timestamp={recommendations[component]?.timestamp || ''}
                  text={recommendations[component]?.text || 'Waiting for recommendation agent output'}
                  confidence={recommendations[component]?.confidence || 0}
                  status={recommendations[component]?.status || 'WAITING'}
                  retrievedCount={recommendations[component]?.retrieved_count || 0}
                />
              ))}
            </div>
          </div>

          <div style={{ background: 'var(--eliyonix-pale-blue)', borderRadius: 16, padding: '28px 28px' }}>
            <div style={{ marginBottom: 20 }}>
              <div className="mono-label" style={{ color: 'var(--eliyonix-coral)', marginBottom: 8 }}>DISCOM Grid View</div>
              <div className="font-grotesk" style={{ fontSize: 20, color: 'var(--eliyonix-ink)', letterSpacing: '-0.3px' }}>MQTT-Published Site Visibility</div>
            </div>

            <div style={{ background: '#fff', borderRadius: 10, border: '1px solid var(--eliyonix-hairline)', overflow: 'hidden' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr 120px 120px 130px 1fr', padding: '10px 18px', borderBottom: '1px solid var(--eliyonix-hairline)', background: 'var(--eliyonix-stone)' }}>
                {['Village ID','Inverter','Solar Output','Fault Score','Status','Last Alert'].map(h => (
                  <span key={h} className="mono-label" style={{ fontSize: 9.5, color: 'var(--eliyonix-muted)' }}>{h}</span>
                ))}
              </div>

              {tableRows.map((site, i) => {
                const siteSensor = site.sensor_data || {}
                const siteAgent = site.agent_result || {}
                const siteFault = Boolean(siteAgent.fault_detected)
                return (
                  <div key={`${siteSensor.village_id}-${siteSensor.inverter_id}-${i}`} className="table-row" style={{ display: 'grid', gridTemplateColumns: '120px 1fr 120px 120px 130px 1fr', padding: '13px 18px', borderBottom: i < tableRows.length - 1 ? '1px solid var(--eliyonix-hairline)' : 'none', alignItems: 'center' }}>
                    <span className="font-mono-e" style={{ fontSize: 12, color: 'var(--eliyonix-ink)', fontWeight: 600 }}>{siteSensor.village_id || '--'}</span>
                    <span style={{ fontSize: 13.5, color: 'var(--eliyonix-ink)' }}>{siteSensor.inverter_id || '--'}</span>
                    <span style={{ fontSize: 13.5, color: 'var(--eliyonix-ink)' }}>{formatNumber(site.derived?.power_kw ?? siteSensor.power_kw, 2)} kW</span>
                    <span className="font-mono-e" style={{ fontSize: 12, color: siteFault ? '#ff7759' : 'var(--eliyonix-ink)' }}>{formatNumber(siteAgent.anomaly_score || 0, 2)}</span>
                    <span className={`chip ${siteFault ? 'chip-coral' : 'chip-green'}`}>{siteFault ? 'FAULT' : 'HEALTHY'}</span>
                    <span style={{ fontSize: 13, color: siteAgent.alert_message ? 'var(--eliyonix-ink)' : 'var(--eliyonix-muted)' }}>{siteAgent.alert_message || 'None'}</span>
                  </div>
                )
              })}

              {!tableRows.length && (
                <div style={{ padding: '18px', color: 'var(--eliyonix-muted)', fontSize: 13 }}>No MQTT site data published yet.</div>
              )}
            </div>

            <div style={{ marginTop: 14, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
              <span style={{ fontSize: 12.5, color: 'var(--eliyonix-muted)' }}>Showing {tableRows.length} MQTT-published installations</span>
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
