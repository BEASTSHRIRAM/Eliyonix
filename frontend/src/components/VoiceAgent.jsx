import { useState, useRef, useEffect } from 'react'
import { Mic, Square, Volume2, Loader } from 'lucide-react'

const LANGUAGES = {
  kannada: { name: 'ಕನ್ನಡ', code: 'kn' },
  hindi: { name: 'हिंदी', code: 'hi' },
  english: { name: 'English', code: 'en' },
  tamil: { name: 'தமிழ்', code: 'ta' },
  telugu: { name: 'తెలుగు', code: 'te' },
}

export default function VoiceAgent({ villageId, onClose }) {
  const [isListening, setIsListening] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [language, setLanguage] = useState('kannada')
  const [transcript, setTranscript] = useState('')
  const [response, setResponse] = useState('')
  const [history, setHistory] = useState([])
  const recognitionRef = useRef(null)
  const synthRef = useRef(null)

  // Initialize Speech Recognition
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition()
      recognitionRef.current.continuous = false
      recognitionRef.current.interimResults = true
      recognitionRef.current.lang = `${LANGUAGES[language].code}-IN`

      recognitionRef.current.onstart = () => {
        setIsListening(true)
        setTranscript('')
      }

      recognitionRef.current.onresult = (event) => {
        let interimTranscript = ''
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript
          if (event.results[i].isFinal) {
            setTranscript(transcript)
          } else {
            interimTranscript += transcript
          }
        }
      }

      recognitionRef.current.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error)
        setIsListening(false)
      }
    }

    synthRef.current = window.speechSynthesis
  }, [language])

  const startListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.lang = `${LANGUAGES[language].code}-IN`
      recognitionRef.current.start()
    }
  }

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
  }

  const handleSubmit = async () => {
    if (!transcript.trim()) return

    setIsProcessing(true)
    try {
      const response = await fetch('/api/voice-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          village_id: villageId,
          query: transcript,
          language: LANGUAGES[language].code,
        }),
      })

      const data = await response.json()
      const agentResponse = data.response || 'Unable to process your request'

      setResponse(agentResponse)
      setHistory([
        ...history,
        { user: transcript, agent: agentResponse, timestamp: new Date() },
      ])
      setTranscript('')

      // Speak the response
      if (synthRef.current) {
        const utterance = new SpeechSynthesisUtterance(agentResponse)
        utterance.lang = `${LANGUAGES[language].code}-IN`
        utterance.rate = 0.95
        synthRef.current.speak(utterance)
      }
    } catch (error) {
      console.error('Error:', error)
      setResponse('Sorry, I encountered an error. Please try again.')
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: 0,
      right: 0,
      width: '100%',
      maxWidth: 480,
      height: '100vh',
      background: 'linear-gradient(135deg, #f5f5f5 0%, #e8f5e9 100%)',
      borderLeft: '1px solid var(--eliyonix-hairline)',
      boxShadow: '-4px 0 20px rgba(0,0,0,0.1)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 999,
    }}>
      {/* Header */}
      <div style={{
        padding: '20px',
        background: '#fff',
        borderBottom: '1px solid var(--eliyonix-hairline)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <div>
          <h3 className="font-grotesk" style={{ fontSize: 18, color: 'var(--eliyonix-ink)', marginBottom: 4 }}>
            Voice Assistant
          </h3>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid var(--eliyonix-hairline)',
              fontSize: 13,
              fontFamily: "'DM Sans', sans-serif",
              cursor: 'pointer',
            }}
          >
            {Object.entries(LANGUAGES).map(([key, val]) => (
              <option key={key} value={key}>{val.name}</option>
            ))}
          </select>
        </div>
        <button onClick={onClose} style={{
          background: 'none',
          border: 'none',
          fontSize: 24,
          cursor: 'pointer',
          color: 'var(--eliyonix-ink)',
        }}>×</button>
      </div>

      {/* Conversation History */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        gap: 16,
      }}>
        {history.length === 0 ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: 'var(--eliyonix-muted)',
            textAlign: 'center',
          }}>
            <div>
              <Mic size={40} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
              <p>Start speaking about productivity or weather</p>
              <p style={{ fontSize: 12, marginTop: 8 }}>e.g., "How can I increase my solar output?" or "What's the weather forecast?"</p>
            </div>
          </div>
        ) : (
          history.map((item, idx) => (
            <div key={idx}>
              {/* User Message */}
              <div style={{
                marginBottom: 12,
                textAlign: 'right',
              }}>
                <div style={{
                  display: 'inline-block',
                  maxWidth: '85%',
                  padding: '12px 16px',
                  background: '#4ade80',
                  color: '#fff',
                  borderRadius: '12px 12px 4px 12px',
                  fontSize: 14,
                  wordWrap: 'break-word',
                }}>
                  {item.user}
                </div>
              </div>

              {/* Agent Message */}
              <div style={{
                marginBottom: 12,
                textAlign: 'left',
              }}>
                <div style={{
                  display: 'inline-block',
                  maxWidth: '85%',
                  padding: '12px 16px',
                  background: '#fff',
                  color: 'var(--eliyonix-ink)',
                  borderRadius: '12px 12px 12px 4px',
                  fontSize: 14,
                  wordWrap: 'break-word',
                  border: '1px solid var(--eliyonix-hairline)',
                }}>
                  {item.agent}
                </div>
              </div>
            </div>
          ))
        )}
        {response && !history.find(h => h.agent === response) && (
          <div style={{ textAlign: 'left' }}>
            <div style={{
              display: 'inline-block',
              maxWidth: '85%',
              padding: '12px 16px',
              background: '#fff',
              color: 'var(--eliyonix-ink)',
              borderRadius: '12px 12px 12px 4px',
              fontSize: 14,
              wordWrap: 'break-word',
              border: '1px solid var(--eliyonix-hairline)',
            }}>
              {response}
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={{
        padding: '16px',
        background: '#fff',
        borderTop: '1px solid var(--eliyonix-hairline)',
      }}>
        {/* Transcript Display */}
        {transcript && (
          <div style={{
            padding: '12px',
            background: 'rgba(74, 222, 128, 0.1)',
            borderRadius: 8,
            marginBottom: 12,
            fontSize: 13,
            color: 'var(--eliyonix-ink)',
            minHeight: 40,
          }}>
            {transcript}
          </div>
        )}

        {/* Controls */}
        <div style={{
          display: 'flex',
          gap: 10,
          justifyContent: 'space-between',
        }}>
          <button
            onClick={isListening ? stopListening : startListening}
            disabled={isProcessing}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: 10,
              border: 'none',
              background: isListening ? '#ff7759' : '#4ade80',
              color: '#fff',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              fontSize: 14,
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              transition: 'opacity 0.2s',
              opacity: isProcessing ? 0.6 : 1,
            }}
          >
            {isListening ? (
              <>
                <Square size={16} /> Stop
              </>
            ) : (
              <>
                <Mic size={16} /> Listen
              </>
            )}
          </button>

          <button
            onClick={handleSubmit}
            disabled={!transcript || isProcessing}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: 10,
              border: 'none',
              background: '#1863dc',
              color: '#fff',
              cursor: transcript && !isProcessing ? 'pointer' : 'not-allowed',
              fontSize: 14,
              fontWeight: 600,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              opacity: transcript && !isProcessing ? 1 : 0.5,
            }}
          >
            {isProcessing ? (
              <>
                <Loader size={16} style={{ animation: 'spin 1s linear infinite' }} /> Processing
              </>
            ) : (
              <>
                <Volume2 size={16} /> Send
              </>
            )}
          </button>
        </div>
      </div>

      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  )
}
