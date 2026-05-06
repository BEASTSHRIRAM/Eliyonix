import { useState } from 'react'
import { X, Lightbulb, Loader, CheckCircle, AlertCircle, Info } from 'lucide-react'

/**
 * RecommendationModal Component
 * Shows AI recommendations with 3 simple action points for farmers
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

  const priorityConfig = {
    'high': { 
      icon: AlertCircle, 
      color: '#ff7759', 
      bgLight: '#ffe8e3',
      label: 'High Priority'
    },
    'medium': { 
      icon: Info, 
      color: '#f5a623', 
      bgLight: '#fff5e6',
      label: 'Medium Priority'
    },
    'low': { 
      icon: CheckCircle, 
      color: '#00b464', 
      bgLight: '#e6f9f0',
      label: 'Low Priority'
    }
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0,0,0,0.5)',
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#ffffff',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '600px',
          maxHeight: '85vh',
          overflow: 'auto',
          boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
          animation: 'slideUp 0.3s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{
          padding: '24px',
          borderBottom: '1px solid #e5e5e9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <span style={{ fontSize: '28px' }}>{icon}</span>
              <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#2a2a2f', margin: 0 }}>
                {componentLabel}
              </h2>
            </div>
            <div style={{ fontSize: '13px', color: '#7e7e8f', marginLeft: '40px' }}>
              AI-powered recommendations for your solar system
            </div>
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
              <div>Analyzing 7 days of data...</div>
            </div>
          ) : recommendation && recommendation.recommendations ? (
            <>
              {/* Analysis Summary */}
              {recommendation.analysis && (
                <div style={{
                  background: '#f8f8fa',
                  borderRadius: '12px',
                  padding: '16px',
                  marginBottom: '24px'
                }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: '#7e7e8f', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    📊 System Analysis ({recommendation.analysis_period || '7 days'})
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: '#7e7e8f', marginBottom: '4px' }}>Data Points</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: '#2a2a2f' }}>
                        {recommendation.data_points_analyzed || 0}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#7e7e8f', marginBottom: '4px' }}>Fault Rate</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: recommendation.analysis.fault_rate > 0.1 ? '#ff7759' : '#00b464' }}>
                        {(recommendation.analysis.fault_rate * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: '#7e7e8f', marginBottom: '4px' }}>Efficiency</div>
                      <div style={{ fontSize: '18px', fontWeight: 700, color: recommendation.analysis.efficiency_score > 80 ? '#00b464' : '#f5a623' }}>
                        {recommendation.analysis.efficiency_score?.toFixed(1) || 0}%
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Top 3 Recommendations */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '14px', fontWeight: 600, color: '#2a2a2f', marginBottom: '16px' }}>
                  ✨ Top 3 Actions for You
                </div>

                {recommendation.recommendations.slice(0, 3).map((rec, index) => {
                  const config = priorityConfig[rec.priority] || priorityConfig['medium']
                  const Icon = config.icon

                  return (
                    <div
                      key={index}
                      style={{
                        border: `2px solid ${config.color}`,
                        borderRadius: '12px',
                        padding: '16px',
                        marginBottom: '12px',
                        background: '#ffffff'
                      }}
                    >
                      {/* Priority Badge */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        marginBottom: '12px'
                      }}>
                        <div style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '6px',
                          background: config.bgLight,
                          color: config.color,
                          padding: '4px 10px',
                          borderRadius: '6px',
                          fontSize: '11px',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          letterSpacing: '0.3px'
                        }}>
                          <Icon size={12} />
                          {config.label}
                        </div>
                        <div style={{
                          fontSize: '12px',
                          fontWeight: 600,
                          color: config.color
                        }}>
                          {Math.round(rec.confidence * 100)}% confident
                        </div>
                      </div>

                      {/* Title */}
                      <div style={{
                        fontSize: '15px',
                        fontWeight: 700,
                        color: '#2a2a2f',
                        marginBottom: '8px'
                      }}>
                        {index + 1}. {rec.title}
                      </div>

                      {/* Description */}
                      <div style={{
                        fontSize: '13px',
                        lineHeight: 1.5,
                        color: '#5a5a66',
                        marginBottom: '12px'
                      }}>
                        {rec.description}
                      </div>

                      {/* Action */}
                      <div style={{
                        background: config.bgLight,
                        borderRadius: '8px',
                        padding: '12px',
                        borderLeft: `3px solid ${config.color}`
                      }}>
                        <div style={{ fontSize: '11px', fontWeight: 600, color: '#7e7e8f', marginBottom: '4px', textTransform: 'uppercase' }}>
                          What to do:
                        </div>
                        <div style={{
                          fontSize: '13px',
                          fontWeight: 600,
                          color: '#2a2a2f',
                          lineHeight: 1.4
                        }}>
                          {rec.action}
                        </div>
                      </div>

                      {/* Impact */}
                      {rec.impact && (
                        <div style={{
                          fontSize: '12px',
                          color: '#7e7e8f',
                          marginTop: '8px',
                          fontStyle: 'italic'
                        }}>
                          💡 Impact: {rec.impact}
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>

              {/* Footer */}
              <div style={{
                paddingTop: '16px',
                borderTop: '1px solid #f0f0f2',
                fontSize: '12px',
                color: '#7e7e8f',
                textAlign: 'center'
              }}>
                Generated at {new Date(recommendation.generated_at).toLocaleString('en-GB', { hour12: false })}
              </div>
            </>
          ) : recommendation && recommendation.error ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '200px',
              color: '#ff7759',
              fontSize: '14px',
              textAlign: 'center',
              gap: '12px'
            }}>
              <AlertCircle size={48} />
              <div>{recommendation.error}</div>
            </div>
          ) : (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              minHeight: '200px',
              color: '#93939f',
              fontSize: '14px'
            }}>
              No recommendations available
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
