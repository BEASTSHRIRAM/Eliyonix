import { useState, useEffect } from 'react'
import { useLocation, Link } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import RecommendationCard from '../components/RecommendationCard'
import { ChevronLeft, RefreshCw, Zap } from 'lucide-react'

/**
 * Recommendations Page
 * Full-page view of all recommendations from RecommendationAgent
 * Shows detailed insights for each component with charts and history
 */
export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState({})
  const [vectorStoreStats, setVectorStoreStats] = useState(null)
  const [schedulerStatus, setSchedulerStatus] = useState(null)
  const [loading, setLoading] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(new Date())

  const components = [
    { key: 'solar', label: '🌞 Solar Output', icon: '🌞' },
    { key: 'fault', label: '⚠️ Fault Score', icon: '⚠️' },
    { key: 'forecast', label: '📈 Load Forecast', icon: '📈' },
    { key: 'alerts', label: '🔔 Active Alerts', icon: '🔔' },
    { key: 'sensor', label: '📡 Live Sensor Feed', icon: '📡' },
    { key: 'agents', label: '🤖 Agent Decisions', icon: '🤖' },
  ]

  useEffect(() => {
    fetchRecommendations()
    const interval = setInterval(fetchRecommendations, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [])

  const fetchRecommendations = async () => {
    setLoading(true)
    try {
      const response = await fetch('/recommendations')
      const data = await response.json()
      setRecommendations(data.recommendations || {})
      setVectorStoreStats(data.vector_store_stats || {})
      setSchedulerStatus(data.scheduler_status || {})
      setLastUpdated(new Date())
    } catch (error) {
      console.error('Error fetching recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  const triggerManualRun = async () => {
    try {
      await fetch('/recommendations/trigger', { method: 'POST' })
      // Fetch updated recommendations after a short delay
      setTimeout(fetchRecommendations, 2000)
    } catch (error) {
      console.error('Error triggering recommendations:', error)
    }
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f8f8f8' }}>
      <Sidebar />

      <main className="main-with-sidebar" style={{ marginLeft: 230, flex: 1, padding: '0 0 48px' }}>
        {/* Header */}
        <div style={{
          background: '#fff',
          borderBottom: '1px solid var(--eliyonix-hairline)',
          padding: '0 32px',
          height: 62,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 40,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Link to="/dashboard" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: '#7e7e8f' }}>
              <ChevronLeft size={18} />
            </Link>
            <h1 className="font-grotesk" style={{ fontSize: 22, fontWeight: 500, letterSpacing: '-0.4px', color: 'var(--eliyonix-ink)', margin: 0 }}>
              Recommendations Engine
            </h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '12px', color: '#93939f' }}>
              Updated: {lastUpdated.toLocaleTimeString('en-GB', { hour12: false })}
            </span>
            <button
              onClick={fetchRecommendations}
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                border: '1px solid var(--eliyonix-hairline)',
                borderRadius: '8px',
                background: '#fff',
                cursor: 'pointer',
                fontSize: '13px',
                color: 'var(--eliyonix-ink)',
                transition: 'all 0.2s ease',
                opacity: loading ? 0.6 : 1,
              }}
              onMouseEnter={(e) => !loading && (e.currentTarget.style.background = '#f8f8fa')}
              onMouseLeave={(e) => e.currentTarget.style.background = '#fff'}
            >
              <RefreshCw size={14} style={{ transform: loading ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }} />
              Refresh
            </button>
            <button
              onClick={triggerManualRun}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '8px 16px',
                border: 'none',
                borderRadius: '8px',
                background: '#2a2a2f',
                cursor: 'pointer',
                fontSize: '13px',
                color: '#fff',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#1a1a1f'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#2a2a2f'}
            >
              <Zap size={14} />
              Run Now
            </button>
          </div>
        </div>

        <div style={{ padding: '28px 32px' }}>
          {/* Scheduler Info */}
          {schedulerStatus && (
            <div style={{
              background: '#f8f8fa',
              borderRadius: '12px',
              padding: '16px',
              marginBottom: '24px',
              border: '1px solid #e5e5e9'
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#93939f', textTransform: 'uppercase', fontWeight: 600, marginBottom: '4px' }}>
                    Scheduler Status
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: schedulerStatus.is_running ? '#00b464' : '#ff7759' }}>
                    {schedulerStatus.is_running ? 'RUNNING' : 'STOPPED'}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#93939f', textTransform: 'uppercase', fontWeight: 600, marginBottom: '4px' }}>
                    Interval
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#2a2a2f' }}>
                    {schedulerStatus.interval_minutes} minutes
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#93939f', textTransform: 'uppercase', fontWeight: 600, marginBottom: '4px' }}>
                    Time Until Next
                  </div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#2a2a2f' }}>
                    {schedulerStatus.time_until_next_minutes ?? 'N/A'} minutes
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: '#93939f', textTransform: 'uppercase', fontWeight: 600, marginBottom: '4px' }}>
                    Last Run
                  </div>
                  <div style={{ fontSize: '12px', color: '#7e7e8f' }}>
                    {schedulerStatus.last_run ? new Date(schedulerStatus.last_run).toLocaleTimeString('en-GB', { hour12: false }) : 'Never'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Vector Store Stats */}
          {vectorStoreStats && (
            <div style={{
              background: '#f8f8fa',
              borderRadius: '12px',
              padding: '16px',
              marginBottom: '24px',
              border: '1px solid #e5e5e9'
            }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#2a2a2f', marginBottom: '12px' }}>
                Vector Store Statistics
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: '#93939f', marginBottom: '4px' }}>Total Documents</div>
                  <div style={{ fontSize: '18px', fontWeight: 700, color: '#2a2a2f' }}>
                    {vectorStoreStats.total_documents || 0}
                  </div>
                </div>
                {Object.entries(vectorStoreStats.documents_by_component || {}).map(([component, count]) => (
                  <div key={component}>
                    <div style={{ fontSize: '11px', color: '#93939f', marginBottom: '4px', textTransform: 'capitalize' }}>
                      {component}
                    </div>
                    <div style={{ fontSize: '18px', fontWeight: 700, color: '#2a2a2f' }}>
                      {count}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations Grid */}
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 600, color: '#2a2a2f', marginBottom: '16px' }}>
              Latest Recommendations
            </h2>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
              gap: '16px'
            }}>
              {components.map(({ key, label, icon }) => (
                <RecommendationCard
                  key={key}
                  component={key}
                  componentLabel={label}
                  icon={icon}
                  timestamp={recommendations[key]?.timestamp || new Date().toISOString()}
                  text={recommendations[key]?.text || `Generating ${key} recommendation...`}
                  confidence={recommendations[key]?.confidence || 0.75}
                  status={recommendations[key]?.status || 'MONITOR'}
                  retrievedCount={recommendations[key]?.retrieved_count || 0}
                />
              ))}
            </div>
          </div>

          {/* Documentation */}
          <div style={{
            background: '#f8f8fa',
            borderRadius: '12px',
            padding: '20px',
            marginTop: '28px',
            border: '1px solid #e5e5e9'
          }}>
            <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#2a2a2f', marginTop: 0 }}>
              About RecommendationAgent
            </h3>
            <p style={{ fontSize: '13px', lineHeight: 1.6, color: '#7e7e8f', margin: '8px 0' }}>
              The RecommendationAgent uses Retrieval-Augmented Generation (RAG) with a vector database to provide AI-powered insights for each dashboard component.
            </p>
            <ul style={{ fontSize: '13px', lineHeight: 1.8, color: '#7e7e8f', paddingLeft: '20px' }}>
              <li><strong>Runs automatically every 60 minutes</strong> or on-demand via "Run Now" button</li>
              <li><strong>Stores 7 days of history</strong> in the vector database</li>
              <li><strong>Retrieves similar past events</strong> using embedding similarity</li>
              <li><strong>Generates recommendations</strong> using Claude via AWS Bedrock</li>
              <li><strong>Provides confidence scores</strong> for each recommendation</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
}
