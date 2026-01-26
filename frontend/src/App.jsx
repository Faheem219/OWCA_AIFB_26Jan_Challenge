import { useState } from 'react'
import VoiceProcessor from './components/VoiceProcessor'
import Chat from './components/Chat'
import WebRTCCall from './components/WebRTCCall'
import CulturalDemo from './components/CulturalDemo'
import VocalForLocal from './components/VocalForLocal'
import { CulturalHeader, CulturalButton, LanguageSelector } from './components/CulturalElements'
import './components/VoiceProcessor.css'
import './components/Chat.css'
import './components/WebRTCCall.css'
import './components/CulturalElements.css'
import './components/VocalForLocal.css'

function App() {
  const [activeTab, setActiveTab] = useState('demo')
  const [selectedLanguage, setSelectedLanguage] = useState('hi')

  const tabConfig = {
    'demo': {
      label: 'डेमो / Demo',
      icon: '🎨',
      description: 'Cultural Design System demonstration with Indian elements'
    },
    'vocal': {
      label: 'वोकल फॉर लोकल / Vocal for Local',
      icon: '🏪',
      description: 'Promote local vendors and connect urban-rural markets'
    },
    'chat': {
      label: 'चैट / Chat',
      icon: '💬',
      description: 'Real-time chat with automatic translation powered by AI'
    },
    'voice': {
      label: 'आवाज़ / Voice',
      icon: '🎤',
      description: 'Voice processing powered by Web Speech API and AWS Polly'
    },
    'webrtc': {
      label: 'कॉल / Calls',
      icon: '📞',
      description: 'WebRTC voice and video calls with live translation and recording'
    }
  }

  return (
    <div className="app">
      <CulturalHeader
        title="बहुभाषी मंडी / Multilingual Mandi"
        subtitle="Real-time Communication Platform for Viksit Bharat"
        showFlag={true}
      />

      <header className="app-header">
        <div className="flex justify-center items-center gap-4 mb-6">
          <LanguageSelector
            selectedLanguage={selectedLanguage}
            onLanguageChange={setSelectedLanguage}
            className="language-selector"
          />
        </div>

        <nav className="app-nav">
          {Object.entries(tabConfig).map(([key, config]) => (
            <CulturalButton
              key={key}
              onClick={() => setActiveTab(key)}
              variant={activeTab === key ? 'primary' : 'outline'}
              className={`nav-btn ${activeTab === key ? 'active' : ''}`}
              showPulse={activeTab === key}
            >
              <span className="mr-2">{config.icon}</span>
              {config.label}
            </CulturalButton>
          ))}
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'demo' && <CulturalDemo />}
        {activeTab === 'vocal' && <VocalForLocal language={selectedLanguage} onLanguageChange={setSelectedLanguage} />}
        {activeTab === 'chat' && <Chat selectedLanguage={selectedLanguage} />}
        {activeTab === 'voice' && <VoiceProcessor selectedLanguage={selectedLanguage} />}
        {activeTab === 'webrtc' && <WebRTCCall selectedLanguage={selectedLanguage} />}
      </main>

      <footer className="app-footer">
        <div className="flex items-center justify-center gap-2 mb-2">
          <span className="text-2xl">🇮🇳</span>
          <span className="font-semibold">Viksit Bharat 2047</span>
          <span className="text-2xl">🇮🇳</span>
        </div>
        <p className="text-center">
          {tabConfig[activeTab].description}
        </p>
        <div className="mt-4 text-sm opacity-75">
          <p>Empowering Indian vendors and buyers across linguistic barriers</p>
          <p>सभी भारतीय भाषाओं में व्यापार को सशक्त बनाना</p>
        </div>
      </footer>
    </div>
  )
}

export default App
