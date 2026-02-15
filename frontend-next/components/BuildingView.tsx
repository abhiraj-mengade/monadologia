'use client';

import { useState, useEffect } from 'react';

interface BuildingState {
  tick: number;
  agents: Record<string, any>;
  locations: Record<string, any>;
  active_parties?: Record<string, any>;
  active_gossip?: any[];
  leaderboard?: any[];
}

interface BuildingViewProps {
  apiUrl: string;
  mathMode: boolean;
}

const FLOOR_LAYOUT = [
  { label: 'ROOFTOP — IO Layer', rooms: ['rooftop'] },
  { label: 'FLOOR 3 — Maybe Monad', rooms: ['floor_3_hall', 'floor_3_apt'] },
  { label: 'FLOOR 2 — Either Monad', rooms: ['floor_2_hall', 'floor_2_apt'] },
  { label: 'FLOOR 1 — List Monad', rooms: ['floor_1_hall', 'floor_1_apt'] },
  { label: 'COMMON AREAS — Natural Transformations', rooms: ['kitchen', 'lounge', 'gym', 'courtyard'] },
  { label: 'LOBBY — Identity Monad', rooms: ['lobby'] },
  { label: 'BASEMENT — ⊥ Bottom', rooms: ['basement'] },
];

const ROOM_ICONS: Record<string, string> = {
  rooftop: '🏙️', floor_3_hall: '🚪', floor_3_apt: '🏠',
  floor_2_hall: '🚪', floor_2_apt: '🏠', floor_1_hall: '🚪', floor_1_apt: '🏠',
  kitchen: '🍳', lounge: '🛋️', gym: '💪', courtyard: '🌳',
  lobby: '🏛️', basement: '🕳️',
};

const MONAD_TYPES: Record<string, { type: string; sig: string; color: string }> = {
  rooftop: { type: 'IO', sig: 'IO ()', color: 'text-purple-400' },
  floor_3_hall: { type: 'Maybe', sig: 'Maybe a', color: 'text-yellow-400' },
  floor_3_apt: { type: 'Maybe', sig: 'Maybe a', color: 'text-yellow-400' },
  floor_2_hall: { type: 'Either', sig: 'Either L R', color: 'text-pink-400' },
  floor_2_apt: { type: 'Either', sig: 'Either L R', color: 'text-pink-400' },
  floor_1_hall: { type: 'List', sig: '[a]', color: 'text-cyan-400' },
  floor_1_apt: { type: 'List', sig: '[a]', color: 'text-cyan-400' },
  lobby: { type: 'Identity', sig: 'Identity a', color: 'text-gray-400' },
  kitchen: { type: 'Functor', sig: 'fmap f', color: 'text-orange-400' },
  lounge: { type: 'NatTrans', sig: 'F ~> G', color: 'text-green-400' },
  gym: { type: 'NatTrans', sig: 'F ~> G', color: 'text-green-400' },
  courtyard: { type: 'NatTrans', sig: 'F ~> G', color: 'text-green-400' },
  basement: { type: '⊥', sig: 'undefined', color: 'text-red-400' },
};

const PERSONALITY_EMOJI: Record<string, string> = {
  social_butterfly: '🦋', schemer: '🕵️', drama_queen: '👑',
  nerd: '🤓', chaos_gremlin: '👹', conspiracy_theorist: '🔍',
};

