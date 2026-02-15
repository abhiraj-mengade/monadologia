'use client';

import { useState, useEffect } from 'react';

interface WorldStatsProps {
  apiUrl: string;
}

export function WorldStats({ apiUrl }: WorldStatsProps) {
  const [stats, setStats] = useState({ tick: 0, agents: 0, gossip: 0, online: false });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${apiUrl}/`);
        const data = await res.json();
        setStats({
          tick: data.current_state?.tick || 0,
          agents: data.current_state?.agents || 0,
          gossip: data.current_state?.active_gossip || 0,
          online: true,
        });
      } catch {
        setStats(prev => ({ ...prev, online: false }));
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  return (
    <div className="flex items-center gap-3 text-[11px]">
      {/* Online indicator */}
      <div className="flex items-center gap-1.5">
        <div className={`w-1.5 h-1.5 rounded-full ${stats.online ? 'bg-emerald-400 pulse' : 'bg-red-400'}`} />
        <span className={stats.online ? 'text-emerald-400' : 'text-red-400'}>
          {stats.online ? 'LIVE' : 'OFFLINE'}
        </span>
      </div>

      {/* Stats */}
      <div className="flex items-center gap-2 px-2 py-1 bg-monad-deep/50 border border-monad-burgundy/30 rounded">
        <span className="text-monad-cream/40">TICK</span>
        <span className="text-monad-teal font-bold font-mono">{stats.tick}</span>
        <span className="text-monad-burgundy/50">|</span>
        <span className="text-monad-cream/40">👥</span>
        <span className="text-monad-gold font-bold font-mono">{stats.agents}</span>
        <span className="text-monad-burgundy/50">|</span>
        <span className="text-monad-cream/40">💬</span>
        <span className="text-monad-coral font-bold font-mono">{stats.gossip}</span>
      </div>
    </div>
  );
}
