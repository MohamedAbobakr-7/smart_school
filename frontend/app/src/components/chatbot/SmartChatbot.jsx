import { useState, useRef, useEffect } from 'react'
import { apiFetch } from '../../lib/api'
import { useAuthStore } from '../../stores/authStore'

const ROLE_LABELS = {
  ADMIN: 'School Admin Chatbot',
  TEACHER: 'Teacher Chatbot',
  STUDENT: 'Student Chatbot',
  PARENT: 'Parent Chatbot',
}

const ROLE_ICONS = {
  ADMIN: '🏫',
  TEACHER: '📚',
  STUDENT: '🎓',
  PARENT: '👨‍👩‍👧',
}

function TypingDots() {
  return (
    <div style={{ display: 'flex', gap: '4px', padding: '12px 16px', alignItems: 'center' }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: '8px', height: '8px', borderRadius: '50%',
          background: 'var(--ss-primary)',
          animation: 'chatbotPulse 1.2s ease-in-out infinite',
          animationDelay: `${i * 0.2}s`,
          display: 'inline-block',
        }} />
      ))}
    </div>
  )
}

function ChatBubble({ msg }) {
  const isBot = msg.sender === 'bot'
  return (
    <div style={{
      display: 'flex',
      justifyContent: isBot ? 'flex-start' : 'flex-end',
      marginBottom: '0.6rem',
      gap: '8px',
      alignItems: 'flex-end',
    }}>
      {isBot && (
        <div style={{
          width: '28px', height: '28px', borderRadius: '50%',
          background: 'var(--ss-auth-brand-gradient)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '14px', flexShrink: 0,
        }}>🤖</div>
      )}
      <div style={{
        maxWidth: '78%',
        padding: '0.6rem 0.9rem',
        borderRadius: isBot ? '4px 16px 16px 16px' : '16px 4px 16px 16px',
        background: isBot
          ? 'var(--ss-bg-hover)'
          : 'var(--ss-auth-brand-gradient)',
        color: isBot ? 'var(--ss-text)' : 'var(--ss-text-on-primary)',
        fontSize: '0.875rem',
        lineHeight: 1.55,
        boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {msg.text}
        {msg.timestamp && (
          <div style={{
            fontSize: '0.68rem',
            marginTop: '4px',
            opacity: 0.6,
            textAlign: 'right',
          }}>
            {msg.timestamp}
          </div>
        )}
      </div>
    </div>
  )
}

export function SmartChatbot() {
  const user = useAuthStore(s => s.user)
  const role = user?.role || 'USER'

  const [isOpen, setIsOpen] = useState(false)
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [messages, setMessages] = useState([])
  const [initialized, setInitialized] = useState(false)
  const bottomRef = useRef(null)
  const inputRef = useRef(null)

  // Fetch greeting + suggestions on first open
  useEffect(() => {
    if (!isOpen || initialized) return
    setInitialized(true)
    ;(async () => {
      try {
        const res = await apiFetch('/chatbot/ask/')
        if (res.ok) {
          const data = await res.json()
          if (data.greeting) {
            setMessages([{ sender: 'bot', text: data.greeting, timestamp: now() }])
          }
          if (data.suggestions) setSuggestions(data.suggestions)
        }
      } catch {
        setMessages([{ sender: 'bot', text: `Hello! I'm your ${ROLE_LABELS[role] || 'Smart School Chatbot'}. How can I help you today?`, timestamp: now() }])
      }
    })()
  }, [isOpen, initialized, role])

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, loading, isOpen])

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  function now() {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  async function sendMessage(text) {
    const trimmed = text.trim()
    if (!trimmed || loading) return
    setInput('')
    setMessages(prev => [...prev, { sender: 'user', text: trimmed, timestamp: now() }])
    setLoading(true)

    try {
      const res = await apiFetch('/chatbot/ask/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed }),
      })
      const data = await res.json()
      if (res.ok) {
        setMessages(prev => [...prev, { sender: 'bot', text: data.reply || 'Sorry, I could not get a response.', timestamp: now() }])
        if (data.suggestions) setSuggestions(data.suggestions)
      } else {
        setMessages(prev => [...prev, { sender: 'bot', text: data.error || 'Something went wrong. Please try again.', timestamp: now() }])
      }
    } catch {
      setMessages(prev => [...prev, { sender: 'bot', text: 'Unable to reach the chatbot. Please check your connection.', timestamp: now() }])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
    }
  }, [input])

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  const icon = ROLE_ICONS[role] || '💬'
  const label = ROLE_LABELS[role] || 'Smart School Chatbot'

  return (
    <>
      {/* Keyframe animation injected once */}
      <style>{`
        @keyframes chatbotPulse {
          0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
          40% { transform: scale(1); opacity: 1; }
        }
        @keyframes chatbotSlideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.95); }
          to { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>

      {/* Floating Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          aria-label="Open Smart School Chatbot"
          style={{
            position: 'fixed', bottom: '1.75rem', right: '1.75rem',
            width: '56px', height: '56px', borderRadius: '50%',
            background: 'var(--ss-auth-brand-gradient)',
            color: 'var(--ss-text-on-primary)', border: 'none',
            boxShadow: 'var(--ss-primary-shadow)',
            cursor: 'pointer', zIndex: 9999,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '1.4rem',
            transition: 'transform 0.2s, box-shadow 0.2s',
          }}
          onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.08)' }}
          onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)' }}
        >
          {icon}
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          style={{
            position: 'fixed', bottom: '1.75rem', right: '1.75rem',
            width: '370px', height: '560px',
            background: 'var(--ss-bg-card)',
            borderRadius: '20px',
            boxShadow: '0 12px 48px rgba(0,0,0,0.18)',
            border: '1px solid var(--ss-border)',
            display: 'flex', flexDirection: 'column',
            zIndex: 9999, overflow: 'hidden',
            animation: 'chatbotSlideUp 0.25s ease',
          }}
        >
          {/* Header */}
          <div style={{
            background: 'var(--ss-auth-brand-gradient)',
            padding: '0.9rem 1rem',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            flexShrink: 0,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <div style={{
                width: '36px', height: '36px', borderRadius: '50%',
                background: 'rgba(255,255,255,0.2)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.1rem',
              }}>
                {icon}
              </div>
              <div>
                <div style={{ color: '#fff', fontWeight: 700, fontSize: '0.9rem' }}>{label}</div>
                <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: '0.73rem' }}>
                  {loading ? '● Thinking…' : '● Online'}
                </div>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              style={{
                background: 'rgba(255,255,255,0.15)', border: 'none', color: '#fff',
                borderRadius: '50%', width: '28px', height: '28px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1rem', transition: 'background 0.2s',
              }}
              aria-label="Close"
            >×</button>
          </div>

          {/* Messages area */}
          <div style={{
            flex: 1, overflowY: 'auto',
            padding: '1rem',
            display: 'flex', flexDirection: 'column',
            background: 'var(--ss-bg-main)',
          }}>
            {messages.map((m, i) => <ChatBubble key={i} msg={m} />)}
            {loading && (
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  background: 'var(--ss-bg-hover)',
                  borderRadius: '4px 16px 16px 16px',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.08)',
                }}>
                  <TypingDots />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Quick Suggestions */}
          {suggestions.length > 0 && !loading && (
            <div style={{
              padding: '0.5rem 0.85rem 0',
              display: 'flex', gap: '0.4rem', flexWrap: 'wrap',
              background: 'var(--ss-bg-card)',
            }}>
              {suggestions.map((s, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(s)}
                  style={{
                    padding: '0.3rem 0.7rem',
                    borderRadius: '999px',
                    border: '1px solid var(--ss-primary)',
                    background: 'transparent',
                    color: 'var(--ss-primary)',
                    fontSize: '0.78rem',
                    cursor: 'pointer',
                    fontWeight: 600,
                    transition: 'all 0.15s',
                    marginBottom: '0.35rem',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = 'var(--ss-primary)'; e.currentTarget.style.color = 'var(--ss-text-on-primary)' }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = 'var(--ss-primary)' }}
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div style={{
            padding: '0.65rem 0.85rem',
            borderTop: '1px solid var(--ss-border)',
            display: 'flex', gap: '0.5rem', alignItems: 'flex-end',
            background: 'var(--ss-bg-card)',
          }}>
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask me anything…"
              disabled={loading}
              rows={1}
              style={{
                flex: 1,
                border: '1.5px solid var(--ss-border)',
                borderRadius: '12px',
                padding: '0.5rem 0.75rem',
                fontSize: '0.875rem',
                background: 'var(--ss-bg-main)',
                color: 'var(--ss-text)',
                resize: 'none',
                outline: 'none',
                lineHeight: 1.5,
                maxHeight: '120px',
                overflow: 'auto',
                transition: 'border-color 0.2s',
                fontFamily: 'inherit',
              }}
              onFocus={e => { e.target.style.borderColor = 'var(--ss-primary)' }}
              onBlur={e => { e.target.style.borderColor = 'var(--ss-border)' }}
            />
            <button
              onClick={() => sendMessage(input)}
              disabled={loading || !input.trim()}
              aria-label="Send"
              style={{
                width: '38px', height: '38px', borderRadius: '50%',
                background: input.trim() && !loading
                  ? 'var(--ss-auth-brand-gradient)'
                  : 'var(--ss-border)',
                border: 'none',
                color: input.trim() && !loading ? 'var(--ss-text-on-primary)' : 'var(--ss-text-muted)',
                cursor: input.trim() && !loading ? 'pointer' : 'default',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 0.2s',
                flexShrink: 0,
                marginBottom: '2px'
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  )
}
