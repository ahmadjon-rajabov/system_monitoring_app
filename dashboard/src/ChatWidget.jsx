import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import axios from 'axios'
import { Send, Bot, User, Loader2, Terminal } from 'lucide-react'

export default function ChatWidget() {
  const [messages, setMessages] = useState([
    { role: 'bot', text: "Systems online. Accessing logs... Ready. How can I assist you with the infrastructure?" }
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }
  useEffect(scrollToBottom, [messages])

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMessage = input
    setInput("")
    setMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setIsLoading(true)

    try {
      const API_URL = import.meta.env.VITE_API_URL || "/api"
      const res = await axios.post(`${API_URL}/chat`, { question: userMessage })
      setMessages(prev => [...prev, { role: 'bot', text: res.data.answer }])
    } catch (error) {
      setMessages(prev => [...prev, { role: 'bot', text: "Error: Gemini AI Connection Failed." }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div style={{ backgroundColor: "#262626", borderRadius: "12px", border: "1px solid #333", height: "100%", overflow: "hidden", 
      display: "flex", flexDirection: "column", boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
    }}>
      
      {/* Header */}
      <div style={{ padding: "1.5rem", borderBottom: "1px solid #333", display: "flex", alignItems: "center", gap: "10px",
        backgroundColor: "#1f1f1f", borderTopLeftRadius: "12px", borderTopRightRadius: "12px", flexShrink: 0
      }}>
        <Terminal size={24} color="#4ade80" />
        <h3 style={{ margin: 0, color: "white" }}>AI System Analyst</h3>
        <span style={{ fontSize: "0.8rem", color: "#666", marginLeft: "auto" }}>Powered by Gemini 1.5</span>
      </div>

      {/* Messages Area */}
      <div style={{ flex: 1, padding: "20px", overflowY: "auto", display: "flex", flexDirection: "column", gap: "15px", minHeight: 0 }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ display: 'flex', gap: '12px', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }}>
            <div style={{ width: '35px', height: '35px', borderRadius: '8px', backgroundColor: msg.role === 'user' ? '#3b82f6' : '#333',
              display: 'flex', alignItems: 'center', justifyContent: 'center',flexShrink: 0
            }}>
              {msg.role === 'user' ? <User size={18} color="white" /> : <Bot size={18} color="#4ade80" />}
            </div>
            <div style={{ backgroundColor: msg.role === 'user' ? '#1e3a8a' : '#333', color: 'white', padding: '12px 16px', borderRadius: '8px',
              maxWidth: '80%', fontSize: '0.95rem', lineHeight: '1.5', border: msg.role === 'user' ? '1px solid #1d4ed8' : '1px solid #444'
            }}>
                <ReactMarkdown 
                    components={{
                        p: ({node, ...props}) => <p style={{margin: 0, marginBottom: '0.5em'}} {...props} />,
                        ul: ({node, ...props}) => <ul style={{margin: 0, paddingLeft: '1.2em'}} {...props} />,
                        li: ({node, ...props}) => <li style={{marginBottom: '0.3em'}} {...props} />,
                        strong: ({node, ...props}) => <strong style={{color: '#4ade80'}} {...props} />
                    }}
                >
                    {msg.text}
                </ReactMarkdown>
            </div>
          </div>
        ))}
        {isLoading && (
          <div style={{ display: 'flex', gap: '12px' }}>
             <div style={{ width: '35px', height: '35px', borderRadius: '8px', backgroundColor: '#333', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={18} color="#4ade80" />
             </div>
             <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#888' }}>
                <Loader2 size={16} className="animate-spin" />
                <span>Analyzing logs...</span>
             </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ padding: "20px", borderTop: "1px solid #333", backgroundColor: "#1f1f1f", borderBottomLeftRadius: "12px", borderBottomRightRadius: "12px" }}>
        <div style={{ display: "flex", gap: "10px" }}>
          <input 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Type a command or question..."
            style={{ flex: 1, backgroundColor: '#0a0a0a', border: '1px solid #333', borderRadius: '6px', padding: '12px', 
                color: 'white', outline: 'none', fontFamily: 'monospace'
            }} 
          />
          <button 
            onClick={sendMessage}
            disabled={isLoading}
            style={{ backgroundColor: '#4ade80', border: 'none', borderRadius: '6px', width: '50px', cursor: 'pointer', display: 'flex', 
                alignItems: 'center', justifyContent: 'center', opacity: isLoading ? 0.5 : 1
            }}>
            <Send size={20} color="black" />
          </button>
        </div>
      </div>
    </div>
  )
}