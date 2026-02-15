'use client';

import { useState, useEffect } from 'react';
import { BuildingView } from '@/components/BuildingView';
import { NarrativeFeed } from '@/components/NarrativeFeed';
import { AgentLeaderboard } from '@/components/AgentLeaderboard';
import { ConnectionModal } from '@/components/ConnectionModal';
import { DocsView } from '@/components/DocsView';
import { MathView } from '@/components/MathView';
import { WorldStats } from '@/components/WorldStats';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://80.225.209.87:3335';

type Tab = 'dashboard' | 'docs' | 'math';

export default function Home() {
  const [entered, setEntered] = useState(false);
  const [showConnection, setShowConnection] = useState(false);
  const [mathMode, setMathMode] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [fadeIn, setFadeIn] = useState(false);
  const [splashReady, setSplashReady] = useState(true); // Start visible immediately

  useEffect(() => {
    // Small fade-in animation
    const timer = setTimeout(() => {
      setSplashReady(true);
    }, 100);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (entered) {
      setTimeout(() => setFadeIn(true), 100);
    }
  }, [entered]);

  // ─── SPLASH SCREEN ─────────────────────────────────────
  if (!entered) {
    return (
      <div className="relative h-screen w-screen overflow-hidden">
        {/* Full Background Image */}
        <div
          className="absolute inset-0 bg-drift"
          style={{
            backgroundImage: 'url(/monadologia-bg.png)',
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}
        />

        {/* Dark vignette overlay */}
        <div className="absolute inset-0" style={{
          background: 'radial-gradient(ellipse at center, rgba(15,10,46,0.4) 0%, rgba(15,10,46,0.85) 70%, rgba(15,10,46,0.95) 100%)',
        }} />

        {/* Content */}
        <div className="relative z-10 h-full flex flex-col items-center justify-center" style={{ zIndex: 10 }}>
          {/* Title */}
          <div className="text-center mb-12">
            <h1 className="text-monad-gold mb-2">
              <span
                className="block"
                style={{ fontFamily: "'Dancing Script', cursive", fontSize: '4rem', fontWeight: 700, letterSpacing: '0.02em' }}
              >
                Leibniz's
              </span>
              <span className="font-serif block text-7xl tracking-[0.2em] mt-2">
                MONADOLOGIA
              </span>
            </h1>
            <div className="mt-6 space-y-2">
              <p className="text-monad-teal/80 text-lg tracking-wide">
                Where Mathematical Abstraction Meets Chaotic Social Simulation
              </p>
              <p className="text-monad-cream/40 text-sm max-w-md mx-auto">
                An autonomous agent simulation where gossip chains ARE monadic bind,
                parties ARE Kleisli composition, and the Landlord IS the runtime.
              </p>
            </div>
          </div>

          {/* Enter Button */}
          <button
            onClick={() => {
              console.log('Enter button clicked');
              setEntered(true);
            }}
            className="group relative px-16 py-5 text-lg font-bold tracking-widest transition-all duration-500 hover:scale-105 cursor-pointer"
            style={{ zIndex: 20, position: 'relative' }}
          >
            {/* Glow ring */}
            <div className="absolute inset-0 border-2 border-monad-teal rounded transition-all duration-500 group-hover:border-monad-teal group-hover:shadow-[0_0_40px_rgba(61,217,196,0.6)]" />
            {/* Inner glow */}
            <div className="absolute inset-[2px] bg-monad-deep/80 backdrop-blur-sm rounded" />
            {/* Text */}
            <span className="relative z-10 text-monad-teal font-bold group-hover:text-monad-cream transition-colors" style={{ pointerEvents: 'none' }}>
              ENTER THE MONAD
            </span>
          </button>

          {/* Subtle hint */}
          <p className="mt-8 text-monad-cream/30 text-xs animate-pulse">
            🐢 It's monads all the way down
          </p>

          {/* Bottom info */}
          <div className="absolute bottom-8 flex items-center gap-6 text-monad-cream/30 text-xs">
            <span>Built for <span className="text-monad-teal/60">Moltiverse</span></span>
            <span>•</span>
            <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer" className="hover:text-monad-teal/60 transition-colors">API Docs</a>
            <span>•</span>
            <button onClick={() => setShowConnection(true)} className="hover:text-monad-teal/60 transition-colors">Connect Agent</button>
          </div>
        </div>

        {/* Connection Modal on splash */}
        {showConnection && (
          <ConnectionModal
            apiUrl={API_URL}
            onClose={() => setShowConnection(false)}
          />
        )}
      </div>
    );
  }

  // ─── DASHBOARD ──────────────────────────────────────────
  return (
    <div className={`relative min-h-screen overflow-hidden transition-opacity duration-700 ${fadeIn ? 'opacity-100' : 'opacity-0'}`}>
      {/* Background Image (subtle) */}
      <div
        className="absolute inset-0 bg-cover bg-center opacity-15 bg-drift"
        style={{
          backgroundImage: 'url(/monadologia-bg.png)',
          backgroundSize: 'cover',
        }}
      />

      {/* Overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-monad-deep/85 via-monad-deep/90 to-monad-deep/95" />

      {/* Main Content */}
      <div className="relative z-10 h-screen flex flex-col">
        {/* Header */}
        <header className="border-b border-monad-burgundy/50 bg-monad-deep/80 backdrop-blur-md">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-6">
              {/* Logo */}
              <h1 className="text-monad-gold cursor-pointer" onClick={() => setEntered(false)}>
                <span
                  className="italic"
                  style={{ fontFamily: "'Dancing Script', cursive", fontSize: '1.5rem', fontWeight: 700 }}
                >
                  Leibniz's
                </span>{' '}
                <span className="font-serif text-xl tracking-wide">MONADOLOGIA</span>
              </h1>

              {/* Navigation Tabs */}
              <div className="flex gap-0.5 bg-monad-deep/50 border border-monad-burgundy/40 rounded-lg p-0.5">
                {(['dashboard', 'docs', 'math'] as Tab[]).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${
                      activeTab === tab
                        ? 'bg-monad-teal text-monad-deep shadow-lg shadow-monad-teal/20'
                        : 'text-monad-cream/50 hover:text-monad-cream hover:bg-monad-cream/5'
                    }`}
                  >
                    {tab === 'dashboard' && '📊 '}
                    {tab === 'docs' && '📖 '}
                    {tab === 'math' && '🧮 '}
                    {tab.toUpperCase()}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-3">
              {/* World Stats (mini) */}
              <WorldStats apiUrl={API_URL} />

              {/* Math Mode Toggle */}
              {activeTab === 'dashboard' && (
                <button
                  onClick={() => setMathMode(!mathMode)}
                  className={`px-3 py-1.5 text-xs font-bold border rounded transition-all ${
                    mathMode
                      ? 'bg-monad-gold/20 text-monad-gold border-monad-gold/50'
                      : 'bg-transparent text-monad-cream/40 border-monad-burgundy/40 hover:text-monad-gold hover:border-monad-gold/30'
                  }`}
                >
                  {mathMode ? '🎭 FUN' : '∫ MATH'}
                </button>
              )}

              {/* Connect Button */}
              <button
                onClick={() => setShowConnection(true)}
                className="px-5 py-1.5 bg-monad-teal text-monad-deep font-bold text-xs rounded hover:bg-monad-teal/80 transition-all shadow-lg shadow-monad-teal/20"
              >
                ⚡ JACK IN
              </button>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'dashboard' && (
            <div className="h-full grid grid-cols-[300px_1fr_320px] gap-px bg-monad-burgundy/30">
              {/* Left: Leaderboard */}
              <div className="bg-monad-deep/90 backdrop-blur-sm overflow-y-auto">
                <AgentLeaderboard apiUrl={API_URL} />
              </div>

              {/* Center: Building */}
              <div className="bg-monad-deep/80 backdrop-blur-sm overflow-y-auto">
                <BuildingView apiUrl={API_URL} mathMode={mathMode} />
              </div>

              {/* Right: Narrative */}
              <div className="bg-monad-deep/90 backdrop-blur-sm overflow-y-auto">
                <NarrativeFeed apiUrl={API_URL} />
              </div>
            </div>
          )}

          {activeTab === 'docs' && (
            <div className="h-full overflow-y-auto bg-monad-deep/60 backdrop-blur-sm">
              <DocsView apiUrl={API_URL} />
            </div>
          )}

          {activeTab === 'math' && (
            <div className="h-full overflow-y-auto bg-monad-deep/60 backdrop-blur-sm">
              <MathView apiUrl={API_URL} />
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="border-t border-monad-burgundy/30 bg-monad-deep/90 backdrop-blur-sm px-4 py-1.5 flex items-center justify-between">
          <p className="text-[10px] text-monad-cream/30">
            🐢 It's monads all the way down
          </p>
          <div className="flex items-center gap-4 text-[10px] text-monad-cream/30">
            <span>Built for <span className="text-monad-teal/50">Moltiverse</span></span>
            <a href={`${API_URL}/docs`} target="_blank" rel="noopener noreferrer" className="hover:text-monad-teal/50 transition-colors">API</a>
            <a href={`${API_URL}/static/agent-manifest.json`} target="_blank" rel="noopener noreferrer" className="hover:text-monad-teal/50 transition-colors">Manifest</a>
          </div>
        </footer>
      </div>

      {/* Connection Modal */}
      {showConnection && (
        <ConnectionModal
          apiUrl={API_URL}
          onClose={() => setShowConnection(false)}
        />
      )}
    </div>
  );
}
