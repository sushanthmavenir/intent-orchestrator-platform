import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './index.css';

const WEBSOCKET_URL = 'ws://localhost:8004/ws/chat';
const API_BASE_URL = 'http://localhost:8004';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [intentForm, setIntentForm] = useState({
    name: '',
    description: '',
    expressionLanguage: 'JSON-LD',
    expressionValue: '',
    lifecycleStatus: 'created'
  });
  const [isSubmittingIntent, setIsSubmittingIntent] = useState(false);
  const messagesEndRef = useRef(null);
  const websocketRef = useRef(null);

  useEffect(() => {
    const connectWebSocket = () => {
      if (websocketRef.current && (websocketRef.current.readyState === WebSocket.OPEN || websocketRef.current.readyState === WebSocket.CONNECTING)) {
        return;
      }

      setConnectionStatus('connecting');
      const ws = new WebSocket(WEBSOCKET_URL);
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnectionStatus('connected');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);

        if (data.type === 'history') {
          setMessages(data.messages || []);
        } else if (data.type === 'connection') {
          addSystemMessage(data.message);
        } else if (data.type === 'processing_status') {
          setMessages(prev => [...prev, { ...data, isProcessing: true }]);
        } else if (data.type === 'intent_created') {
          setMessages(prev => [...prev, { ...data, isIntentCreation: true }]);
        } else if (data.type === 'workflow_starting') {
          setMessages(prev => [...prev, { ...data, isWorkflowStatus: true }]);
        } else if (data.type === 'workflow_completed') {
          setMessages(prev => [...prev, { ...data, isWorkflowCompletion: true }]);
        } else if (data.type === 'risk_assessment') {
          setMessages(prev => [...prev, { ...data, isRiskAssessment: true }]);
        } else if (data.type === 'recommendation') {
          setMessages(prev => [...prev, { ...data, isRecommendation: true }]);
        } else if (data.type === 'error' || data.type === 'workflow_error') {
          setMessages(prev => [...prev, { ...data, isError: true }]);
        } else {
          setMessages(prev => [...prev, data]);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnectionStatus('disconnected');
        // Automatically attempt to reconnect
        setTimeout(connectWebSocket, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close(); // This will trigger the onclose handler and reconnection logic
      };
    };

    connectWebSocket();

    return () => {
      if (websocketRef.current) {
        websocketRef.current.onclose = null; // Prevent reconnection attempts on component unmount
        websocketRef.current.close();
      }
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addSystemMessage = (content) => {
    const systemMessage = {
      type: 'system_message',
      content,
      timestamp: new Date().toISOString(),
      id: Date.now().toString()
    };
    setMessages(prev => [...prev, systemMessage]);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const sendMessage = (e) => {
    e.preventDefault();
    
    if (!inputMessage.trim() || !websocketRef.current || connectionStatus !== 'connected') {
      return;
    }

    const message = {
      type: 'chat_message',
      content: inputMessage.trim(),
      user: 'User'
    };

    websocketRef.current.send(JSON.stringify(message));
    setInputMessage('');
  };

  const handleIntentFormChange = (e) => {
    const { name, value } = e.target;
    setIntentForm(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const submitIntent = async (e) => {
    e.preventDefault();
    
    if (!intentForm.name || !intentForm.expressionValue) {
      alert('Please fill in the required fields (Name and Expression Value)');
      return;
    }

    setIsSubmittingIntent(true);

    try {
      // Create the intent via REST API
      const intentPayload = {
        name: intentForm.name,
        description: intentForm.description,
        lifecycleStatus: intentForm.lifecycleStatus,
        expression: {
          '@type': intentForm.expressionLanguage === 'JSON-LD' ? 'JsonLdExpression' : 
                   intentForm.expressionLanguage === 'Turtle' ? 'TurtleExpression' : 'RdxmlExpression',
          expressionLanguage: intentForm.expressionLanguage,
          expressionValue: intentForm.expressionValue
        }
      };

      const response = await axios.post(`${API_BASE_URL}/tmf-api/intent/v4/intent`, intentPayload);
      
      // Notify via WebSocket
      if (websocketRef.current && connectionStatus === 'connected') {
        const intentMessage = {
          type: 'intent_submission',
          intent_data: response.data,
          user: 'User'
        };
        websocketRef.current.send(JSON.stringify(intentMessage));
      }

      // Reset form
      setIntentForm({
        name: '',
        description: '',
        expressionLanguage: 'JSON-LD',
        expressionValue: '',
        lifecycleStatus: 'created'
      });

      addSystemMessage(`Intent "${response.data.name}" created successfully with ID: ${response.data.id}`);

    } catch (error) {
      console.error('Error creating intent:', error);
      addSystemMessage(`Error creating intent: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsSubmittingIntent(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const getMessageClass = (message) => {
    if (message.type === 'user_message') return 'user';
    if (message.isError) return 'error';
    if (message.isProcessing) return 'processing';
    if (message.isIntentCreation) return 'intent-creation';
    if (message.isWorkflowStatus || message.type === 'workflow_starting') return 'workflow-status';
    if (message.isWorkflowCompletion) return 'workflow-completion';
    if (message.isRiskAssessment) return 'risk-assessment';
    if (message.isRecommendation) return 'recommendation';
    if (message.type === 'bot_message') return 'bot';
    return 'system';
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      default: return 'Disconnected';
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Intent Orchestrator Platform</h1>
        <p>TMF 921A Intent Management with Chat Interface and Workflow Orchestration</p>
      </header>

      <main className="main-content">
        <div className="chat-container">
          <div className="chat-header">
            <div className="chat-title">
              <h2>💬 Smart Chat Interface</h2>
              <p className="chat-subtitle">
                Type naturally - AI automatically creates TMF 921A intents and runs fraud detection workflows
              </p>
            </div>
            <div className="connection-status">
              <div className={`status-indicator ${connectionStatus}`}></div>
              <span>{getConnectionStatusText()}</span>
            </div>
          </div>
          <div className="chat-instructions">
            <div className="instruction-box">
              <strong>💡 How it works:</strong> Just type your message naturally (e.g., "I think someone is trying to scam me"). 
              The system will automatically create a TMF 921A intent, analyze your message, and run appropriate fraud detection workflows.
            </div>
          </div>

          <div className="chat-messages">
            {messages.map((message) => (
              <div key={message.id} className={`message ${getMessageClass(message)}`}>
                <div className="message-content">
                  {message.content}
                </div>
                <div className="message-meta">
                  {message.user} • {formatTimestamp(message.timestamp)}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            <form onSubmit={sendMessage} className="chat-input-form">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Type naturally... (e.g., 'Someone called pretending to be my bank', 'I got a suspicious text message')"
                className="chat-input"
                disabled={connectionStatus !== 'connected'}
              />
              <button
                type="submit"
                className="send-button"
                disabled={connectionStatus !== 'connected' || !inputMessage.trim()}
              >
                Send
              </button>
            </form>
          </div>
        </div>

        <div className="sidebar">
          <div className="sidebar-header">
            <h3>🔧 Manual Intent Creation</h3>
            <p className="sidebar-subtitle">
              Direct TMF 921A API access for developers and advanced users
            </p>
          </div>
          <div className="sidebar-instructions">
            <div className="instruction-box advanced">
              <strong>⚙️ Technical Interface:</strong> Create TMF 921A intents manually using structured forms. 
              This bypasses the chat-to-intent processing and creates intents directly via the API.
            </div>
          </div>
          <div className="sidebar-content">
            <form onSubmit={submitIntent} className="intent-form">
              <div className="form-group">
                <label htmlFor="name">Intent Name *</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={intentForm.name}
                  onChange={handleIntentFormChange}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  name="description"
                  value={intentForm.description}
                  onChange={handleIntentFormChange}
                  placeholder="Describe what this intent should achieve..."
                />
              </div>

              <div className="form-group">
                <label htmlFor="lifecycleStatus">Lifecycle Status</label>
                <select
                  id="lifecycleStatus"
                  name="lifecycleStatus"
                  value={intentForm.lifecycleStatus}
                  onChange={handleIntentFormChange}
                >
                  <option value="created">Created</option>
                  <option value="active">Active</option>
                  <option value="pending">Pending</option>
                  <option value="fulfilled">Fulfilled</option>
                  <option value="suspended">Suspended</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="terminated">Terminated</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="expressionLanguage">Expression Language</label>
                <select
                  id="expressionLanguage"
                  name="expressionLanguage"
                  value={intentForm.expressionLanguage}
                  onChange={handleIntentFormChange}
                >
                  <option value="JSON-LD">JSON-LD</option>
                  <option value="Turtle">Turtle</option>
                  <option value="RDF-XML">RDF-XML</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="expressionValue">Expression Value *</label>
                <textarea
                  id="expressionValue"
                  name="expressionValue"
                  value={intentForm.expressionValue}
                  onChange={handleIntentFormChange}
                  placeholder="Enter the intent expression..."
                  required
                />
              </div>

              <button
                type="submit"
                className="submit-intent-button"
                disabled={isSubmittingIntent}
              >
                {isSubmittingIntent && <div className="loading-spinner"></div>}
                {isSubmittingIntent ? 'Creating Intent...' : 'Create Intent'}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;