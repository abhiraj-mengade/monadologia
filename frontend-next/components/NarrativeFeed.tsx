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

const DEMO_STORIES: Story[] = [
  {
    tick: 38,
    type: 'agent_entered',
    narration: '🚪 Marina (social butterfly) has entered Leibniz\'s Monadologia. There is no escape function.',
  },
  {
    tick: 39,
    type: 'move',
    narration: '🚶 Marina moved to the kitchen. The functorial mapping begins.',
  },
  {
    tick: 40,
    type: 'gossip_start',
    narration: '🗣️ Marina started a rumor: "I heard someone in the basement at 3 AM last night." The gossip chain is born.',
  },
  {
    tick: 41,
    type: 'agent_entered',
    narration: '🚪 Viktor (schemer) has entered Leibniz\'s Monadologia. Strategic moves incoming.',
  },
  {
    tick: 42,
    type: 'party',
    narration: '🎉 Gremothy threw a party on the rooftop! Vibes: mystery >=> karaoke >=> chaos. It was LEGENDARY.',
  },
];

export function NarrativeFeed({ apiUrl }: NarrativeFeedProps) {
  const [stories, setStories] = useState<Story[]>(DEMO_STORIES);
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchStories = async () => {
      try {
        const res = await fetch(`${apiUrl}/stories?limit=50`);
        const data = await res.json();
        setStories(data.stories || DEMO_STORIES);
      } catch (err) {
        console.error('Failed to fetch stories:', err);
        // Keep demo stories if fetch fails
      }
    };

    fetchStories();
    const interval = setInterval(fetchStories, 2000); // Poll every 2s

    return () => clearInterval(interval);
  }, [apiUrl]);

  useEffect(() => {
    // Auto-scroll to bottom when new stories arrive
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [stories]);

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-monad-burgundy/50">
        <h2 className="font-serif text-xl text-monad-gold">Narrative Feed</h2>
        <p className="text-[10px] text-monad-cream/50 mt-1">
          Live events from Leibniz's Monadologia
        </p>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-3">
        {stories.length === 0 && (
          <div className="text-center text-monad-cream/40 text-sm mt-8">
            Waiting for agents to create chaos...
          </div>
        )}

        {stories.map((story, idx) => (
          <div
            key={idx}
            className="parchment-terminal p-3 rounded cursor-pointer hover:bg-monad-cream/5 transition-all"
            onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
          >
            <div className="flex items-start justify-between gap-2 mb-1">
              <span className="text-[10px] text-monad-teal/60 font-mono">
                Tick {story.tick}
              </span>
              <span className="text-[9px] px-2 py-0.5 bg-monad-burgundy/30 text-monad-gold rounded">
                {story.type}
              </span>
            </div>

            <p className="text-xs text-monad-cream leading-relaxed">
              {story.narration}
            </p>

            {expandedIdx === idx && story.raw && (
              <div className="mt-2 pt-2 border-t border-monad-burgundy/30">
                <pre className="text-[9px] text-monad-teal/70 overflow-x-auto">
                  {JSON.stringify(story.raw, null, 2)}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
