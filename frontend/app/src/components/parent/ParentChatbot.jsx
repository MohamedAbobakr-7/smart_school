import { useState, useRef, useEffect } from 'react'
import { apiFetch } from '../../lib/api'

export function ParentChatbot() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hello! I am your Smart School Chatbot. How can I help you today?' }
  ])
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  const addMessage = (sender, text) => {
    setMessages(prev => [...prev, { sender, text }])
  }

  const handleQuestion = async (type) => {
    if (loading) return
    setLoading(true)

    let userMsg = ''
    if (type === 'attendance') userMsg = 'Show attendance'
    if (type === 'grades') userMsg = 'Show grades'
    if (type === 'absences') userMsg = 'Any absences?'

    addMessage('user', userMsg)

    try {
      if (type === 'attendance') {
        const res = await apiFetch('/attendance/')
        const data = await res.json().catch(() => [])
        const list = Array.isArray(data) ? data : data.results || []
        
        const total = list.length
        const present = list.filter(r => r.status === 'present').length
        const absent = list.filter(r => r.status === 'absent').length
        
        addMessage('bot', `I found ${total} attendance records across your children. ${present} Present and ${absent} Absent.`)
      } 
      else if (type === 'grades') {
        const res = await apiFetch('/grades/')
        const data = await res.json().catch(() => [])
        const list = Array.isArray(data) ? data : data.results || []
        
        if (list.length === 0) {
          addMessage('bot', 'No grades found for your children yet.')
        } else {
          const valid = list.filter(g => g.percentage != null)
          if (valid.length === 0) {
            addMessage('bot', `I found ${list.length} grade records but couldn't calculate an average.`)
          } else {
            const avg = valid.reduce((a, b) => a + b.percentage, 0) / valid.length
            addMessage('bot', `I found ${list.length} recent grades. The average score is ${Math.round(avg)}%.`)
          }
        }
      }
      else if (type === 'absences') {
        const res = await apiFetch('/attendance/')
        const data = await res.json().catch(() => [])
        const list = Array.isArray(data) ? data : data.results || []
        
        const absences = list.filter(r => r.status === 'absent')
        if (absences.length === 0) {
          addMessage('bot', 'Great news! No absences found for your children.')
        } else {
          // Get the latest 3 absences
          const recent = absences.slice(0, 3)
          const details = recent.map(a => `${a.student_name || 'Your child'} on ${new Date(a.date).toLocaleDateString()}`).join(', ')
          addMessage('bot', `I found ${absences.length} absences. Recent ones: ${details}.`)
        }
      }
    } catch (e) {
      addMessage('bot', 'Sorry, I encountered an error fetching the data.')
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) {
    return (
      <button 
        onClick={() => setIsOpen(true)}
        style={{
          position: 'fixed',
          bottom: '2rem',
          right: '2rem',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          background: '#6366f1',
          color: 'white',
          border: 'none',
          boxShadow: '0 4px 12px rgba(99, 102, 241, 0.4)',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}
        aria-label="Open Chatbot"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
      </button>
    )
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: '2rem',
      right: '2rem',
      width: '350px',
      height: '500px',
      background: 'var(--bg)',
      borderRadius: '16px',
      boxShadow: '0 8px 30px rgba(0,0,0,0.12)',
      border: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      zIndex: 1000,
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        background: '#6366f1',
        color: 'white',
        padding: '1rem',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          </svg>
          Smart School Chatbot
        </h3>
        <button 
          onClick={() => setIsOpen(false)}
          style={{ background: 'transparent', border: 'none', color: 'white', cursor: 'pointer', display: 'flex', padding: '4px' }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '1rem',
        background: 'var(--bg)'
      }}>
        {messages.map((m, i) => {
          const isBot = m.sender === 'bot'
          return (
            <div key={i} style={{ display: 'flex', justifyContent: isBot ? 'flex-start' : 'flex-end' }}>
              <div style={{
                maxWidth: '80%',
                padding: '0.75rem 1rem',
                borderRadius: '12px',
                background: isBot ? 'var(--code-bg)' : '#6366f1',
                color: isBot ? 'var(--text-h)' : 'white',
                border: isBot ? '1px solid var(--border)' : 'none',
                fontSize: '0.9rem',
                lineHeight: 1.4
              }}>
                {m.text}
              </div>
            </div>
          )
        })}
        {loading && (
          <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
            <div style={{ padding: '0.75rem 1rem', borderRadius: '12px', background: 'var(--code-bg)', border: '1px solid var(--border)', fontSize: '0.9rem', color: '#9ca3af' }}>
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      <div style={{
        padding: '1rem',
        borderTop: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        background: 'var(--bg)'
      }}>
        <p style={{ margin: '0 0 0.25rem', fontSize: '0.8rem', color: '#6b7280', fontWeight: 600 }}>Ask a question:</p>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          <button 
            disabled={loading}
            onClick={() => handleQuestion('attendance')}
            style={{ padding: '0.5rem 0.75rem', borderRadius: '20px', border: '1px solid var(--border-color)', background: 'transparent', cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-color)' }}
          >
            Show attendance
          </button>
          <button 
            disabled={loading}
            onClick={() => handleQuestion('grades')}
            style={{ padding: '0.5rem 0.75rem', borderRadius: '20px', border: '1px solid var(--border-color)', background: 'transparent', cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-color)' }}
          >
            Show grades
          </button>
          <button 
            disabled={loading}
            onClick={() => handleQuestion('absences')}
            style={{ padding: '0.5rem 0.75rem', borderRadius: '20px', border: '1px solid var(--border-color)', background: 'transparent', cursor: 'pointer', fontSize: '0.85rem', color: 'var(--text-color)' }}
          >
            Any absences?
          </button>
        </div>
      </div>
    </div>
  )
}
