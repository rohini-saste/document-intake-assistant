import React, { useState, useEffect, useRef } from 'react';
import { Send, FileText, Database, RotateCcw, Download } from 'lucide-react';
import DOMPurify from 'dompurify';
import { chatWithAssistant, resetSession } from './api';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [activeTab, setActiveTab] = useState('doc');
  const [intakeState, setIntakeState] = useState(null);
  const [draftDoc, setDraftDoc] = useState('');
  const [loading, setLoading] = useState(false);
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    handleReset();
  }, []);

  useEffect(() => {
    if (messages.length > 0 && intakeState) {
      localStorage.setItem('docIntakeSession', JSON.stringify({
        messages, intakeState, draftDoc
      }));
    }
  }, [messages, intakeState, draftDoc]);

  const handleDownload = () => {
    if (!draftDoc) return;
    const blob = new Blob([draftDoc], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Personal_Wishes_Draft.md';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleReset = async (forceClear = false) => {
    try {
      setLoading(true);
      if (forceClear) {
        localStorage.removeItem('docIntakeSession');
      } else {
        const saved = localStorage.getItem('docIntakeSession');
        if (saved) {
          const parsed = JSON.parse(saved);
          setMessages(parsed.messages);
          setIntakeState(parsed.intakeState);
          setDraftDoc(parsed.draftDoc);
          setLoading(false);
          return;
        }
      }
      
      const res = await resetSession();
      setMessages([{ role: 'assistant', content: res.reply }]);
      setIntakeState(res.state);
      setDraftDoc(res.draft_document);
    } catch (err) {
      console.error(err);
      setMessages([{ role: 'assistant', content: "Error connecting to backend." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    try {
      const res = await chatWithAssistant(userMsg, intakeState);
      setMessages(prev => [...prev, { role: 'assistant', content: res.reply }]);
      setIntakeState(res.state);
      setDraftDoc(res.draft_document);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderMarkdown = (text) => {
    if (!text) return '';
    const lines = text.split('\n');
    let inList = false;
    let html = '';

    for (let i = 0; i < lines.length; i++) {
      let line = lines[i];

      // Horizontal rule
      if (/^---$/.test(line.trim())) {
        if (inList) { html += '</ul>'; inList = false; }
        html += '<hr style="margin: 20px 0; border: none; border-top: 1px solid #e4e4e7;" />';
        continue;
      }

      // Headers
      if (line.startsWith('# ')) {
        if (inList) { html += '</ul>'; inList = false; }
        html += `<h1>${line.slice(2)}</h1>`;
        continue;
      }
      if (line.startsWith('## ')) {
        if (inList) { html += '</ul>'; inList = false; }
        html += `<h2>${line.slice(3)}</h2>`;
        continue;
      }
      if (line.startsWith('### ')) {
        if (inList) { html += '</ul>'; inList = false; }
        html += `<h3>${line.slice(4)}</h3>`;
        continue;
      }

      // Blockquote
      if (line.startsWith('> ')) {
        if (inList) { html += '</ul>'; inList = false; }
        const content = line.slice(2).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html += `<blockquote>${content}</blockquote>`;
        continue;
      }

      // List item
      if (line.trim().startsWith('- ')) {
        if (!inList) { html += '<ul style="margin-left: 20px; margin-bottom: 12px;">'; inList = true; }
        const content = line.trim().slice(2)
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\*(.*?)\*/g, '<em>$1</em>');
        html += `<li>${content}</li>`;
        continue;
      }

      if (inList) {
        html += '</ul>';
        inList = false;
      }

      if (!line.trim()) {
        continue;
      }

      // Regular line / paragraph
      const formatted = line
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
      html += `<p style="margin-bottom: 8px;">${formatted}</p>`;
    }

    if (inList) {
      html += '</ul>';
    }

    return html;
  };

  return (
    <div className="app-container">
      {/* Left Chat Pane */}
      <div className="chat-pane">
        <div className="chat-header">
          <h1>
            <FileText size={24} color="#8b5cf6" />
            Document Intake Assistant
          </h1>
        </div>
        
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              {msg.content}
            </div>
          ))}
          {loading && (
            <div className="message assistant">
              <span style={{ opacity: 0.5 }}>Thinking...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input-area">
          <input 
            type="text" 
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your answer or correct a previous one..."
            disabled={loading}
          />
          <button className="chat-send-btn" onClick={handleSend} disabled={loading} title="Send Message">
            <Send size={18} />
          </button>
          <button className="chat-send-btn" style={{ background: '#3f3f46' }} onClick={() => handleReset(true)} title="Reset Session">
            <RotateCcw size={18} />
          </button>
        </div>
      </div>

      {/* Right Preview Pane */}
      <div className="preview-pane">
        <div className="preview-tabs" style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              className={`tab ${activeTab === 'doc' ? 'active' : ''}`}
              onClick={() => setActiveTab('doc')}
            >
              <FileText size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'text-bottom' }} />
              Draft Document
            </button>
            <button 
              className={`tab ${activeTab === 'state' ? 'active' : ''}`}
              onClick={() => setActiveTab('state')}
            >
              <Database size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'text-bottom' }} />
              Structured State
            </button>
          </div>
          <button 
            className="tab" 
            style={{ background: '#8b5cf6', color: 'white', border: 'none', cursor: 'pointer' }}
            onClick={handleDownload}
            title="Download Document"
          >
            <Download size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'text-bottom' }} />
            Export
          </button>
        </div>

        <div className="preview-content">
          {activeTab === 'state' && (
            <pre className="state-viewer">
              {intakeState ? JSON.stringify(intakeState, null, 2) : 'Loading state...'}
            </pre>
          )}
          
          {activeTab === 'doc' && (
            <div className="doc-viewer" dangerouslySetInnerHTML={{ 
              __html: DOMPurify.sanitize(renderMarkdown(draftDoc))
            }} />
          )}
        </div>
      </div>
    </div>
  );
}
