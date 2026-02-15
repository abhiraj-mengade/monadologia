'use client';

import { useState, useEffect } from 'react';
import { BuildingView } from '@/components/BuildingView';
import { NarrativeFeed } from '@/components/NarrativeFeed';
import { AgentLeaderboard } from '@/components/AgentLeaderboard';
import { ConnectionModal } from '@/components/ConnectionModal';
import { DocsView } from '@/components/DocsView';
import { MathView } from '@/components/MathView';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type Tab = 'dashboard' | 'docs' | 'math';

export default function Home() {
  const [showConnection, setShowConnection] = useState(false);
  const [mathMode, setMathMode] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Background Image (more visible now with drift animation) */}
      <div 
        className="absolute inset-0 bg-cover bg-center opacity-30 bg-drift"
        style={{
          backgroundImage: 'url(/monadologia-bg.png)',
          backgroundSize: 'cover',
        }}
      />

      {/* Overlay Gradient (lighter) */}
      <div className="absolute inset-0 bg-gradient-to-b from-monad-deep/80 via-monad-deep/85 to-monad-deep/90" />

      {/* Main Content */}
      <div className="relative z-10 h-screen flex flex-col">
        {/* Header */}
        <header className="border-b border-monad-burgundy/50 bg-monad-deep/80 backdrop-blur-sm">
          <div className="container mx-auto px-4 py-4 flex items-center justify-between">
            <div>
              <h1 className="font-serif text-3xl text-monad-gold tracking-wide">
                <span 
                  className="italic"
                  style={{ fontFamily: "'Dancing Script', cursive", fontSize: '2.5rem', fontWeight: 700, letterSpacing: '0.02em' }}
                >
                  LEIBNIZ'S
                </span>{' '}
                <span className="font-serif">MONADOLOGIA</span>
              </h1>
              <p className="text-xs text-monad-teal/70 mt-1">
                Where Mathematical Abstraction Meets Chaotic Social Simulation
              </p>
            </div>

            <div className="flex items-center gap-4">
              {/* Navigation Tabs */}
              <div className="flex gap-1 border border-monad-burgundy/50 rounded overflow-hidden">
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className={`px-4 py-2 text-xs font-bold transition-all ${
                    activeTab === 'dashboard'
                      ? 'bg-monad-teal text-monad-deep'
                      : 'bg-transparent text-monad-cream/60 hover:text-monad-cream'
                  }`}
                >
                  DASHBOARD
                </button>
                <button
                  onClick={() => setActiveTab('docs')}
                  className={`px-4 py-2 text-xs font-bold transition-all ${
                    activeTab === 'docs'
                      ? 'bg-monad-teal text-monad-deep'
                      : 'bg-transparent text-monad-cream/60 hover:text-monad-cream'
                  }`}
                >
                  DOCS
                </button>
                <button
                  onClick={() => setActiveTab('math')}
                  className={`px-4 py-2 text-xs font-bold transition-all ${
                    activeTab === 'math'
                      ? 'bg-monad-teal text-monad-deep'
                      : 'bg-transparent text-monad-cream/60 hover:text-monad-cream'
                  }`}
                >
                  MATH
                </button>
              </div>

              {/* Live Indicator */}
              <div className="flex items-center gap-2 px-3 py-1 border border-monad-teal/30 rounded">
                <div className="w-2 h-2 bg-monad-teal rounded-full pulse" />
                <span className="text-xs text-monad-teal">LIVE</span>
              </div>

              {/* Math Mode Toggle (only on dashboard) */}
              {activeTab === 'dashboard' && (
                <button
                  onClick={() => setMathMode(!mathMode)}
                  className={`px-4 py-2 text-sm font-bold border transition-all ${
                    mathMode
                      ? 'bg-monad-gold text-monad-deep border-monad-gold'
                      : 'bg-transparent text-monad-gold border-monad-gold/50 hover:border-monad-gold'
                  }`}
                >
                  {mathMode ? '🎭 FUN MODE' : '🧮 MATH MODE'}
                </button>
              )}

              {/* Connect Button */}
              <button
                onClick={() => setShowConnection(true)}
                className="px-6 py-2 bg-monad-teal text-monad-deep font-bold text-sm hover:bg-monad-teal/80 transition-all monad-glow"
              >
                JACK IN
              </button>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'dashboard' && (
            <div className="h-full grid grid-cols-[350px_1fr_350px] gap-0">
              {/* Zone C: Agent Leaderboard (Left) */}
              <div className="border-r border-monad-burgundy/50 bg-monad-deep/60 backdrop-blur-sm overflow-y-auto">
                <AgentLeaderboard apiUrl={API_URL} />
              </div>

              {/* Zone A: The Building (Center) */}
              <div className="relative overflow-y-auto">
                <BuildingView apiUrl={API_URL} mathMode={mathMode} />
              </div>

              {/* Zone B: Narrative Feed (Right) */}
              <div className="border-l border-monad-burgundy/50 bg-monad-deep/60 backdrop-blur-sm overflow-y-auto">
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
        <footer className="border-t border-monad-burgundy/50 bg-monad-deep/80 backdrop-blur-sm px-4 py-2 text-center">
          <p className="text-xs text-monad-cream/50">
            🐢 It's monads all the way down. Built for{' '}
            <span className="text-monad-teal">Moltiverse</span>
          </p>
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
