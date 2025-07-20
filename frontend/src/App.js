import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Personality data
const personalities = [
  {
    _id: 'assistant',
    name: 'Assistant',
    description: 'Helpful and professional AI assistant',
    avatar_color: 'blue',
    personality_traits: ['Professional', 'Helpful', 'Clear', 'Detailed']
  },
  {
    _id: 'creative',
    name: 'Creative', 
    description: 'Artistic and imaginative AI companion',
    avatar_color: 'purple',
    personality_traits: ['Artistic', 'Imaginative', 'Inspiring', 'Unique']
  },
  {
    _id: 'expert',
    name: 'Expert',
    description: 'Technical and analytical AI specialist', 
    avatar_color: 'green',
    personality_traits: ['Technical', 'Analytical', 'Precise', 'Logical']
  },
  {
    _id: 'friend',
    name: 'Friend',
    description: 'Casual and supportive AI companion',
    avatar_color: 'orange', 
    personality_traits: ['Friendly', 'Casual', 'Supportive', 'Warm']
  }
];

// Voice Recording Hook
const useVoiceRecording = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioData, setAudioData] = useState(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks = [];

      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result.split(',')[1];
          setAudioData(base64);
        };
        reader.readAsDataURL(blob);
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Microphone access is required for voice messages');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) {
      mediaRecorder.stop();
      mediaRecorder.stream.getTracks().forEach(track => track.stop());
      setIsRecording(false);
    }
  };

  return { isRecording, audioData, startRecording, stopRecording, setAudioData };
};

