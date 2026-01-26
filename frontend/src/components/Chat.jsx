import React, { useState, useEffect, useRef } from 'react';
import './Chat.css';

const Chat = () => {
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [typingUsers, setTypingUsers] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const messagesEndRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  // Mock user data - in real app this would come from authentication
  useEffect(() => {
    setUser({
      id: 'user123',
      name: 'John Doe',
      language: 'en',
      token: 'mock-jwt-token'
    });
  }, []);

  // Initialize WebSocket connection
  useEffect(() => {
    if (user && !wsRef.current) {
      connectWebSocket();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [user]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8000/api/v1/chat/ws?token=${user.token}`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      };

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (user) {
            connectWebSocket();
          }
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error. Retrying...');
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setError('Failed to connect to chat service');
    }
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'new_message':
        if (data.conversation_id === activeConversation?.id) {
          addMessageToChat(data.data);
        }
        updateConversationPreview(data.conversation_id, data.data);
        break;

      case 'typing_indicator':
        if (data.conversation_id === activeConversation?.id) {
          handleTypingIndicator(data.data);
        }
        break;

      case 'read_receipt':
        if (data.conversation_id === activeConversation?.id) {
          handleReadReceipt(data.data);
        }
        break;

      case 'subscribed':
        console.log(`Subscribed to conversation ${data.conversation_id}`);
        break;

      case 'error':
        setError(data.message);
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const addMessageToChat = (messageData) => {
    const newMessage = {
      id: messageData.message_id,
      sender_id: messageData.sender_id,
      sender_name: messageData.sender_name,
      text: messageData.text,
      timestamp: new Date(messageData.timestamp),
      message_type: messageData.message_type,
      is_own: messageData.sender_id === user.id
    };

    setMessages(prev => [...prev, newMessage]);
  };

  const updateConversationPreview = (conversationId, messageData) => {
    setConversations(prev => prev.map(conv => 
      conv.id === conversationId 
        ? { 
            ...conv, 
            last_message_preview: messageData.text,
            last_message_at: new Date(messageData.timestamp),
            unread_count: conv.id === activeConversation?.id ? 0 : conv.unread_count + 1
          }
        : conv
    ));
  };

  const handleTypingIndicator = (data) => {
    if (data.status === 'typing') {
      setTypingUsers(prev => {
        const existing = prev.find(u => u.user_id === data.user_id);
        if (!existing) {
          return [...prev, { user_id: data.user_id, user_name: data.user_name }];
        }
        return prev;
      });

      // Remove typing indicator after 3 seconds
      setTimeout(() => {
        setTypingUsers(prev => prev.filter(u => u.user_id !== data.user_id));
      }, 3000);
    } else {
      setTypingUsers(prev => prev.filter(u => u.user_id !== data.user_id));
    }
  };

  const handleReadReceipt = (data) => {
    // Update message read status
    setMessages(prev => prev.map(msg => 
      msg.id === data.message_id 
        ? { ...msg, read_by: [...(msg.read_by || []), data.user_id] }
        : msg
    ));
  };

  const subscribeToConversation = (conversationId) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'subscribe',
        conversation_id: conversationId
      }));
    }
  };

  const sendTypingIndicator = (status) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && activeConversation) {
      wsRef.current.send(JSON.stringify({
        type: 'typing',
        conversation_id: activeConversation.id,
        status: status
      }));
    }
  };

  const loadConversations = async () => {
    try {
      setLoading(true);
      // Mock API call - replace with actual API
      const mockConversations = [
        {
          id: 'conv1',
          type: 'direct',
          participants: [{ user_id: 'user456', user_name: 'Jane Smith' }],
          last_message_preview: 'Hello, how are you?',
          last_message_at: new Date(),
          unread_count: 2
        },
        {
          id: 'conv2',
          type: 'direct',
          participants: [{ user_id: 'user789', user_name: 'Bob Johnson' }],
          last_message_preview: 'Thanks for the information',
          last_message_at: new Date(Date.now() - 3600000),
          unread_count: 0
        }
      ];
      
      setConversations(mockConversations);
    } catch (error) {
      setError('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (conversationId) => {
    try {
      setLoading(true);
      // Mock API call - replace with actual API
      const mockMessages = [
        {
          id: 'msg1',
          sender_id: 'user456',
          sender_name: 'Jane Smith',
          text: 'Hello, how are you?',
          translated_text: 'Hello, how are you?',
          timestamp: new Date(Date.now() - 1800000),
          message_type: 'text',
          is_own: false
        },
        {
          id: 'msg2',
          sender_id: user.id,
          sender_name: user.name,
          text: 'I am doing well, thank you!',
          timestamp: new Date(Date.now() - 1200000),
          message_type: 'text',
          is_own: true
        }
      ];
      
      setMessages(mockMessages);
    } catch (error) {
      setError('Failed to load messages');
    } finally {
      setLoading(false);
    }
  };

  const selectConversation = async (conversation) => {
    setActiveConversation(conversation);
    await loadMessages(conversation.id);
    subscribeToConversation(conversation.id);
    
    // Mark conversation as read
    setConversations(prev => prev.map(conv => 
      conv.id === conversation.id ? { ...conv, unread_count: 0 } : conv
    ));
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !activeConversation) return;

    try {
      const messageText = newMessage.trim();
      setNewMessage('');

      // Add message optimistically to UI
      const tempMessage = {
        id: `temp-${Date.now()}`,
        sender_id: user.id,
        sender_name: user.name,
        text: messageText,
        timestamp: new Date(),
        message_type: 'text',
        is_own: true,
        sending: true
      };

      setMessages(prev => [...prev, tempMessage]);

      // Mock API call - replace with actual API
      setTimeout(() => {
        setMessages(prev => prev.map(msg => 
          msg.id === tempMessage.id 
            ? { ...msg, id: `msg-${Date.now()}`, sending: false }
            : msg
        ));
      }, 1000);

    } catch (error) {
      setError('Failed to send message');
    }
  };

  const handleMessageInput = (e) => {
    setNewMessage(e.target.value);

    // Send typing indicator
    if (!isTyping) {
      setIsTyping(true);
      sendTypingIndicator('typing');
    }

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set timeout to stop typing indicator
    typingTimeoutRef.current = setTimeout(() => {
      setIsTyping(false);
      sendTypingIndicator('stopped');
    }, 1000);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const formatDate = (date) => {
    const today = new Date();
    const messageDate = new Date(date);
    
    if (messageDate.toDateString() === today.toDateString()) {
      return formatTime(messageDate);
    } else {
      return messageDate.toLocaleDateString();
    }
  };

  // Load conversations on component mount
  useEffect(() => {
    loadConversations();
  }, []);

  return (
    <div className="chat-container">
      {/* Connection Status */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        <span className="status-indicator"></span>
        {isConnected ? 'Connected' : 'Connecting...'}
      </div>

      <div className="chat-layout">
        {/* Conversations Sidebar */}
        <div className="conversations-sidebar">
          <div className="sidebar-header">
            <h2>Conversations</h2>
            <button className="new-chat-btn" title="New Chat">+</button>
          </div>

          {loading && !conversations.length ? (
            <div className="loading">Loading conversations...</div>
          ) : (
            <div className="conversations-list">
              {conversations.map(conversation => (
                <div
                  key={conversation.id}
                  className={`conversation-item ${activeConversation?.id === conversation.id ? 'active' : ''}`}
                  onClick={() => selectConversation(conversation)}
                >
                  <div className="conversation-avatar">
                    {conversation.participants[0]?.user_name?.charAt(0) || '?'}
                  </div>
                  <div className="conversation-info">
                    <div className="conversation-name">
                      {conversation.participants[0]?.user_name || 'Unknown'}
                    </div>
                    <div className="conversation-preview">
                      {conversation.last_message_preview}
                    </div>
                  </div>
                  <div className="conversation-meta">
                    <div className="conversation-time">
                      {formatDate(conversation.last_message_at)}
                    </div>
                    {conversation.unread_count > 0 && (
                      <div className="unread-badge">{conversation.unread_count}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Chat Area */}
        <div className="chat-area">
          {activeConversation ? (
            <>
              {/* Chat Header */}
              <div className="chat-header">
                <div className="chat-participant">
                  <div className="participant-avatar">
                    {activeConversation.participants[0]?.user_name?.charAt(0) || '?'}
                  </div>
                  <div className="participant-info">
                    <div className="participant-name">
                      {activeConversation.participants[0]?.user_name || 'Unknown'}
                    </div>
                    <div className="participant-status">
                      {isConnected ? 'Online' : 'Offline'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Messages Area */}
              <div className="messages-area">
                {loading && !messages.length ? (
                  <div className="loading">Loading messages...</div>
                ) : (
                  <>
                    {messages.map(message => (
                      <div
                        key={message.id}
                        className={`message ${message.is_own ? 'own-message' : 'other-message'}`}
                      >
                        {!message.is_own && (
                          <div className="message-avatar">
                            {message.sender_name?.charAt(0) || '?'}
                          </div>
                        )}
                        <div className="message-content">
                          <div className="message-bubble">
                            <div className="message-text">
                              {message.translated_text || message.text}
                            </div>
                            {message.translated_text && message.translated_text !== message.text && (
                              <div className="original-text">
                                Original: {message.text}
                              </div>
                            )}
                          </div>
                          <div className="message-meta">
                            <span className="message-time">{formatTime(message.timestamp)}</span>
                            {message.sending && <span className="sending-indicator">Sending...</span>}
                          </div>
                        </div>
                      </div>
                    ))}

                    {/* Typing Indicators */}
                    {typingUsers.length > 0 && (
                      <div className="typing-indicator">
                        <div className="typing-avatar">
                          {typingUsers[0].user_name?.charAt(0) || '?'}
                        </div>
                        <div className="typing-bubble">
                          <div className="typing-dots">
                            <span></span>
                            <span></span>
                            <span></span>
                          </div>
                        </div>
                      </div>
                    )}

                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* Message Input */}
              <div className="message-input-area">
                <div className="message-input-container">
                  <textarea
                    value={newMessage}
                    onChange={handleMessageInput}
                    onKeyPress={handleKeyPress}
                    placeholder="Type a message..."
                    className="message-input"
                    rows="1"
                    disabled={!isConnected}
                  />
                  <button
                    onClick={sendMessage}
                    disabled={!newMessage.trim() || !isConnected}
                    className="send-button"
                  >
                    Send
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="no-conversation">
              <h3>Select a conversation to start chatting</h3>
              <p>Choose from your existing conversations or start a new one.</p>
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-toast">
          <span>{error}</span>
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}
    </div>
  );
};

export default Chat;