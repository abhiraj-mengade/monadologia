'use client';

import { useState, useEffect } from 'react';

interface BuildingState {
  tick: number;
  agents: Record<string, any>;
  locations: Record<string, any>;
}

interface BuildingViewProps {
  apiUrl: string;
  mathMode: boolean;
}

const FLOOR_LAYOUT = [
  ['rooftop'],
  ['floor_3_hall', 'floor_3_apt'],
  ['floor_2_hall', 'floor_2_apt'],
  ['floor_1_hall', 'floor_1_apt'],
  ['kitchen', 'lounge', 'gym', 'courtyard'],
  ['lobby'],
  ['basement'],
];

const MONAD_TYPES: Record<string, string> = {
  rooftop: 'IO',
  floor_3_hall: 'Maybe',
  floor_3_apt: 'Maybe',
  floor_2_hall: 'Either',
  floor_2_apt: 'Either',
  floor_1_hall: 'List',
  floor_1_apt: 'List',
  lobby: 'Identity',
  kitchen: 'Functor',
  lounge: 'NatTrans',
  gym: 'NatTrans',
  courtyard: 'NatTrans',
  basement: '⊥ (Bottom)',
};

// Demo data for when backend is offline
const DEMO_BUILDING: BuildingState = {
  tick: 42,
  agents: {
    'demo1': { id: 'demo1', name: 'Marina', personality: 'social_butterfly', mood: 'happy', location: 'kitchen', clout: 125 },
    'demo2': { id: 'demo2', name: 'Viktor', personality: 'schemer', mood: 'scheming', location: 'lounge', clout: 98 },
    'demo3': { id: 'demo3', name: 'Gremothy', personality: 'chaos_gremlin', mood: 'chaotic', location: 'kitchen', clout: 203 },
    'demo4': { id: 'demo4', name: 'Professor Byte', personality: 'nerd', mood: 'chill', location: 'lobby', clout: 67 },
  },
  locations: {
    rooftop: { name: 'The Rooftop (IO Layer)', agents: [] },
    floor_3_hall: { name: 'Floor 3 Hallway (Maybe)', agents: [] },
    floor_3_apt: { name: 'Floor 3 Apartment', agents: [] },
    floor_2_hall: { name: 'Floor 2 Hallway (Either)', agents: [] },
    floor_2_apt: { name: 'Floor 2 Apartment', agents: [] },
    floor_1_hall: { name: 'Floor 1 Hallway (List)', agents: [] },
    floor_1_apt: { name: 'Floor 1 Apartment', agents: [] },
    lobby: { name: 'The Lobby (Identity)', agents: [{ id: 'demo4', name: 'Professor Byte', personality: 'nerd', mood: 'chill' }] },
    kitchen: { name: 'The Kitchen', agents: [
      { id: 'demo1', name: 'Marina', personality: 'social_butterfly', mood: 'happy' },
      { id: 'demo3', name: 'Gremothy', personality: 'chaos_gremlin', mood: 'chaotic' }
    ]},
    lounge: { name: 'The Lounge', agents: [{ id: 'demo2', name: 'Viktor', personality: 'schemer', mood: 'scheming' }] },
    gym: { name: 'The Gym', agents: [] },
    courtyard: { name: 'The Courtyard', agents: [] },
    basement: { name: 'The Basement (⊥)', agents: [] },
  }
};

export function BuildingView({ apiUrl, mathMode }: BuildingViewProps) {
  const [building, setBuilding] = useState<BuildingState | null>(null);
  const [loading, setLoading] = useState(true);
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    const fetchBuilding = async () => {
      try {
        const res = await fetch(`${apiUrl}/building`);
        const data = await res.json();
        setBuilding(data);
        setLoading(false);
        setIsOffline(false);
      } catch (err) {
        console.error('Failed to fetch building state:', err);
        // Use demo data if backend is offline
        if (!building) {
          setBuilding(DEMO_BUILDING);
          setIsOffline(true);
        }
        setLoading(false);
      }
    };

    fetchBuilding();
    const interval = setInterval(fetchBuilding, 3000); // Poll every 3s

    return () => clearInterval(interval);
  }, [apiUrl]);

  if (loading && !building) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-monad-teal animate-pulse">Loading Leibniz's Monadologia...</div>
      </div>
    );
  }

  if (!building) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-monad-coral mb-2">Backend Offline</div>
          <div className="text-xs text-monad-cream/50">Start the server at port 8000</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-4 text-center">
        <h2 className="font-serif text-2xl text-monad-gold">The Building</h2>
        <p className="text-xs text-monad-cream/60 mt-1">
          Tick {building.tick} • {Object.keys(building.agents).length} Agents
          {isOffline && <span className="ml-2 text-monad-coral">(Demo Mode)</span>}
        </p>
      </div>

      <div className="space-y-2 max-w-4xl mx-auto">
        {FLOOR_LAYOUT.map((floor, floorIdx) => (
          <div
            key={floorIdx}
            className={`grid gap-2 ${
              floor.length === 1
                ? 'grid-cols-1'
                : floor.length === 2
                ? 'grid-cols-2'
                : 'grid-cols-4'
            }`}
          >
            {floor.map((locId) => {
              const loc = building.locations[locId];
              const agents = loc?.agents || [];
              const monadType = MONAD_TYPES[locId] || '?';

              // Determine vibe color based on agents
              let vibeClass = '';
              if (agents.length > 3) {
                vibeClass = 'vibe-party';
              } else if (agents.some((a: any) => a.personality === 'drama_queen')) {
                vibeClass = 'vibe-drama';
              } else if (agents.length > 0) {
                vibeClass = 'vibe-chill';
              }

              return (
                <div
                  key={locId}
                  className={`building-cell ${vibeClass} ${
                    mathMode ? 'monad-glow-gold' : ''
                  }`}
                >
                  <div className="font-bold text-monad-teal text-xs mb-1">
                    {mathMode ? monadType : loc?.name || locId}
                  </div>

                  {mathMode && (
                    <div className="text-[10px] text-monad-gold/60 mb-2 font-mono">
                      {locId === 'kitchen' && 'fmap cook'}
                      {locId === 'rooftop' && 'IO ()'}
                      {locId.includes('floor_3') && 'Maybe a'}
                      {locId.includes('floor_2') && 'Either L R'}
                      {locId.includes('floor_1') && '[a]'}
                      {locId === 'lobby' && 'Identity a'}
                      {locId === 'basement' && '⊥'}
                      {['lounge', 'gym', 'courtyard'].includes(locId) && 'F a → G a'}
                    </div>
                  )}

                  <div className="space-y-1">
                    {agents.map((agent: any) => (
                      <div
                        key={agent.id}
                        className={`text-[10px] px-1 py-0.5 rounded ${
                          agent.personality === 'chaos_gremlin'
                            ? 'agent-chaos bg-monad-coral/20'
                            : 'bg-monad-teal/10 text-monad-cream/80'
                        }`}
                        title={`${agent.name} (${agent.personality})`}
                      >
                        {agent.personality === 'social_butterfly' && '🦋'}
                        {agent.personality === 'schemer' && '🕵️'}
                        {agent.personality === 'drama_queen' && '👑'}
                        {agent.personality === 'nerd' && '🤓'}
                        {agent.personality === 'chaos_gremlin' && '👹'}
                        {agent.personality === 'conspiracy_theorist' && '🔍'}
                        {' '}
                        {agent.name}
                      </div>
                    ))}
                  </div>

                  {agents.length === 0 && (
                    <div className="text-[10px] text-monad-cream/30 italic">empty</div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
