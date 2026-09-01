import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../services/api';

const AIChat = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [selectedConsultationId, setSelectedConsultationId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await apiClient.post('/api/v1/ai/chat', {
        message: inputMessage,
        patient_id: selectedPatientId,
        consultation_id: selectedConsultationId,
        context: {}
      });

      const aiMessage = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        sources: response.data.sources,
        tool_executions: response.data.tool_executions,
        confidence: response.data.confidence
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('AI chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
        error: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSelectedPatientId(null);
    setSelectedConsultationId(null);
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700 rounded-t-lg">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <div>
            <h2 className="text-white font-semibold text-lg">AI Assistant</h2>
            <p className="text-blue-100 text-sm">Powered by Amazon Bedrock</p>
          </div>
        </div>
        <button
          onClick={clearChat}
          className="px-3 py-1.5 text-sm bg-white/20 hover:bg-white/30 text-white rounded-lg transition-colors"
        >
          Clear Chat
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-700 mb-2">Start a conversation</h3>
            <p className="text-sm max-w-md">
              Ask me about patient information, consultation history, document analysis, 
              or practice analytics. I can help you prepare for consultations and find relevant information.
            </p>
            <div className="mt-4 space-y-2 text-sm">
              <div className="bg-blue-50 px-4 py-2 rounded-lg text-blue-700">
                "What was the previous diagnosis for Client AYU-000001?"
              </div>
              <div className="bg-blue-50 px-4 py-2 rounded-lg text-blue-700">
                "Show me today's consultations"
              </div>
              <div className="bg-blue-50 px-4 py-2 rounded-lg text-blue-700">
                "What are the most common conditions this month?"
              </div>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.error
                  ? 'bg-red-50 text-red-700 border border-red-200'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                <div className="mb-3 pb-3 border-b border-gray-300">
                  <p className="text-xs font-semibold text-gray-600 mb-2">Sources:</p>
                  {message.sources.map((source, idx) => (
                    <div key={idx} className="text-xs text-gray-600 mb-1">
                      <span className="font-medium">{source.type}:</span> {source.source || 'N/A'}
                      {source.similarity && (
                        <span className="ml-2 text-gray-500">(similarity: {source.similarity.toFixed(2)})</span>
                      )}
                    </div>
                  ))}
                </div>
              )}

              <div className="prose prose-sm max-w-none">
                {message.content.split('\n').map((line, idx) => (
                  <p key={idx} className={line.trim() === '' ? 'my-2' : ''}>
                    {line}
                  </p>
                ))}
              </div>

              {message.role === 'assistant' && message.tool_executions && message.tool_executions.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-300">
                  <p className="text-xs font-semibold text-gray-600 mb-2">Tools Used:</p>
                  <div className="flex flex-wrap gap-1">
                    {message.tool_executions.map((tool, idx) => (
                      <span
                        key={idx}
                        className={`px-2 py-1 rounded text-xs ${
                          tool.success
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {tool.tool_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-2 text-xs opacity-70">
                {new Date(message.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-4">
              <div className="flex space-x-2">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-gray-50 rounded-b-lg">
        <form onSubmit={handleSendMessage} className="flex space-x-3">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me about patients, consultations, documents, or analytics..."
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={2}
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !inputMessage.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center space-x-2"
          >
            <span>Send</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          AI responses are for informational purposes only and should not replace professional medical judgment.
        </p>
      </div>
    </div>
  );
};

export default AIChat;