// Message Component
const Message = ({ message, personality }) => {
  const isUser = message.role === 'user';
  const avatarColor = personality?.avatar_color || 'gray';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`flex max-w-xs lg:max-w-md ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        {!isUser && (
          <div className={`w-10 h-10 rounded-full bg-${avatarColor}-500 flex items-center justify-center text-white font-bold mr-3`}>
            {personality?.name?.[0] || 'A'}
          </div>
        )}
        <div className={`px-4 py-2 rounded-2xl ${
          isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-gray-100 text-gray-800 border border-gray-200'
        }`}>
          <p className="text-sm">{message.content}</p>
          {message.message_type === 'voice' && (
            <span className="text-xs opacity-75">🎵 Voice message</span>
          )}
        </div>
        {isUser && (
          <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold ml-3">
            You
          </div>
        )}
      </div>
    </div>
  );
};

// Personality Selector Component
const PersonalitySelector = ({ personalities, selectedPersonality, onSelectPersonality }) => {
  return (
    <div className="bg-white border-b border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">AI Personalities</h3>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
        {personalities.map((personality) => (
          <button
            key={personality._id}
            onClick={() => onSelectPersonality(personality)}
            className={`p-3 rounded-lg border-2 transition-all duration-200 ${
              selectedPersonality?._id === personality._id
                ? `border-${personality.avatar_color}-500 bg-${personality.avatar_color}-50`
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className={`w-8 h-8 rounded-full bg-${personality.avatar_color}-500 flex items-center justify-center text-white font-bold mb-2 mx-auto`}>
              {personality.name[0]}
            </div>
            <p className="text-xs font-medium text-gray-800">{personality.name}</p>
            <p className="text-xs text-gray-600 mt-1">{personality.description}</p>
            <div className="flex flex-wrap gap-1 mt-2">
              {personality.personality_traits.slice(0, 2).map((trait, idx) => (
                <span key={idx} className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                  {trait}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

// Voice Controls Component
const VoiceControls = ({ isRecording, onStartRecording, onStopRecording, onSendVoice, canSend }) => {
  return (
    <div className="flex items-center space-x-2">
      {!isRecording ? (
        <button
          onClick={onStartRecording}
          className="p-2 bg-red-500 hover:bg-red-600 text-white rounded-full transition-colors duration-200"
          title="Start voice recording"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </button>
      ) : (
        <button
          onClick={onStopRecording}
          className="p-2 bg-gray-500 hover:bg-gray-600 text-white rounded-full transition-colors duration-200 animate-pulse"
          title="Stop recording"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 6h12v12H6z"/>
          </svg>
        </button>
      )}
      
      {canSend && (
        <button
          onClick={onSendVoice}
          className="p-2 bg-green-500 hover:bg-green-600 text-white rounded-full transition-colors duration-200"
          title="Send voice message"
        >
          <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      )}
    </div>
  );
};

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedPersonality, setSelectedPersonality] = useState(personalities[0]);
  const [sessionId, setSessionId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [realtimeConnected, setRealtimeConnected] = useState(false);
  
  const messagesEndRef = useRef(null);
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  
  // Voice recording hook
  const { isRecording, audioData, startRecording, stopRecording, setAudioData } = useVoiceRecording();

  // Initialize session
  useEffect(() => {
    const initializeSession = async () => {
      try {
        const response = await fetch(`${backendUrl}/api/sessions/new`);
        const data = await response.json();
        setSessionId(data.session_id);
      } catch (error) {
        console.error('Error creating session:', error);
        setSessionId(`session-${Date.now()}`);
      }
    };
    
    initializeSession();
  }, [backendUrl]);

  // Auto-scroll to bottom
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Send text message
  const sendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
      message_type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${backendUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: inputMessage,
          personality_id: selectedPersonality._id,
          session_id: sessionId
        }),
      });

      const data = await response.json();
      
      const aiMessage = {
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        message_type: 'text'
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
        message_type: 'text'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Send voice message
  const sendVoiceMessage = async () => {
    if (!audioData) return;

    const userMessage = {
      role: 'user',
      content: '[Voice message sent]',
      timestamp: new Date(),
      message_type: 'voice'
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${backendUrl}/api/voice/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio_data: audioData,
          personality_id: selectedPersonality._id,
          session_id: sessionId
        }),
      });

      const data = await response.json();
      
      const aiMessage = {
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
        message_type: 'text'
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending voice message:', error);
      const errorMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your voice message.',
        timestamp: new Date(),
        message_type: 'text'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setAudioData(null);
    }
  };

  // Initialize realtime voice chat
  const startRealtimeVoice = async () => {
    try {
      // This would initialize the WebRTC realtime voice chat
      console.log('Starting realtime voice chat...');
      setRealtimeConnected(true);
      alert('Realtime voice chat would be initialized here with your OpenAI API key!');
    } catch (error) {
      console.error('Error starting realtime voice:', error);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">AI Multi-Personality Chat</h1>
            <p className="text-blue-100 text-sm">Chat with different AI minds & use voice features</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={startRealtimeVoice}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors duration-200 ${
                realtimeConnected 
                  ? 'bg-green-500 hover:bg-green-600' 
                  : 'bg-red-500 hover:bg-red-600'
              }`}
            >
              {realtimeConnected ? '🎤 Live Voice' : '🎤 Start Voice Chat'}
            </button>
          </div>
        </div>
      </div>

      {/* Personality Selector */}
      <PersonalitySelector 
        personalities={personalities}
        selectedPersonality={selectedPersonality}
        onSelectPersonality={setSelectedPersonality}
      />

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 mt-10">
            <div className={`w-16 h-16 rounded-full bg-${selectedPersonality.avatar_color}-500 flex items-center justify-center text-white font-bold text-xl mx-auto mb-4`}>
              {selectedPersonality.name[0]}
            </div>
            <h3 className="text-lg font-semibold text-gray-700">Chat with {selectedPersonality.name}</h3>
            <p className="text-sm text-gray-600 mt-2">{selectedPersonality.description}</p>
            <div className="flex flex-wrap justify-center gap-2 mt-3">
              {selectedPersonality.personality_traits.map((trait, idx) => (
                <span key={idx} className="text-xs bg-gray-200 text-gray-700 px-3 py-1 rounded-full">
                  {trait}
                </span>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <Message 
              key={index} 
              message={message} 
              personality={selectedPersonality}
            />
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className={`w-10 h-10 rounded-full bg-${selectedPersonality.avatar_color}-500 flex items-center justify-center text-white font-bold mr-3`}>
              {selectedPersonality.name[0]}
            </div>
            <div className="bg-gray-100 rounded-2xl px-4 py-2 border border-gray-200">
              <div className="flex space-x-1">
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
      <div className="border-t bg-white p-4">
        <form onSubmit={sendMessage} className="flex items-center space-x-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder={`Type a message to ${selectedPersonality.name}...`}
              className="w-full px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isLoading}
            />
          </div>
          
          {/* Voice Controls */}
          <VoiceControls
            isRecording={isRecording}
            onStartRecording={startRecording}
            onStopRecording={stopRecording}
            onSendVoice={sendVoiceMessage}
            canSend={!!audioData}
          />
          
          {/* Send Button */}
          <button
            type="submit"
            disabled={!inputMessage.trim() || isLoading}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-full font-medium transition-colors duration-200"
          >
            {isLoading ? (
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            )}
          </button>
        </form>
        
        {isRecording && (
          <div className="mt-2 text-center text-sm text-red-600 animate-pulse">
            🔴 Recording... Click stop when finished
          </div>
        )}
        
        {audioData && !isRecording && (
          <div className="mt-2 text-center text-sm text-green-600">
            ✓ Voice message ready to send
          </div>
        )}
      </div>
    </div>
  );
}

export default App;