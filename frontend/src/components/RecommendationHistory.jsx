import { useState, useEffect } from 'react'
import { X, Filter, Clock, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'

/**
 * RecommendationHistory Component
 * Displays a timeline/drawer of recommendation history
 * Can filter by component or status
 * Shows when recommendations were generated and which components they affected
 */
export default function RecommendationHistory({ isOpen = false, onClose = () => {} }) {
  const [history, setHistory] = useState([])
  const [selectedComponent, setSelectedComponent] = useState(null)
  const [selectedStatus, setSelectedStatus] = useState(null)
  const [loading, setLoading] = useState(false)

  const components = ['solar', 'fault', 'forecast', 'alerts', 'sensor', 'agents']
  const componentLabels = {
    'solar': '🌞 Solar Output',
    'fault': '⚠️ Fault Score',
    'forecast': '📈 Load Forecast',
    'alerts': '🔔 Active Alerts',
    'sensor': '📡 Live Sensor Feed',
    'agents': '🤖 Agent Decisions'
  }

  // Fetch history on mount
  useEffect(() => {
    if (isOpen) {
      fetchHistory()
    }
  }, [isOpen, selectedComponent, selectedStatus])

  const fetchHistory = async () => {
    setLoading(true)
    try {
      let url = '/recommendations/history?limit=100'
      if (selectedComponent) {
        url += `&component=${selectedComponent}`
      }
      const response = await fetch(url)
      const data = await response.json()
      setHistory(data.history || [])
    } catch (error) {
      console.error('Error fetching recommendation history:', error)
    } finally {
      setLoading(false)
    }
  }

  // Filter history
  const filteredHistory = history.filter(item => {
    if (selectedStatus && item.status !== selectedStatus) return false
    return true
  })

  const statusConfig = {
    'ACTION_REQUIRED': {
      icon: AlertCircle,
      bg: '#ff7759',
      label: 'Action Required'
    },
    'MONITOR': {
      icon: AlertTriangle,
      bg: '#f5a623',
      label: 'Monitor'
    },
    'OPTIMAL': {
      icon: CheckCircle,
      bg: '#00b464',
      label: 'Optimal'
    }
  }

  if (!isOpen) return null

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.5)',
        zIndex: 40,
        display: 'flex',
        justifyContent: 'flex-end'
      }}
      onClick={onClose}
    >
      {/* Drawer */}
      <div
        style={{
          background: '#ffffff',
          width: '100%',
          maxWidth: '420px',
          height: '100vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '-4px 0 12px rgba(0,0,0,0.15)',
          animation: 'slideIn 0.3s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #e5e5e9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{
            fontSize: '16px',
            fontWeight: 700,
            color: '#2a2a2f',
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <Clock size={18} />
            Recommendation History
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: '#7e7e8f',
              padding: '4px'
            }}
            onMouseEnter={(e) => e.target.style.color = '#2a2a2f'}
            onMouseLeave={(e) => e.target.style.color = '#7e7e8f'}
          >
            <X size={20} />
          </button>
        </div>

        {/* Filters */}
        <div style={{
          padding: '12px 20px',
          borderBottom: '1px solid #f0f0f2',
          background: '#f8f8fa'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', fontSize: '11px', color: '#7e7e8f', fontWeight: 600 }}>
            <Filter size={14} />
            FILTERS
          </div>

          {/* Component Filter */}
          <div style={{ marginBottom: '10px' }}>
            <div style={{ fontSize: '10px', color: '#93939f', marginBottom: '6px', fontWeight: 500 }}>Component:</div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <button
                onClick={() => setSelectedComponent(null)}
                style={{
                  padding: '4px 10px',
                  borderRadius: '6px',
                  border: selectedComponent === null ? '1px solid #7e7e8f' : '1px solid #e5e5e9',
                  background: selectedComponent === null ? '#2a2a2f' : 'transparent',
                  color: selectedComponent === null ? 'white' : '#7e7e8f',
                  fontSize: '10px',
                  cursor: 'pointer',
                  fontWeight: 500
                }}
              >
                All
              </button>
              {components.map(comp => (
                <button
                  key={comp}
                  onClick={() => setSelectedComponent(comp)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: selectedComponent === comp ? '1px solid #7e7e8f' : '1px solid #e5e5e9',
                    background: selectedComponent === comp ? '#2a2a2f' : 'transparent',
                    color: selectedComponent === comp ? 'white' : '#7e7e8f',
                    fontSize: '10px',
                    cursor: 'pointer',
                    fontWeight: 500
                  }}
                >
                  {comp.substring(0, 3).toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <div style={{ fontSize: '10px', color: '#93939f', marginBottom: '6px', fontWeight: 500 }}>Status:</div>
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {['ACTION_REQUIRED', 'MONITOR', 'OPTIMAL'].map(s => (
                <button
                  key={s}
                  onClick={() => setSelectedStatus(selectedStatus === s ? null : s)}
                  style={{
                    padding: '4px 10px',
                    borderRadius: '6px',
                    border: selectedStatus === s ? `1px solid ${statusConfig[s].bg}` : '1px solid #e5e5e9',
                    background: selectedStatus === s ? statusConfig[s].bg : 'transparent',
                    color: selectedStatus === s ? 'white' : '#7e7e8f',
                    fontSize: '10px',
                    cursor: 'pointer',
                    fontWeight: 500
                  }}
                >
                  {statusConfig[s].label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* History List */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 0'
        }}>
          {loading ? (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100px',
              color: '#93939f',
              fontSize: '13px'
            }}>
              Loading history...
            </div>
          ) : filteredHistory.length === 0 ? (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100px',
              color: '#93939f',
              fontSize: '13px'
            }}>
              No recommendations found
            </div>
          ) : (
            filteredHistory.map((item, idx) => {
              const StatusIcon = statusConfig[item.status]?.icon || AlertTriangle
              const statusBg = statusConfig[item.status]?.bg || '#f5a623'

              return (
                <div
                  key={idx}
                  style={{
                    padding: '12px 16px',
                    borderBottom: '1px solid #f0f0f2',
                    cursor: 'pointer',
                    transition: 'background 0.2s ease'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f8f8fa'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  {/* Time + Status */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <div style={{ fontSize: '11px', color: '#7e7e8f', fontWeight: 500 }}>
                      {new Date(item.timestamp).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      background: statusBg,
                      color: 'white',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '9px',
                      fontWeight: 600
                    }}>
                      <StatusIcon size={10} />
                      {statusConfig[item.status]?.label || 'Unknown'}
                    </div>
                  </div>

                  {/* Component + Text */}
                  <div style={{ marginBottom: '6px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#2a2a2f', marginBottom: '3px' }}>
                      {componentLabels[item.component] || item.component}
                    </div>
                    <div style={{ fontSize: '12px', lineHeight: 1.4, color: '#7e7e8f' }}>
                      {item.text.substring(0, 120)}{item.text.length > 120 ? '...' : ''}
                    </div>
                  </div>

                  {/* Confidence + Retrieved Count */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '10px', color: '#93939f' }}>
                    <div>Confidence: {Math.round(item.confidence * 100)}%</div>
                    {item.retrieved_events && item.retrieved_events.length > 0 && (
                      <div>{item.retrieved_events.length} similar event{item.retrieved_events.length !== 1 ? 's' : ''}</div>
                    )}
                  </div>
                </div>
              )
            })
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '12px 16px',
          borderTop: '1px solid #e5e5e9',
          fontSize: '11px',
          color: '#93939f',
          textAlign: 'center'
        }}>
          Showing {filteredHistory.length} of {history.length} recommendations
        </div>
      </div>

      <style>{`
        @keyframes slideIn {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
      `}</style>
    </div>
  )
}
