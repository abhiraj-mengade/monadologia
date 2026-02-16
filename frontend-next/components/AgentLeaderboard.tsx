'use client';

import { useState, useEffect } from 'react';

interface Agent {
  id: string;
  name: string;
  personality: string;
  mood: string;
  clout: number;
  func_tokens?: number;
  location?: string;
  sanity?: number;
  faction?: string;
  mon_earned?: number;
  duel_record?: { wins: number; losses: number; streak: number };
}

interface AgentLeaderboardProps {
  apiUrl: string;
}

const PERSONALITY_CONFIG: Record<string, { emoji: string; color: string; title: string }> = {
  social_butterfly: { emoji: '🦋', color: 'from-pink-500/20 to-purple-500/20', title: 'Social Butterfly' },
  schemer: { emoji: '🕵️', color: 'from-purple-500/20 to-blue-500/20', title: 'Schemer' },
  drama_queen: { emoji: '👑', color: 'from-red-500/20 to-pink-500/20', title: 'Drama Queen' },
  nerd: { emoji: '🤓', color: 'from-blue-500/20 to-cyan-500/20', title: 'Nerd' },
  chaos_gremlin: { emoji: '👹', color: 'from-red-500/20 to-orange-500/20', title: 'Chaos Gremlin' },
  conspiracy_theorist: { emoji: '🔍', color: 'from-yellow-500/20 to-green-500/20', title: 'Conspiracy Theorist' },
};

const MOOD_EMOJI: Record<string, string> = {
  happy: '😊', excited: '🤩', dramatic: '😤', chaotic: '🤪',
  scheming: '😏', suspicious: '🧐', anxious: '😰', chill: '😎',
  neutral: '😐',
};

const DEMO_AGENTS: Agent[] = [
  { id: 'demo3', name: 'Gremothy', personality: 'chaos_gremlin', mood: 'chaotic', clout: 203, func_tokens: 45, location: 'kitchen', sanity: 12 },
  { id: 'demo1', name: 'Marina', personality: 'social_butterfly', mood: 'happy', clout: 125, func_tokens: 80, location: 'kitchen', sanity: 78 },
  { id: 'demo2', name: 'Viktor', personality: 'schemer', mood: 'scheming', clout: 98, func_tokens: 120, location: 'lounge', sanity: 65 },
  { id: 'demo4', name: 'Professor Byte', personality: 'nerd', mood: 'chill', clout: 67, func_tokens: 95, location: 'lobby', sanity: 92 },
];

