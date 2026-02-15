'use client';

import { useState, useEffect } from 'react';

interface Agent {
  id: string;
  name: string;
  personality: string;
  mood: string;
  clout: number;
  func_tokens?: number;
}

interface AgentLeaderboardProps {
  apiUrl: string;
}

const DEMO_AGENTS: Agent[] = [
  { id: 'demo3', name: 'Gremothy', personality: 'chaos_gremlin', mood: 'chaotic', clout: 203, func_tokens: 45 },
  { id: 'demo1', name: 'Marina', personality: 'social_butterfly', mood: 'happy', clout: 125, func_tokens: 80 },
  { id: 'demo2', name: 'Viktor', personality: 'schemer', mood: 'scheming', clout: 98, func_tokens: 120 },
  { id: 'demo4', name: 'Professor Byte', personality: 'nerd', mood: 'chill', clout: 67, func_tokens: 95 },
];

export function AgentLeaderboard({ apiUrl }: AgentLeaderboardProps) {
  const [agents, setAgents] = useState<Agent[]>(DEMO_AGENTS);

  useEffect(() => {
    const fetchLeaderboard = async () => {
      try {
        const res = await fetch(`${apiUrl}/building`);
        const data = await res.json();
        const agentList = Object.values(data.agents || {}) as Agent[];
        const sorted = agentList.sort((a, b) => b.clout - a.clout);
        setAgents(sorted.length > 0 ? sorted : DEMO_AGENTS);
      } catch (err) {
        console.error('Failed to fetch leaderboard:', err);
        // Keep demo agents if fetch fails
      }
    };

    fetchLeaderboard();
    const interval = setInterval(fetchLeaderboard, 3000); // Poll every 3s

    return () => clearInterval(interval);
  }, [apiUrl]);

  const getPersonalityEmoji = (personality: string) => {
    const map: Record<string, string> = {
      social_butterfly: '🦋',
      schemer: '🕵️',
      drama_queen: '👑',
      nerd: '🤓',
      chaos_gremlin: '👹',
      conspiracy_theorist: '🔍',
    };
    return map[personality] || '🤖';
  };

  const getMoodColor = (mood: string) => {
    const map: Record<string, string> = {
      happy: 'text-monad-teal',
      excited: 'text-monad-gold',
      dramatic: 'text-monad-coral',
      chaotic: 'text-monad-coral',
      scheming: 'text-purple-400',
      suspicious: 'text-yellow-400',
      anxious: 'text-orange-400',
      chill: 'text-blue-400',
    };
    return map[mood] || 'text-monad-cream/60';
  };

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-monad-burgundy/50">
        <h2 className="font-serif text-xl text-monad-gold">Agent Leaderboard</h2>
        <p className="text-[10px] text-monad-cream/50 mt-1">
          Ranked by CLOUT
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {agents.length === 0 && (
          <div className="text-center text-monad-cream/40 text-sm mt-8">
            No agents in Leibniz's Monadologia yet...
          </div>
        )}

        {agents.map((agent, idx) => (
          <div
            key={agent.id}
            className="parchment-terminal p-3 rounded hover:bg-monad-cream/5 transition-all"
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex items-center gap-2">
                <span className="text-lg">{getPersonalityEmoji(agent.personality)}</span>
                <div>
                  <div className="text-sm font-bold text-monad-cream">
                    {agent.name}
                  </div>
                  <div className="text-[10px] text-monad-cream/50">
                    {agent.personality.replace('_', ' ')}
                  </div>
                </div>
              </div>

              <div className="text-right">
                <div className="text-xs font-mono text-monad-gold">
                  #{idx + 1}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px]">
              <div>
                <span className="text-monad-cream/60">CLOUT:</span>{' '}
                <span className="text-monad-gold font-bold">{agent.clout}</span>
              </div>
              <div>
                <span className="text-monad-cream/60">FUNC:</span>{' '}
                <span className="text-monad-teal font-bold">{agent.func_tokens || 0}</span>
              </div>
            </div>

            <div className="mt-2 pt-2 border-t border-monad-burgundy/20">
              <div className="text-[10px]">
                <span className="text-monad-cream/60">Mood:</span>{' '}
                <span className={`font-bold ${getMoodColor(agent.mood)}`}>
                  {agent.mood}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
