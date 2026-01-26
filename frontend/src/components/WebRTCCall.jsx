import React, { useState, useRef, useEffect, useCallback } from 'react';
import './WebRTCCall.css';

const WebRTCCall = () => {
  // Call state
  const [callState, setCallState] = useState('idle'); // idle, calling, ringing, connected, ended
  const [callType, setCallType] = useState('voice'); // voice, video
  const [isIncomingCall, setIsIncomingCall] = useState(false);
  const [currentCall, setCurrentCall] = useState(null);
  const [callDuration, setCallDuration] = useState(0);
  
  // Media state
  const [localStream, setLocalStream] = useState(null);
  const [remoteStream, setRemoteStream] = useState(null);
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoEnabled, setIsVideoEnabled] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  
  // Translation state
  const [translationEnabled, setTranslationEnabled] = useState(true);
  const [sourceLanguage, setSourceLanguage] = useState('hi');
  const [targetLanguage, setTargetLanguage] = useState('en');
  const [isListening, setIsListening] = useState(false);
  const [translatedText, setTranslatedText] = useState('');
  
  // Recording state
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  
  // Error and status
  const [error, setError] = useState('');
  const [status, setStatus] = useState('');
  
  // Refs
  const localVideoRef = useRef(null);
  const remoteVideoRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const wsRef = useRef(null);
  const callTimerRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const recognitionRef = useRef(null);
  
  // Mock user data
  const [user] = useState({
    id: 'user123',
    name: 'John Doe',
    language: 'en'
  });
  
  // Supported languages
  const languages = [
    { code: 'hi', name: 'Hindi' },
    { code: 'en', name: 'English' },
    { code: 'ta', name: 'Tamil' },
    { code: 'te', name: 'Telugu' },
    { code: 'bn', name: 'Bengali' },
    { code: 'mr', name: 'Marathi' },
    { code: 'gu', name: 'Gujarati' },
    { code: 'kn', name: 'Kannada' },
    { code: 'ml', name: 'Malayalam' },
    { code: 'pa', name: 'Punjabi' }
  ];
  
  // WebRTC configuration
  const rtcConfiguration = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };
  
  // Initialize WebSocket connection
  useEffect(() => {
    connectWebSocket();
    initializeSpeechRecognition();
    
    return () => {
      cleanup();
    };
  }, []);
  
  // Call timer
  useEffect(() => {
    if (callState === 'connected') {
      callTimerRef.current = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
    } else {
      if (callTimerRef.current) {
        clearInterval(callTimerRef.current);
        callTimerRef.current = null;
      }
      if (callState === 'idle') {
        setCallDuration(0);
      }
    }
    
    return () => {
      if (callTimerRef.current) {
        clearInterval(callTimerRef.current);
      }
    };
  }, [callState]);
  
  // Recording timer
  useEffect(() => {
    if (isRecording) {
      recordingTimerRef.current = setInterval(() => {
        setRecordingDuration(prev => prev + 1);
      }, 1000);
    } else {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
      setRecordingDuration(0);
    }
    
    return () => {
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
    };
  }, [isRecording]);
  
  const connectWebSocket = () => {
    try {
      const wsUrl = `ws://localhost:8000/api/v1/chat/ws?token=mock-jwt-token`;
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        console.log('WebSocket connected for WebRTC');
        setStatus('Connected');
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };
      
      wsRef.current.onclose = () => {
        console.log('WebSocket disconnected');
        setStatus('Disconnected');
        // Attempt to reconnect
        setTimeout(connectWebSocket, 3000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('Connection error');
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setError('Failed to connect');
    }
  };
  
  const initializeSpeechRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = `${sourceLanguage}-IN`;
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          }
        }
        
        if (finalTranscript && translationEnabled && currentCall) {
          translateSpeech(finalTranscript);
        }
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };
      
      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  };
  
  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'call_invitation':
        handleIncomingCall(data);
        break;
      case 'call_answered':
        handleCallAnswered(data);
        break;
      case 'call_ended':
        handleCallEnded(data);
        break;
      case 'webrtc_signal':
        handleWebRTCSignal(data);
        break;
      case 'voice_translation':
        handleVoiceTranslation(data);
        break;
      case 'recording_status':
        handleRecordingStatus(data);
        break;
      default:
        console.log('Unknown WebSocket message:', data.type);
    }
  };
  
  const handleIncomingCall = (data) => {
    setIsIncomingCall(true);
    setCurrentCall({
      call_id: data.call_id,
      caller_id: data.caller_id,
      caller_name: data.caller_name,
      call_type: data.call_type
    });
    setCallType(data.call_type);
    setCallState('ringing');
    setTranslationEnabled(data.enable_translation);
  };
  
  const handleCallAnswered = (data) => {
    if (data.accepted) {
      setCallState('connecting');
      initializePeerConnection();
    } else {
      setCallState('ended');
      setError('Call was rejected');
    }
  };
  
  const handleCallEnded = (data) => {
    setCallState('ended');
    cleanup();
  };
  
  const handleWebRTCSignal = async (data) => {
    if (!peerConnectionRef.current) return;
    
    try {
      switch (data.signal_type) {
        case 'offer':
          await peerConnectionRef.current.setRemoteDescription(data.signal_data);
          const answer = await peerConnectionRef.current.createAnswer();
          await peerConnectionRef.current.setLocalDescription(answer);
          sendSignal('answer', answer);
          break;
        case 'answer':
          await peerConnectionRef.current.setRemoteDescription(data.signal_data);
          break;
        case 'ice_candidate':
          await peerConnectionRef.current.addIceCandidate(data.signal_data);
          break;
      }
    } catch (error) {
      console.error('Error handling WebRTC signal:', error);
      setError('Connection failed');
    }
  };
  
  const handleVoiceTranslation = (data) => {
    setTranslatedText(data.translated_text);
    
    // Play translated audio if available
    if (data.translated_audio_url) {
      const audio = new Audio(data.translated_audio_url);
      audio.play().catch(console.error);
    }
  };
  
  const handleRecordingStatus = (data) => {
    setIsRecording(data.recording_enabled);
  };
  
  const initiateCall = async (calleeId, type = 'voice') => {
    try {
      setCallState('calling');
      setCallType(type);
      setError('');
      
      const response = await fetch('/api/v1/webrtc/calls/initiate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer mock-jwt-token`
        },
        body: JSON.stringify({
          callee_id: calleeId,
          call_type: type,
          enable_translation: translationEnabled
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setCurrentCall({ call_id: result.call_id });
      
      // Initialize peer connection for caller
      await initializePeerConnection();
      
    } catch (error) {
      console.error('Error initiating call:', error);
      setError('Failed to initiate call');
      setCallState('idle');
    }
  };
  
  const answerCall = async (accept) => {
    try {
      const response = await fetch('/api/v1/webrtc/calls/answer', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer mock-jwt-token`
        },
        body: JSON.stringify({
          call_id: currentCall.call_id,
          accept: accept
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      if (accept) {
        setCallState('connecting');
        setIsIncomingCall(false);
        await initializePeerConnection();
      } else {
        setCallState('idle');
        setIsIncomingCall(false);
        setCurrentCall(null);
      }
      
    } catch (error) {
      console.error('Error answering call:', error);
      setError('Failed to answer call');
    }
  };
  
  const endCall = async () => {
    try {
      if (currentCall) {
        await fetch(`/api/v1/webrtc/calls/${currentCall.call_id}/end`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer mock-jwt-token`
          }
        });
      }
      
      setCallState('ended');
      cleanup();
      
    } catch (error) {
      console.error('Error ending call:', error);
      cleanup();
    }
  };
  
  const initializePeerConnection = async () => {
    try {
      // Get user media
      const constraints = {
        audio: true,
        video: callType === 'video'
      };
      
      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      setLocalStream(stream);
      
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream;
      }
      
      // Create peer connection
      peerConnectionRef.current = new RTCPeerConnection(rtcConfiguration);
      
      // Add local stream to peer connection
      stream.getTracks().forEach(track => {
        peerConnectionRef.current.addTrack(track, stream);
      });
      
      // Handle remote stream
      peerConnectionRef.current.ontrack = (event) => {
        const [remoteStream] = event.streams;
        setRemoteStream(remoteStream);
        if (remoteVideoRef.current) {
          remoteVideoRef.current.srcObject = remoteStream;
        }
      };
      
      // Handle ICE candidates
      peerConnectionRef.current.onicecandidate = (event) => {
        if (event.candidate) {
          sendSignal('ice_candidate', event.candidate);
        }
      };
      
      // Handle connection state changes
      peerConnectionRef.current.onconnectionstatechange = () => {
        const state = peerConnectionRef.current.connectionState;
        console.log('Connection state:', state);
        
        if (state === 'connected') {
          setCallState('connected');
          setStatus('Connected');
        } else if (state === 'disconnected' || state === 'failed') {
          setCallState('ended');
          setError('Connection lost');
        }
      };
      
      // Create offer if we're the caller
      if (callState === 'calling') {
        const offer = await peerConnectionRef.current.createOffer();
        await peerConnectionRef.current.setLocalDescription(offer);
        sendSignal('offer', offer);
      }
      
    } catch (error) {
      console.error('Error initializing peer connection:', error);
      setError('Failed to access camera/microphone');
      setCallState('idle');
    }
  };
  
  const sendSignal = async (signalType, signalData) => {
    try {
      if (!currentCall) return;
      
      await fetch(`/api/v1/webrtc/calls/${currentCall.call_id}/signal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer mock-jwt-token`
        },
        body: JSON.stringify({
          call_id: currentCall.call_id,
          signal_type: signalType,
          signal_data: signalData
        })
      });
      
    } catch (error) {
      console.error('Error sending signal:', error);
    }
  };
  
  const toggleMute = () => {
    if (localStream) {
      const audioTrack = localStream.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);
      }
    }
  };
  
  const toggleVideo = () => {
    if (localStream) {
      const videoTrack = localStream.getVideoTracks()[0];
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        setIsVideoEnabled(videoTrack.enabled);
      }
    }
  };
  
  const toggleScreenShare = async () => {
    try {
      if (!isScreenSharing) {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true
        });
        
        // Replace video track with screen share
        const videoTrack = screenStream.getVideoTracks()[0];
        const sender = peerConnectionRef.current.getSenders().find(s => 
          s.track && s.track.kind === 'video'
        );
        
        if (sender) {
          await sender.replaceTrack(videoTrack);
        }
        
        setIsScreenSharing(true);
        
        // Handle screen share end
        videoTrack.onended = () => {
          setIsScreenSharing(false);
          // Switch back to camera
          if (localStream) {
            const cameraTrack = localStream.getVideoTracks()[0];
            if (sender && cameraTrack) {
              sender.replaceTrack(cameraTrack);
            }
          }
        };
        
      } else {
        // Switch back to camera
        if (localStream) {
          const videoTrack = localStream.getVideoTracks()[0];
          const sender = peerConnectionRef.current.getSenders().find(s => 
            s.track && s.track.kind === 'video'
          );
          
          if (sender && videoTrack) {
            await sender.replaceTrack(videoTrack);
          }
        }
        setIsScreenSharing(false);
      }
      
    } catch (error) {
      console.error('Error toggling screen share:', error);
      setError('Screen sharing failed');
    }
  };
  
  const toggleRecording = async () => {
    try {
      if (!currentCall) return;
      
      const response = await fetch('/api/v1/webrtc/calls/record', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer mock-jwt-token`
        },
        body: JSON.stringify({
          call_id: currentCall.call_id,
          enable_recording: !isRecording
        })
      });
      
      if (!response.ok) {
        throw new Error('Failed to toggle recording');
      }
      
      setIsRecording(!isRecording);
      
    } catch (error) {
      console.error('Error toggling recording:', error);
      setError('Recording control failed');
    }
  };
  
  const toggleTranslation = () => {
    setTranslationEnabled(!translationEnabled);
    if (!translationEnabled && recognitionRef.current) {
      recognitionRef.current.start();
      setIsListening(true);
    } else if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };
  
  const translateSpeech = async (text) => {
    try {
      if (!currentCall) return;
      
      // This would typically send the recognized speech text to the backend
      // For now, we'll simulate it
      const response = await fetch('/api/v1/webrtc/calls/translate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer mock-jwt-token`
        },
        body: JSON.stringify({
          call_id: currentCall.call_id,
          audio_data: 'base64_audio_data', // Would be actual audio data
          source_language: sourceLanguage,
          target_language: targetLanguage
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Translation sent:', result);
      }
      
    } catch (error) {
      console.error('Error translating speech:', error);
    }
  };
  
  const cleanup = () => {
    // Stop media streams
    if (localStream) {
      localStream.getTracks().forEach(track => track.stop());
      setLocalStream(null);
    }
    
    if (remoteStream) {
      remoteStream.getTracks().forEach(track => track.stop());
      setRemoteStream(null);
    }
    
    // Close peer connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    
    // Stop speech recognition
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    
    // Clear timers
    if (callTimerRef.current) {
      clearInterval(callTimerRef.current);
      callTimerRef.current = null;
    }
    
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
    
    // Reset state
    setCallState('idle');
    setCurrentCall(null);
    setIsIncomingCall(false);
    setIsMuted(false);
    setIsVideoEnabled(true);
    setIsScreenSharing(false);
    setIsRecording(false);
    setIsListening(false);
    setTranslatedText('');
    setError('');
  };
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };
  
  return (
    <div className="webrtc-call">
      <div className="call-header">
        <h2>Voice & Video Communication</h2>
        <div className="connection-status">
          <span className={`status-indicator ${status === 'Connected' ? 'connected' : 'disconnected'}`}></span>
          {status}
        </div>
      </div>
      
      {/* Call Controls */}
      {callState === 'idle' && (
        <div className="call-setup">
          <div className="call-type-selector">
            <label>
              <input
                type="radio"
                value="voice"
                checked={callType === 'voice'}
                onChange={(e) => setCallType(e.target.value)}
              />
              Voice Call
            </label>
            <label>
              <input
                type="radio"
                value="video"
                checked={callType === 'video'}
                onChange={(e) => setCallType(e.target.value)}
              />
              Video Call
            </label>
          </div>
          
          <div className="translation-settings">
            <label>
              <input
                type="checkbox"
                checked={translationEnabled}
                onChange={toggleTranslation}
              />
              Enable Live Translation
            </label>
            
            {translationEnabled && (
              <div className="language-selectors">
                <select
                  value={sourceLanguage}
                  onChange={(e) => setSourceLanguage(e.target.value)}
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name} (Source)
                    </option>
                  ))}
                </select>
                
                <select
                  value={targetLanguage}
                  onChange={(e) => setTargetLanguage(e.target.value)}
                >
                  {languages.map(lang => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name} (Target)
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
          
          <button
            className="call-button start-call"
            onClick={() => initiateCall('user456', callType)}
          >
            Start {callType === 'video' ? 'Video' : 'Voice'} Call
          </button>
        </div>
      )}
      
      {/* Incoming Call */}
      {isIncomingCall && (
        <div className="incoming-call">
          <div className="caller-info">
            <h3>Incoming {currentCall?.call_type} call</h3>
            <p>From: {currentCall?.caller_name}</p>
          </div>
          <div className="call-actions">
            <button
              className="call-button accept"
              onClick={() => answerCall(true)}
            >
              Accept
            </button>
            <button
              className="call-button reject"
              onClick={() => answerCall(false)}
            >
              Reject
            </button>
          </div>
        </div>
      )}
      
      {/* Active Call */}
      {(callState === 'calling' || callState === 'connecting' || callState === 'connected') && (
        <div className="active-call">
          <div className="call-info">
            <div className="call-status">
              {callState === 'calling' && 'Calling...'}
              {callState === 'connecting' && 'Connecting...'}
              {callState === 'connected' && `Connected - ${formatTime(callDuration)}`}
            </div>
            
            {isRecording && (
              <div className="recording-indicator">
                <span className="recording-dot"></span>
                Recording - {formatTime(recordingDuration)}
              </div>
            )}
          </div>
          
          {/* Video Area */}
          {callType === 'video' && (
            <div className="video-area">
              <div className="remote-video">
                <video
                  ref={remoteVideoRef}
                  autoPlay
                  playsInline
                  className="remote-video-element"
                />
                {!remoteStream && (
                  <div className="video-placeholder">
                    Waiting for remote video...
                  </div>
                )}
              </div>
              
              <div className="local-video">
                <video
                  ref={localVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className="local-video-element"
                />
              </div>
            </div>
          )}
          
          {/* Translation Display */}
          {translationEnabled && translatedText && (
            <div className="translation-display">
              <h4>Translation:</h4>
              <p>{translatedText}</p>
              {isListening && (
                <div className="listening-indicator">
                  <span className="listening-dot"></span>
                  Listening for speech...
                </div>
              )}
            </div>
          )}
          
          {/* Call Controls */}
          <div className="call-controls">
            <button
              className={`control-button ${isMuted ? 'active' : ''}`}
              onClick={toggleMute}
              title={isMuted ? 'Unmute' : 'Mute'}
            >
              🎤
            </button>
            
            {callType === 'video' && (
              <button
                className={`control-button ${!isVideoEnabled ? 'active' : ''}`}
                onClick={toggleVideo}
                title={isVideoEnabled ? 'Turn off video' : 'Turn on video'}
              >
                📹
              </button>
            )}
            
            {callType === 'video' && (
              <button
                className={`control-button ${isScreenSharing ? 'active' : ''}`}
                onClick={toggleScreenShare}
                title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
              >
                🖥️
              </button>
            )}
            
            <button
              className={`control-button ${isRecording ? 'active' : ''}`}
              onClick={toggleRecording}
              title={isRecording ? 'Stop recording' : 'Start recording'}
            >
              ⏺️
            </button>
            
            <button
              className="control-button end-call"
              onClick={endCall}
              title="End call"
            >
              📞
            </button>
          </div>
        </div>
      )}
      
      {/* Call Ended */}
      {callState === 'ended' && (
        <div className="call-ended">
          <h3>Call Ended</h3>
          {callDuration > 0 && (
            <p>Duration: {formatTime(callDuration)}</p>
          )}
          <button
            className="call-button"
            onClick={() => setCallState('idle')}
          >
            Start New Call
          </button>
        </div>
      )}
      
      {/* Error Display */}
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
          <button onClick={() => setError('')}>×</button>
        </div>
      )}
      
      {/* Instructions */}
      <div className="instructions">
        <h4>Features:</h4>
        <ul>
          <li>Voice and video calls with WebRTC</li>
          <li>Live language interpretation during calls</li>
          <li>Screen sharing for product demonstrations</li>
          <li>Call recording and transcription</li>
          <li>Real-time translation of spoken content</li>
        </ul>
      </div>
    </div>
  );
};

export default WebRTCCall;