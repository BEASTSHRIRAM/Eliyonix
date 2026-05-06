import { useState } from 'react'
import { X, Lightbulb, Loader } from 'lucide-react'

/**
 * RecommendationModal Component
 * Shows a recommendation for a single component in a modal
 */
export default function RecommendationModal({
  isOpen = false,
  onClose = () => {},
  component = '',
  componentLabel = '',
  icon = '💡',
  loading = false,
  recommendation = null
}) {
  if (!isOpen) return null

  const statusConfig = {
    'ACTION_REQUIRED': { bg: '#ff7759', bgLight: '#ffe8e3' },
    'MONITOR': { bg: '#f5a623', bgLight: '#fff5e6' },
    'OPTIMAL': { bg: '#00b464', bgLight: '#e6f9f0' },
    'ERROR': { bg: '#93939f', bgLight: '#f0f0f2' }
  }

  const statusInfo = statusConfig[recommendation?.status] || statusConfig['MONITOR']

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.5)',
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#ffffff',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '480px',
          maxHeight: '80vh',
          overflow: 'auto',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          animation: 'slideUp 0.3s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid #e5e5e9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '24px' }}>{icon}</span>
            <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#2a2a2f', margin: 0 }}>
              {componentLabel}
            </h2>
          </div>
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

        {/* Content */}
        <div style={{ padding: '24px' }}>
          {loading ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '12px',
              minHeight: '200px',
              color: '#93939f'
            }}>
              <Loader size={32} style={{ animation: 'spin 1s linear infinite' }} />
              <div>Generating recommendation...</div>
            </div>
          ) : recommendation ? (
            <>
              {/* Status Badge */}
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                background: statusInfo.bgLight,
                color: statusInfo.bg,
                padding: '6px 12px',
                borderRadius: '8px',
                fontSize: '11px',
                fontWeight: 600,
                marginBottom: '16px',
                textTransform: 'uppercase',
                letterSpacing: '0.3px'
              }}>
                <Lightbulb size={12} />
                {recommendation.status}
              </div>

              {/* Timestamp */}
              <div style={{
                fontSize: '11px',
                color: '#93939f',
                marginBottom: '16px',
                fontWeight: 500
              }}>
                Generated: {new Date(recommendation.timestamp).toLocaleString('en-GB', { hour12: false })}
              </div>

              {/* Recommendation Text */}
              <div style={{ marginBottom: '16px' }}>
                <p style={{
                  fontSize: '14px',
                  lineHeight: 1.6,
                  color: '#2a2a2f',
                  margin: 0
                }}>
                  {recommendation.text}
                </p>
              </div>

              {/* Confidence Bar */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '8px'
                }}>
                  <label style={{ fontSize: '12px', fontWeight: 600, color: '#2a2a2f' }}>
                    Confidence
                  </label>
                  <span style={{ fontSize: '14px', fontWeight: 700, color: statusInfo.bg }}>
                    {Math.round(recommendation.confidence * 100)}%
                  </span>
                </div>
                <div style={{
                  width: '100%',
                  height: '6px',
                  background: '#e5e5e9',
                  borderRadius: '3px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${Math.round(recommendation.confidence * 100)}%`,
                    height: '100%',
                    background: statusInfo.bg,
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>

              {/* Retrieved Events */}
              {recommendation.retrieved_count > 0 && (
                <div style={{
                  paddingTop: '16px',
                  borderTop: '1px solid #f0f0f2',
                  fontSize: '12px',
                  color: '#7e7e8f'
                }}>
                  Based on <strong>{recommendation.retrieved_count}</strong> similar past event{recommendation.retrieved_count !== 1 ? 's' : ''}
                </div>
              )}
            </>
          ) : (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '200px',
              color: '#93939f',
              fontSize: '14px'
            }}>
              No recommendation available
            </div>
          )}
        </div>

        <style>{`
          @keyframes slideUp {
            from {
              transform: translateY(20px);
              opacity: 0;
            }
            to {
              transform: translateY(0);
              opacity: 1;
            }
          }
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    </div>
  )
}