// Demo data
const DEMO_BUILDING: BuildingState = {
  tick: 42,
  agents: {
    'demo1': { id: 'demo1', name: 'Marina', personality: 'social_butterfly', mood: 'happy', location: 'kitchen', clout: 125 },
    'demo2': { id: 'demo2', name: 'Viktor', personality: 'schemer', mood: 'scheming', location: 'lounge', clout: 98 },
    'demo3': { id: 'demo3', name: 'Gremothy', personality: 'chaos_gremlin', mood: 'chaotic', location: 'kitchen', clout: 203 },
    'demo4': { id: 'demo4', name: 'Professor Byte', personality: 'nerd', mood: 'chill', location: 'lobby', clout: 67 },
  },
  locations: {
    rooftop: { name: 'The Rooftop', agents: [] },
    floor_3_hall: { name: 'Floor 3 Hall', agents: [] },
    floor_3_apt: { name: 'Floor 3 Apt', agents: [] },
    floor_2_hall: { name: 'Floor 2 Hall', agents: [] },
    floor_2_apt: { name: 'Floor 2 Apt', agents: [] },
    floor_1_hall: { name: 'Floor 1 Hall', agents: [] },
    floor_1_apt: { name: 'Floor 1 Apt', agents: [] },
    lobby: { name: 'The Lobby', agents: [{ id: 'demo4', name: 'Professor Byte', personality: 'nerd', mood: 'chill' }] },
    kitchen: { name: 'The Kitchen', agents: [
      { id: 'demo1', name: 'Marina', personality: 'social_butterfly', mood: 'happy' },
      { id: 'demo3', name: 'Gremothy', personality: 'chaos_gremlin', mood: 'chaotic' }
    ]},
    lounge: { name: 'The Lounge', agents: [{ id: 'demo2', name: 'Viktor', personality: 'schemer', mood: 'scheming' }] },
    gym: { name: 'The Gym', agents: [] },
    courtyard: { name: 'The Courtyard', agents: [] },
    basement: { name: 'The Basement', agents: [] },
  },
};

