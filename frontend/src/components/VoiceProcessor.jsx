import React, { useState, useRef, useEffect } from 'react';

const VoiceProcessor = () => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSupported, setIsSupported] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState('hi-IN');
  const [audioUrl, setAudioUrl] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  
  const recognitionRef = useRef(null);
  const audioRef = useRef(null);

  // Supported languages for Web Speech API
  const supportedLanguages = [
    { code: 'hi-IN', name: 'Hindi (India)', lang: 'hi' },
    { code: 'en-IN', name: 'English (India)', lang: 'en' },
    { code: 'ta-IN', name: 'Tamil (India)', lang: 'ta' },
    { code: 'te-IN', name: 'Telugu (India)', lang: 'te' },
    { code: 'bn-IN', name: 'Bengali (India)', lang: 'bn' },
    { code: 'mr-IN', name: 'Marathi (India)', lang: 'mr' },
    { code: 'gu-IN', name: 'Gujarati (India)', lang: 'gu' },
    { code: 'kn-IN', name: 'Kannada (India)', lang: 'kn' },
    { code: 'ml-IN', name: 'Malayalam (India)', lang: 'ml' },
    { code: 'pa-IN', name: 'Punjabi (India)', lang: 'pa' }
  ];

  useEffect(() => {
    // Check if Web Speech API is supported
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      setIsSupported(true);
      
      // Initialize speech recognition
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;
      recognitionRef.current.lang = selectedLanguage;
      
      recognitionRef.current.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }
        
        setTranscript(finalTranscript + interimTranscript);
      };
      
      recognitionRef.current.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setError(`Speech recognition error: ${event.error}`);
        setIsListening(false);
      };
      
      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    } else {
      setIsSupported(false);
      setError('Web Speech API is not supported in this browser');
    }
    
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [selectedLanguage]);

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      setTranscript('');
      setError('');
      recognitionRef.current.lang = selectedLanguage;
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  const convertToSpeech = async () => {
    if (!transcript.trim()) {
      setError('No text to convert to speech');
      return;
    }

    setIsProcessing(true);
    setError('');
    
    try {
      // Get the language code for the backend API
      const selectedLang = supportedLanguages.find(lang => lang.code === selectedLanguage);
      const languageCode = selectedLang ? selectedLang.lang : 'hi';
      
      const response = await fetch('/api/v1/voice/text-to-speech', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}` // Assuming token is stored in localStorage
        },
        body: JSON.stringify({
          text: transcript,
          language: languageCode,
          voice_type: 'standard',
          audio_format: 'mp3'
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setAudioUrl(result.audio_url);
      
    } catch (error) {
      console.error('Text-to-speech error:', error);
      setError(`Text-to-speech conversion failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const playAudio = () => {
    if (audioRef.current && audioUrl) {
      audioRef.current.play();
    }
  };

  const clearTranscript = () => {
    setTranscript('');
    setAudioUrl('');
    setError('');
  };

  if (!isSupported) {
    return (
      <div className="voice-processor error">
        <h3>Voice Processing</h3>
        <p className="error-message">
          Web Speech API is not supported in this browser. 
          Please use Chrome, Edge, or Safari for voice features.
        </p>
      </div>
    );
  }

  return (
    <div className="voice-processor">
      <h3>Voice Processing Demo</h3>
      
      {/* Language Selection */}
      <div className="language-selector">
        <label htmlFor="language-select">Select Language:</label>
        <select 
          id="language-select"
          value={selectedLanguage} 
          onChange={(e) => setSelectedLanguage(e.target.value)}
          disabled={isListening}
        >
          {supportedLanguages.map(lang => (
            <option key={lang.code} value={lang.code}>
              {lang.name}
            </option>
          ))}
        </select>
      </div>

      {/* Speech Recognition Controls */}
      <div className="speech-controls">
        <button 
          onClick={startListening} 
          disabled={isListening || isProcessing}
          className={`btn ${isListening ? 'btn-danger' : 'btn-primary'}`}
        >
          {isListening ? 'Listening...' : 'Start Speaking'}
        </button>
        
        <button 
          onClick={stopListening} 
          disabled={!isListening}
          className="btn btn-secondary"
        >
          Stop
        </button>
        
        <button 
          onClick={clearTranscript}
          disabled={isListening || isProcessing}
          className="btn btn-outline"
        >
          Clear
        </button>
      </div>

      {/* Status Indicator */}
      {isListening && (
        <div className="status-indicator">
          <div className="listening-animation"></div>
          <span>Listening... Speak now</span>
        </div>
      )}

      {/* Transcript Display */}
      <div className="transcript-section">
        <label htmlFor="transcript">Recognized Text:</label>
        <textarea
          id="transcript"
          value={transcript}
          onChange={(e) => setTranscript(e.target.value)}
          placeholder="Your speech will appear here..."
          rows="4"
          disabled={isListening}
        />
      </div>

      {/* Text-to-Speech Controls */}
      <div className="tts-controls">
        <button 
          onClick={convertToSpeech}
          disabled={!transcript.trim() || isProcessing || isListening}
          className="btn btn-success"
        >
          {isProcessing ? 'Converting...' : 'Convert to Speech'}
        </button>
        
        {audioUrl && (
          <button 
            onClick={playAudio}
            disabled={isProcessing}
            className="btn btn-info"
          >
            Play Audio
          </button>
        )}
      </div>

      {/* Audio Player */}
      {audioUrl && (
        <div className="audio-player">
          <audio 
            ref={audioRef}
            controls 
            src={audioUrl}
            onError={(e) => setError('Audio playback failed')}
          >
            Your browser does not support the audio element.
          </audio>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Instructions */}
      <div className="instructions">
        <h4>How to use:</h4>
        <ol>
          <li>Select your preferred language</li>
          <li>Click "Start Speaking" and speak clearly</li>
          <li>Click "Stop" when finished</li>
          <li>Review the recognized text</li>
          <li>Click "Convert to Speech" to generate audio</li>
          <li>Play the generated audio</li>
        </ol>
      </div>
    </div>
  );
};

export default VoiceProcessor;