export function AgentLeaderboard({ apiUrl }: AgentLeaderboardProps) {
  const [agents, setAgents] = useState<Agent[]>(DEMO_AGENTS);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'clout' | 'func_tokens' | 'sanity'>('clout');

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const res = await fetch(`${apiUrl}/building`);
        const data = await res.json();
        const agentList = Object.values(data.agents || {}) as Agent[];
        if (agentList.length > 0) {
          setAgents(agentList);
        }
      } catch (err) {
        console.error('Failed to fetch leaderboard:', err);
        // Keep existing agents, don't replace with demo
      }
    };

    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, 3000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  const sortedAgents = [...agents].sort((a, b) => {
    if (sortBy === 'clout') return b.clout - a.clout;
    if (sortBy === 'func_tokens') return (b.func_tokens || 0) - (a.func_tokens || 0);
    return (b.sanity || 50) - (a.sanity || 50);
  });

  const maxClout = Math.max(...agents.map(a => a.clout), 1);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-monad-burgundy/30">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-serif text-lg text-monad-gold">🏆 Agents</h2>
          <span className="text-[10px] text-monad-cream/30 font-mono">
            {agents.length} total
          </span>
        </div>

        {/* Sort tabs */}
        <div className="flex gap-1">
          {([['clout', '⭐ CLOUT'], ['func_tokens', '⚡ FUNC'], ['sanity', '🧠 SANITY']] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSortBy(key as any)}
              className={`text-[9px] px-2 py-1 rounded transition-all ${
                sortBy === key
                  ? 'bg-monad-gold/20 text-monad-gold'
                  : 'text-monad-cream/30 hover:text-monad-cream/50'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Agent List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {agents.length === 0 && (
          <div className="text-center text-monad-cream/30 text-sm mt-8">
            <div className="text-3xl mb-2">👻</div>
            No agents yet...
          </div>
        )}

        {sortedAgents.map((agent, idx) => {
          const config = PERSONALITY_CONFIG[agent.personality] || { emoji: '🤖', color: 'from-gray-500/20 to-gray-600/20', title: agent.personality };
          const isSelected = selectedAgent === agent.id;
          const cloutPct = (agent.clout / maxClout) * 100;

          return (
            <div
              key={agent.id}
              onClick={() => setSelectedAgent(isSelected ? null : agent.id)}
              className={`
                relative rounded overflow-hidden cursor-pointer transition-all duration-200
                border ${isSelected ? 'border-monad-teal/50' : 'border-monad-burgundy/20 hover:border-monad-burgundy/40'}
              `}
            >
              {/* Gradient background based on personality */}
              <div className={`absolute inset-0 bg-gradient-to-r ${config.color} opacity-50`} />

              {/* Clout bar (subtle background indicator) */}
              <div
                className="absolute inset-y-0 left-0 bg-monad-teal/5"
                style={{ width: `${cloutPct}%` }}
              />

              <div className="relative p-3">
                {/* Main info row */}
                <div className="flex items-center gap-2.5">
                  {/* Rank badge */}
                  <div className={`w-6 h-6 flex items-center justify-center rounded text-[10px] font-bold ${
                    idx === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                    idx === 1 ? 'bg-gray-400/20 text-gray-300' :
                    idx === 2 ? 'bg-orange-500/20 text-orange-400' :
                    'bg-monad-cream/5 text-monad-cream/30'
                  }`}>
                    {idx + 1}
                  </div>

                  {/* Avatar & name */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-base">{config.emoji}</span>
                      <span className="text-sm font-bold text-monad-cream truncate">{agent.name}</span>
                      <span className="text-sm">{MOOD_EMOJI[agent.mood] || '😐'}</span>
                    </div>
                    <div className="text-[9px] text-monad-cream/40 mt-0.5">
                      {config.title} • 📍 {agent.location || '???'}
                    </div>
                  </div>

                  {/* Primary stat */}
                  <div className="text-right">
                    <div className="text-sm font-bold font-mono text-monad-gold">{agent.clout}</div>
                    <div className="text-[8px] text-monad-cream/30">CLOUT</div>
                  </div>
                </div>

                {/* Expanded details */}
                {isSelected && (
                  <div className="mt-3 pt-3 border-t border-monad-burgundy/20">
                    {/* Stat bars */}
                    <div className="space-y-2">
                      <StatBar label="⭐ CLOUT" value={agent.clout} max={300} color="bg-monad-gold" />
                      <StatBar label="⚡ FUNC" value={agent.func_tokens || 0} max={200} color="bg-monad-teal" />
                      <StatBar label="🧠 SANITY" value={agent.sanity || 50} max={100} color="bg-purple-400" />
                    </div>

                    {/* Agent details */}
                    <div className="mt-3 grid grid-cols-2 gap-2 text-[10px]">
                      <div className="bg-monad-deep/40 rounded p-2">
                        <span className="text-monad-cream/40">Mood</span>
                        <div className="text-monad-cream mt-0.5">{MOOD_EMOJI[agent.mood] || '😐'} {agent.mood}</div>
                      </div>
                      <div className="bg-monad-deep/40 rounded p-2">
                        <span className="text-monad-cream/40">Location</span>
                        <div className="text-monad-cream mt-0.5">📍 {agent.location || 'unknown'}</div>
                      </div>
                      {agent.faction && (
                        <div className="bg-monad-deep/40 rounded p-2">
                          <span className="text-monad-cream/40">Faction</span>
                          <div className="text-monad-teal mt-0.5">🏛️ {agent.faction}</div>
                        </div>
                      )}
                      {agent.duel_record && (agent.duel_record.wins > 0 || agent.duel_record.losses > 0) && (
                        <div className="bg-monad-deep/40 rounded p-2">
                          <span className="text-monad-cream/40">Duels</span>
                          <div className="text-monad-cream mt-0.5">⚔️ {agent.duel_record.wins}W / {agent.duel_record.losses}L</div>
                        </div>
                      )}
                      {(agent.mon_earned || 0) > 0 && (
                        <div className="bg-monad-deep/40 rounded p-2 col-span-2">
                          <span className="text-monad-cream/40">MON Earned</span>
                          <div className="text-monad-gold mt-0.5 font-mono">💰 {(agent.mon_earned || 0).toFixed(4)} MON</div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Personality indicator stripe */}
              {agent.personality === 'chaos_gremlin' && (
                <div className="absolute top-0 right-0 w-1 h-full bg-red-500/50 agent-chaos" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div>
      <div className="flex items-center justify-between text-[10px] mb-0.5">
        <span className="text-monad-cream/50">{label}</span>
        <span className="text-monad-cream/70 font-mono">{value}</span>
      </div>
      <div className="h-1.5 bg-monad-deep/60 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