export function BuildingView({ apiUrl, mathMode }: BuildingViewProps) {
  const [building, setBuilding] = useState<BuildingState | null>(null);
  const [loading, setLoading] = useState(true);
  const [isOffline, setIsOffline] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState<string | null>(null);

  useEffect(() => {
    const fetchBuilding = async () => {
      try {
        const res = await fetch(`${apiUrl}/building`);
        const data = await res.json();
        setBuilding(data);
        setLoading(false);
        setIsOffline(false);
      } catch {
        if (!building) {
          setBuilding(DEMO_BUILDING);
          setIsOffline(true);
        }
        setLoading(false);
      }
    };

    fetchBuilding();
    const interval = setInterval(fetchBuilding, 3000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  if (loading && !building) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="text-4xl mb-4 animate-bounce">🏢</div>
          <div className="text-monad-teal animate-pulse">Materializing The Monad...</div>
        </div>
      </div>
    );
  }

  if (!building) return null;

  const totalAgents = Object.keys(building.agents).length;

  return (
    <div className="h-full flex flex-col">
      {/* Building Header */}
      <div className="p-4 border-b border-monad-burgundy/30 flex items-center justify-between">
        <div>
          <h2 className="font-serif text-xl text-monad-gold flex items-center gap-2">
            🏢 The Building
            {isOffline && <span className="text-xs text-monad-coral font-mono">(DEMO)</span>}
          </h2>
          <p className="text-[10px] text-monad-cream/40 mt-0.5">
            Tick {building.tick} • {totalAgents} agent{totalAgents !== 1 ? 's' : ''} inside
          </p>
        </div>
        {mathMode && (
          <div className="text-[10px] text-monad-gold/60 font-mono px-2 py-1 border border-monad-gold/20 rounded">
            Category Theory View
          </div>
        )}
      </div>

      {/* Building Visualization */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-3xl mx-auto space-y-1">
          {FLOOR_LAYOUT.map((floor, floorIdx) => (
            <div key={floorIdx}>
              {/* Floor Label */}
              <div className="text-[9px] text-monad-cream/30 font-mono uppercase tracking-widest mb-1 pl-1">
                {mathMode ? floor.label : floor.label.split('—')[0]}
              </div>

              {/* Rooms */}
              <div className={`grid gap-1 mb-3 ${
                floor.rooms.length === 1 ? 'grid-cols-1'
                : floor.rooms.length === 2 ? 'grid-cols-2'
                : 'grid-cols-4'
              }`}>
                {floor.rooms.map((locId) => {
                  const loc = building.locations[locId];
                  const agents = loc?.agents || [];
                  const monad = MONAD_TYPES[locId];
                  const isSelected = selectedRoom === locId;
                  const hasParty = agents.length > 3;
                  const hasActivity = agents.length > 0;

                  return (
                    <div
                      key={locId}
                      onClick={() => setSelectedRoom(isSelected ? null : locId)}
                      className={`
                        relative p-3 rounded cursor-pointer transition-all duration-300 border
                        ${isSelected
                          ? 'border-monad-teal bg-monad-teal/10 shadow-[0_0_20px_rgba(61,217,196,0.15)]'
                          : hasParty
                            ? 'border-monad-gold/40 bg-monad-gold/5'
                            : hasActivity
                              ? 'border-monad-burgundy/40 bg-monad-cream/[0.03] hover:bg-monad-cream/[0.06]'
                              : 'border-monad-burgundy/20 bg-monad-deep/40 hover:bg-monad-cream/[0.02]'
                        }
                      `}
                    >
                      {/* Room header */}
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-1.5">
                          <span className="text-sm">{ROOM_ICONS[locId] || '📦'}</span>
                          <span className={`text-xs font-bold ${hasActivity ? 'text-monad-cream' : 'text-monad-cream/40'}`}>
                            {mathMode ? monad?.type : (loc?.name || locId).replace('The ', '')}
                          </span>
                        </div>
                        {agents.length > 0 && (
                          <span className="text-[10px] bg-monad-teal/20 text-monad-teal px-1.5 py-0.5 rounded-full font-mono">
                            {agents.length}
                          </span>
                        )}
                      </div>

                      {/* Math mode type signature */}
                      {mathMode && monad && (
                        <div className={`text-[10px] font-mono mb-2 ${monad.color}`}>
                          {monad.sig}
                        </div>
                      )}

                      {/* Agents in room */}
                      <div className="space-y-1">
                        {agents.map((agent: any) => (
                          <div
                            key={agent.id}
                            className={`flex items-center gap-1.5 text-[11px] px-1.5 py-1 rounded ${
                              agent.personality === 'chaos_gremlin'
                                ? 'agent-chaos bg-monad-coral/10'
                                : 'bg-monad-cream/[0.04] text-monad-cream/80'
                            }`}
                          >
                            <span>{PERSONALITY_EMOJI[agent.personality] || '🤖'}</span>
                            <span className="font-bold truncate">{agent.name}</span>
                            {isSelected && (
                              <span className="text-[9px] text-monad-cream/40 ml-auto">
                                {agent.mood}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>

                      {agents.length === 0 && (
                        <div className="text-[10px] text-monad-cream/20 italic">
                          {locId === 'basement' ? '👀 dare to explore?' : 'empty'}
                        </div>
                      )}

                      {/* Party indicator */}
                      {hasParty && (
                        <div className="absolute -top-1 -right-1 text-sm animate-bounce">🎉</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Selected Room Details */}
        {selectedRoom && building.locations[selectedRoom] && (
          <div className="max-w-3xl mx-auto mt-4 parchment-terminal p-4 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-serif text-lg text-monad-gold">
                {ROOM_ICONS[selectedRoom]} {building.locations[selectedRoom]?.name || selectedRoom}
              </h3>
              <button
                onClick={() => setSelectedRoom(null)}
                className="text-monad-cream/40 hover:text-monad-coral text-sm"
              >
                ✕
              </button>
            </div>

            {mathMode && MONAD_TYPES[selectedRoom] && (
              <div className={`text-sm font-mono mb-3 ${MONAD_TYPES[selectedRoom].color}`}>
                Type: {MONAD_TYPES[selectedRoom].type} — {MONAD_TYPES[selectedRoom].sig}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              {(building.locations[selectedRoom]?.agents || []).map((agent: any) => (
                <div key={agent.id} className="bg-monad-deep/50 p-3 rounded border border-monad-burgundy/30">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{PERSONALITY_EMOJI[agent.personality] || '🤖'}</span>
                    <div>
                      <div className="text-sm font-bold text-monad-cream">{agent.name}</div>
                      <div className="text-[10px] text-monad-cream/50">{agent.personality?.replace('_', ' ')}</div>
                    </div>
                  </div>
                  <div className="flex gap-3 text-[10px]">
                    <span>Mood: <span className="text-monad-teal">{agent.mood}</span></span>
                    {agent.clout !== undefined && (
                      <span>Clout: <span className="text-monad-gold">{agent.clout}</span></span>
                    )}
                  </div>
                </div>
              ))}

              {(building.locations[selectedRoom]?.agents || []).length === 0 && (
                <div className="col-span-2 text-center text-monad-cream/30 text-sm py-4">
                  No agents here right now
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
