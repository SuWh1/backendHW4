import React, { useState, useEffect, useRef, useCallback } from 'react';

interface Agent {
  agent_id: string;
  name: string;
  status: 'offline' | 'online' | 'recording' | 'thinking' | 'speaking';
  last_seen: string;
}

interface VoiceMessage {
  type: string;
  data: {
    sender_id?: string;
    receiver_id?: string;
    session_id?: string;
    audio_base64?: string;
    transcribed_text?: string;
    ai_response_text?: string;
    ai_response_audio?: string;
    timestamp: string;
  };
}

interface Session {
  session_id: string;
  initiator_id: string;
  target_id: string;
  status: string;
  started_at: string;
}

const VoiceComm: React.FC = () => {
  const [agentId, setAgentId] = useState<string>('');
  const [agentName, setAgentName] = useState<string>('');
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [agentStatus, setAgentStatus] = useState<string>('offline');
  const [onlineAgents, setOnlineAgents] = useState<Agent[]>([]);
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [volume, setVolume] = useState<number>(1);
  const [isMuted, setIsMuted] = useState<boolean>(false);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize audio context
  useEffect(() => {
    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  // Connect to WebSocket
  const connectWebSocket = useCallback(() => {
    if (!agentId) return;

    const wsUrl = `ws://localhost:8000/ws/${agentId}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setAgentStatus('online');
      
      // Send initial status update
      const message = {
        type: 'status_update',
        data: { status: 'online' }
      };
      wsRef.current?.send(JSON.stringify(message));
    };

    wsRef.current.onmessage = (event) => {
      const message: VoiceMessage = JSON.parse(event.data);
      handleWebSocketMessage(message);
    };

    wsRef.current.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setAgentStatus('offline');
    };

    wsRef.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
  }, [agentId]);

  // Handle WebSocket messages
  const handleWebSocketMessage = (message: VoiceMessage) => {
    console.log('Received message:', message);
    
    switch (message.type) {
      case 'status_update':
        // Update agent status in the list
        setOnlineAgents(prev => 
          prev.map(agent => 
            agent.agent_id === message.data.sender_id 
              ? { ...agent, status: message.data.transcribed_text as any } 
              : agent
          )
        );
        break;

      case 'session_started':
        setCurrentSession(message.data as any);
        console.log('Session started:', message.data);
        break;

      case 'session_ended':
        setCurrentSession(null);
        console.log('Session ended:', message.data);
        break;

      case 'ai_response':
        // Play AI response audio
        if (message.data.ai_response_audio && !isMuted) {
          playAudioFromBase64(message.data.ai_response_audio);
        }
        setMessages(prev => [...prev, message]);
        setAgentStatus('online');
        break;

      case 'voice_message':
        // Handle incoming voice message
        setMessages(prev => [...prev, message]);
        break;

      case 'error':
        console.error('Error from server:', message.data);
        setAgentStatus('online');
        break;
    }
  };

  // Play audio from base64
  const playAudioFromBase64 = async (base64Audio: string) => {
    try {
      const audioData = Uint8Array.from(atob(base64Audio), c => c.charCodeAt(0));
      const audioBuffer = await audioContextRef.current?.decodeAudioData(audioData.buffer);
      
      if (audioBuffer && audioContextRef.current) {
        const source = audioContextRef.current.createBufferSource();
        const gainNode = audioContextRef.current.createGain();
        
        source.buffer = audioBuffer;
        gainNode.gain.value = volume;
        
        source.connect(gainNode);
        gainNode.connect(audioContextRef.current.destination);
        
        source.start();
      }
    } catch (error) {
      console.error('Error playing audio:', error);
    }
  };

  // Start recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          sampleRate: 16000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        } 
      });
      
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      const recordingStartTime = Date.now();

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const recordingDuration = Date.now() - recordingStartTime;
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Check minimum duration (OpenAI requires at least 0.1 seconds)
        if (recordingDuration < 200) { // 200ms minimum for safety
          console.warn('Recording too short, minimum duration is 200ms');
          setAgentStatus('online');
          return;
        }
        
        sendVoiceMessage(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setAgentStatus('recording');
      
      // Update status via WebSocket
      const message = {
        type: 'status_update',
        data: { status: 'recording' }
      };
      wsRef.current?.send(JSON.stringify(message));

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Please allow microphone access to use voice communication');
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      // Stop the stream
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    }
  };

  // Send voice message
  const sendVoiceMessage = async (audioBlob: Blob) => {
    try {
      // Convert to base64
      const arrayBuffer = await audioBlob.arrayBuffer();
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)));

      const message = {
        type: 'voice_message',
        data: {
          audio_base64: base64Audio,
          sender_id: agentId,
          receiver_id: 'ai_agent', // For now, always send to AI
          session_id: currentSession?.session_id || 'default_session',
          timestamp: new Date().toISOString()
        }
      };

      wsRef.current?.send(JSON.stringify(message));
      console.log('Voice message sent');
    } catch (error) {
      console.error('Error sending voice message:', error);
    }
  };

  // Register agent
  const registerAgent = async () => {
    if (!agentId || !agentName) {
      alert('Please enter both Agent ID and Name');
      return;
    }

    try {
      const response = await fetch('http://localhost:8000/agents/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          agent_id: agentId,
          name: agentName
        })
      });

      if (response.ok) {
        connectWebSocket();
      } else {
        // Agent might already exist, try to connect anyway
        connectWebSocket();
      }
    } catch (error) {
      console.error('Error registering agent:', error);
      // Try to connect anyway
      connectWebSocket();
    }
  };

  // Fetch online agents
  const fetchOnlineAgents = async () => {
    try {
      const response = await fetch('http://localhost:8000/agents/online');
      const agents = await response.json();
      setOnlineAgents(agents);
    } catch (error) {
      console.error('Error fetching online agents:', error);
    }
  };

  // Fetch online agents periodically
  useEffect(() => {
    if (isConnected) {
      fetchOnlineAgents();
      const interval = setInterval(fetchOnlineAgents, 5000);
      return () => clearInterval(interval);
    }
  }, [isConnected]);

  // Disconnect
  const disconnect = () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    setIsConnected(false);
    setAgentStatus('offline');
    setCurrentSession(null);
  };

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'text-green-500';
      case 'recording': return 'text-red-500';
      case 'thinking': return 'text-yellow-500';
      case 'speaking': return 'text-blue-500';
      default: return 'text-gray-500';
    }
  };

  // Get status icon
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'recording': return '🎤';
      case 'thinking': return '🤔';
      case 'speaking': return '🔊';
      case 'online': return '🟢';
      default: return '⚫';
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">
          🎙️ A2A Voice Communication System
        </h1>
        <h1 className="text-3xl font-bold mb-8 text-center">
          ❤️‍🔥 BAHA U MENIA NETU VEBKI ❤️‍🔥
        </h1>

        {!isConnected ? (
          <div className="bg-gray-800 rounded-lg p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Connect as Agent</h2>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Agent ID (e.g., agent_001)"
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
                className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
              <input
                type="text"
                placeholder="Agent Name (e.g., Alice)"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
                className="w-full p-3 bg-gray-700 rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
              <button
                onClick={registerAgent}
                className="w-full bg-blue-600 hover:bg-blue-700 p-3 rounded-lg font-semibold transition-colors"
              >
                Connect
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Agent Status */}
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`flex items-center space-x-2 ${getStatusColor(agentStatus)}`}>
                    <span className="text-2xl">{getStatusIcon(agentStatus)}</span>
                    <span className="font-semibold">{agentName} ({agentId})</span>
                  </div>
                  <span className="text-sm text-gray-400">Status: {agentStatus}</span>
                </div>
                
                <div className="flex items-center space-x-4">
                  {/* Volume Control */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setIsMuted(!isMuted)}
                      className={`p-2 rounded ${isMuted ? 'bg-red-600' : 'bg-gray-600'} hover:opacity-80`}
                    >
                      {isMuted ? '🔇' : '🔊'}
                    </button>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.1"
                      value={volume}
                      onChange={(e) => setVolume(parseFloat(e.target.value))}
                      className="w-20"
                      disabled={isMuted}
                    />
                  </div>
                  
                  <button
                    onClick={disconnect}
                    className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg flex items-center space-x-2"
                  >
                    <span>📞</span>
                    <span>Disconnect</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Voice Controls */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Voice Communication</h2>
              <div className="flex justify-center">
                <button
                  onMouseDown={startRecording}
                  onMouseUp={stopRecording}
                  onTouchStart={startRecording}
                  onTouchEnd={stopRecording}
                  className={`w-24 h-24 rounded-full flex items-center justify-center transition-all duration-200 text-4xl ${
                    isRecording 
                      ? 'bg-red-600 scale-110 shadow-lg shadow-red-500/50 animate-pulse' 
                      : 'bg-blue-600 hover:bg-blue-700'
                  }`}
                  disabled={agentStatus === 'thinking'}
                >
                  {isRecording ? '🔴' : '🎤'}
                </button>
              </div>
              <p className="text-center mt-4 text-gray-400">
                {isRecording 
                  ? 'Recording... Release to send' 
                  : agentStatus === 'thinking' 
                    ? 'AI is processing your message...'
                    : 'Hold to record voice message'
                }
              </p>
            </div>

            {/* Online Agents */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4 flex items-center space-x-2">
                <span>👥</span>
                <span>Online Agents ({onlineAgents.length})</span>
              </h2>
              <div className="space-y-2">
                {onlineAgents.length === 0 ? (
                  <p className="text-gray-400 text-center py-4">No other agents online</p>
                ) : (
                  onlineAgents.map((agent) => (
                    <div key={agent.agent_id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`flex items-center space-x-2 ${getStatusColor(agent.status)}`}>
                          <span className="text-xl">{getStatusIcon(agent.status)}</span>
                          <span>{agent.agent_id}</span>
                        </div>
                      </div>
                      <span className="text-sm text-gray-400">{agent.status}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Message History */}
            <div className="bg-gray-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold mb-4">Message History</h2>
              <div className="space-y-3 max-h-60 overflow-y-auto">
                {messages.length === 0 ? (
                  <p className="text-gray-400 text-center py-4">No messages yet</p>
                ) : (
                  messages.slice(-10).map((message, index) => (
                    <div key={index} className="p-3 bg-gray-700 rounded-lg">
                      <div className="flex justify-between text-sm text-gray-400 mb-2">
                        <span>{message.type}</span>
                        <span>{new Date(message.data.timestamp).toLocaleTimeString()}</span>
                      </div>
                      {message.data.transcribed_text && (
                        <p className="text-blue-300 mb-1">
                          <strong>You:</strong> {message.data.transcribed_text}
                        </p>
                      )}
                      {message.data.ai_response_text && (
                        <p className="text-green-300">
                          <strong>AI:</strong> {message.data.ai_response_text}
                        </p>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VoiceComm; 