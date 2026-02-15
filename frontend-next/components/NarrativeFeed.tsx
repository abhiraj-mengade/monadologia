'use client';

import { useState, useEffect, useRef } from 'react';

interface Story {
  tick: number;
  type: string;
  narration: string;
  raw?: any;
}

interface NarrativeFeedProps {
  apiUrl: string;
}

const TYPE_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
  agent_entered: { icon: '🚪', color: 'border-l-emerald-400', label: 'ENTER' },
  move: { icon: '🚶', color: 'border-l-blue-400', label: 'MOVE' },
  gossip_start: { icon: '🗣️', color: 'border-l-pink-400', label: 'GOSSIP' },
  gossip_spread: { icon: '🔄', color: 'border-l-purple-400', label: 'SPREAD' },
  party: { icon: '🎉', color: 'border-l-yellow-400', label: 'PARTY' },
  party_join: { icon: '🕺', color: 'border-l-yellow-300', label: 'JOIN' },
  cook: { icon: '🍳', color: 'border-l-orange-400', label: 'COOK' },
  prank: { icon: '😈', color: 'border-l-red-400', label: 'PRANK' },
  talk: { icon: '💬', color: 'border-l-cyan-400', label: 'TALK' },
  board: { icon: '📋', color: 'border-l-gray-400', label: 'BOARD' },
};

const DEMO_STORIES: Story[] = [
  {
    tick: 35,
    type: 'agent_entered',
    narration: '🚪 Marina (social butterfly) has entered Leibniz\'s Monadologia. There is no escape function.',
  },
  {
    tick: 36,
    type: 'move',
    narration: '🚶 Marina wandered into the kitchen. The functorial mapping begins — every room transforms her.',
  },
  {
    tick: 37,
    type: 'agent_entered',
    narration: '🚪 Viktor (schemer) has entered Leibniz\'s Monadologia. The building grows more suspicious.',
  },
  {
    tick: 38,
    type: 'gossip_start',
    narration: '🗣️ Marina started a rumor: "I heard someone in the basement at 3 AM." The gossip monad binds...',
  },
  {
    tick: 39,
    type: 'cook',
    narration: '🍳 Gremothy attempted to cook a "mystery stew." The kitchen functors tremble.',
  },
  {
    tick: 40,
    type: 'agent_entered',
    narration: '🚪 Gremothy (chaos gremlin) has entered Leibniz\'s Monadologia. EVERYONE PANIC.',
  },
  {
    tick: 41,
    type: 'prank',
    narration: '😈 Gremothy pranked Viktor with "a bucket of lambda calculus." Pure chaotic evil.',
  },
  {
    tick: 42,
    type: 'party',
    narration: '🎉 Gremothy threw a party on the rooftop! Vibes: mystery >=> karaoke >=> chaos. LEGENDARY.',
  },
];

export function NarrativeFeed({ apiUrl }: NarrativeFeedProps) {
  const [stories, setStories] = useState<Story[]>(DEMO_STORIES);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const [filter, setFilter] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchStories = async () => {
      try {
        const res = await fetch(`${apiUrl}/stories?limit=50`);
        const data = await res.json();
        if (data.stories && data.stories.length > 0) {
          setStories(data.stories);
        }
      } catch {
        // Keep demo stories
      }
    };

    fetchStories();
    const interval = setInterval(fetchStories, 2000);
    return () => clearInterval(interval);
  }, [apiUrl]);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [stories, autoScroll]);

  const filteredStories = filter
    ? stories.filter(s => s.type === filter)
    : stories;

  const eventTypes = [...new Set(stories.map(s => s.type))];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-monad-burgundy/30">
        <div className="flex items-center justify-between mb-2">
          <h2 className="font-serif text-lg text-monad-gold">📜 Narrative</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              className={`text-[10px] px-2 py-0.5 rounded border transition-all ${
                autoScroll
                  ? 'border-monad-teal/40 text-monad-teal bg-monad-teal/10'
                  : 'border-monad-burgundy/30 text-monad-cream/30'
              }`}
            >
              {autoScroll ? '⬇️ AUTO' : '⏸ PAUSED'}
            </button>
            <span className="text-[10px] text-monad-cream/30 font-mono">
              {stories.length} events
            </span>
          </div>
        </div>

        {/* Filter chips */}
        <div className="flex flex-wrap gap-1">
          <button
            onClick={() => setFilter(null)}
            className={`text-[9px] px-2 py-0.5 rounded-full transition-all ${
              !filter ? 'bg-monad-teal/20 text-monad-teal' : 'text-monad-cream/30 hover:text-monad-cream/50'
            }`}
          >
            ALL
          </button>
          {eventTypes.map(type => {
            const config = TYPE_CONFIG[type] || { icon: '❓', label: type };
            return (
              <button
                key={type}
                onClick={() => setFilter(filter === type ? null : type)}
                className={`text-[9px] px-2 py-0.5 rounded-full transition-all ${
                  filter === type ? 'bg-monad-teal/20 text-monad-teal' : 'text-monad-cream/30 hover:text-monad-cream/50'
                }`}
              >
                {config.icon} {config.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Stories */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2">
        {filteredStories.length === 0 && (
          <div className="text-center text-monad-cream/30 text-sm mt-8">
            <div className="text-3xl mb-2">🕰️</div>
            Waiting for agents to create chaos...
          </div>
        )}

        {filteredStories.map((story, idx) => {
          const config = TYPE_CONFIG[story.type] || { icon: '❓', color: 'border-l-gray-500', label: story.type };
          const isExpanded = expandedIdx === idx;

          return (
            <div
              key={`${story.tick}-${idx}`}
              className={`
                border-l-2 ${config.color}
                p-2.5 rounded-r cursor-pointer transition-all duration-200
                bg-monad-cream/[0.02] hover:bg-monad-cream/[0.05]
                ${isExpanded ? 'bg-monad-cream/[0.06]' : ''}
              `}
              onClick={() => setExpandedIdx(isExpanded ? null : idx)}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-[10px] text-monad-teal/50 font-mono">
                  T{story.tick}
                </span>
                <span className="text-[9px] px-1.5 py-0.5 bg-monad-burgundy/20 text-monad-cream/40 rounded font-mono">
                  {config.icon} {config.label}
                </span>
              </div>

              <p className="text-xs text-monad-cream/80 leading-relaxed">
                {story.narration}
              </p>

              {isExpanded && story.raw && (
                <div className="mt-2 pt-2 border-t border-monad-burgundy/20">
                  <pre className="text-[9px] text-monad-teal/60 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(story.raw, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
