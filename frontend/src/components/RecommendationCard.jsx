import { useState } from 'react'
import { ChevronDown, AlertCircle, CheckCircle, AlertTriangle } from 'lucide-react'

/**
 * RecommendationCard Component
 * Displays a single recommendation for a dashboard component
 * Shows: component name, timestamp, recommendation text, confidence, status
 * Expandable to show full reasoning and retrieved context
 */
export default function RecommendationCard({
  component = 'solar',
  componentLabel = 'Solar Output',
  icon = '🌞',
  timestamp = new Date().toISOString(),
  text = 'No recommendation available',
  confidence = 0.75,
  status = 'MONITOR',
  retrievedCount = 0,
  retrievedEvents = []
}) {
  const [isExpanded, setIsExpanded] = useState(false)

  // Status badge styling
  const statusConfig = {
    'ACTION_REQUIRED': {
      bg: '#ff7759',
      text: 'Action Required',
      icon: AlertCircle,
      bgLight: '#ffe8e3'
    },
    'MONITOR': {
      bg: '#f5a623',
      text: 'Monitor',
      icon: AlertTriangle,
      bgLight: '#fff5e6'
    },
    'OPTIMAL': {
      bg: '#00b464',
      text: 'Optimal',
      icon: CheckCircle,
      bgLight: '#e6f9f0'
    },
    'ERROR': {
      bg: '#93939f',
      text: 'Error',
      icon: AlertCircle,
      bgLight: '#f0f0f2'
    }
  }

  const statusInfo = statusConfig[status] || statusConfig['MONITOR']
  const StatusIcon = statusInfo.icon

  // Format timestamp
  const formatTime = (isoString) => {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`

    const timeStr = date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
    return `${timeStr}`
  }

  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid #e5e5e9',
        borderRadius: '12px',
        padding: '16px',
        marginBottom: '12px',
        transition: 'all 0.2s ease',
        cursor: 'pointer',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)'
        e.currentTarget.style.borderColor = '#d0d0d5'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none'
        e.currentTarget.style.borderColor = '#e5e5e9'
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1 }}>
          <span style={{ fontSize: '20px' }}>{icon}</span>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#2a2a2f', marginBottom: '2px' }}>
              {componentLabel}
            </div>
            <div style={{ fontSize: '11px', color: '#93939f', letterSpacing: '0.3px' }}>
              {formatTime(timestamp)} · {timestamp}
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div
            style={{
              background: statusInfo.bgLight,
              color: statusInfo.bg,
              padding: '4px 10px',
              borderRadius: '6px',
              fontSize: '10px',
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              textTransform: 'uppercase',
              letterSpacing: '0.4px'
            }}
          >
            <StatusIcon size={12} />
            {statusInfo.text}
          </div>
        </div>
      </div>

      {/* Recommendation Text */}
      <div style={{ marginBottom: '12px' }}>
        <p style={{
          fontSize: '13px',
          lineHeight: 1.5,
          color: '#2a2a2f',
          margin: 0,
          marginBottom: '8px'
        }}>
          {text}
        </p>

        {/* Confidence Score */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ fontSize: '10px', color: '#93939f', fontWeight: 500 }}>
            Confidence:
          </div>
          <div style={{
            width: '80px',
            height: '4px',
            background: '#e5e5e9',
            borderRadius: '2px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${Math.round(confidence * 100)}%`,
              height: '100%',
              background: confidence > 0.8 ? '#00b464' : confidence > 0.6 ? '#f5a623' : '#ff7759',
              transition: 'width 0.3s ease'
            }} />
          </div>
          <div style={{ fontSize: '11px', fontWeight: 600, color: '#2a2a2f' }}>
            {Math.round(confidence * 100)}%
          </div>
        </div>
      </div>

      {/* Retrieved Events Reference */}
      {retrievedCount > 0 && (
        <div style={{
          fontSize: '11px',
          color: '#7e7e8f',
          paddingTop: '8px',
          borderTop: '1px solid #f0f0f2',
          marginBottom: '12px'
        }}>
          Based on {retrievedCount} similar past event{retrievedCount !== 1 ? 's' : ''}
        </div>
      )}

      {/* Expand Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          background: 'none',
          border: 'none',
          color: '#7e7e8f',
          cursor: 'pointer',
          fontSize: '11px',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          padding: 0,
          transition: 'color 0.2s ease'
        }}
        onMouseEnter={(e) => e.target.style.color = '#2a2a2f'}
        onMouseLeave={(e) => e.target.style.color = '#7e7e8f'}
      >
        <ChevronDown size={14} style={{
          transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
          transition: 'transform 0.2s ease'
        }} />
        {isExpanded ? 'Hide' : 'Show'} Details
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div style={{
          marginTop: '12px',
          paddingTop: '12px',
          borderTop: '1px solid #f0f0f2'
        }}>
          <div style={{
            background: '#f8f8fa',
            borderRadius: '8px',
            padding: '10px',
            marginBottom: '10px'
          }}>
            <div style={{ fontSize: '10px', fontWeight: 600, color: '#93939f', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
              Full Reasoning
            </div>
            <div style={{ fontSize: '12px', lineHeight: 1.6, color: '#2a2a2f' }}>
              {text}
            </div>
          </div>

          {retrievedEvents && retrievedEvents.length > 0 && (
            <div>
              <div style={{ fontSize: '10px', fontWeight: 600, color: '#93939f', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>
                Retrieved Context
              </div>
              {retrievedEvents.map((event, idx) => (
                <div
                  key={idx}
                  style={{
                    background: '#f8f8fa',
                    borderRadius: '6px',
                    padding: '8px',
                    marginBottom: '6px',
                    fontSize: '11px',
                    lineHeight: 1.5,
                    color: '#2a2a2f'
                  }}
                >
                  <div style={{ fontWeight: 600, marginBottom: '3px' }}>
                    {event.timestamp}
                  </div>
                  <div style={{ color: '#7e7e8f' }}>
                    {event.text}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
