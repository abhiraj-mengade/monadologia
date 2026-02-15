'use client';

import { useState, useEffect } from 'react';

interface MathMapping {
  game_concept: string;
  math_concept: string;
  explanation: string;
  haskell: string;
}

interface MathData {
  title: string;
  subtitle: string;
  mappings: MathMapping[];
  philosophy: any;
}

interface MathViewProps {
  apiUrl: string;
}

const FALLBACK_MATH: MathData = {
  title: "The Mathematical Structure",
  subtitle: "Category Theory Hidden in Plain Sight",
  mappings: [
    {
      game_concept: "Gossip Chains",
      math_concept: "Monadic Bind (>>=)",
      explanation: "When gossip spreads through agents, each agent transforms the rumor based on their personality. This IS monadic bind — each step unwraps, transforms, and re-wraps the value.",
      haskell: "spreadGossip :: Gossip -> Agent -> Gossip\ngossipChain = rumor >>= agent1 >>= agent2 >>= agent3"
    },
    {
      game_concept: "Party Composition",
      math_concept: "Kleisli Composition (>=>)",
      explanation: "Party vibes chain together: mystery >=> karaoke >=> chaos. Each vibe transforms the party atmosphere. The order MATTERS — this is Kleisli composition of monadic functions.",
      haskell: "partyVibe :: Vibe -> Party -> Party\nepicParty = mystery >=> karaoke >=> chaos"
    },
    {
      game_concept: "Kitchen Cooking",
      math_concept: "Functor (fmap)",
      explanation: "Cooking transforms ingredients into dishes without changing the container. This is fmap — applying a function inside a context.",
      haskell: "cook :: Ingredient -> Dish\nkitchenAction = fmap cook pantry"
    },
    {
      game_concept: "Floor Mechanics",
      math_concept: "Monad Types",
      explanation: "Each floor IS a different monad. Floor 3 is Maybe (things may not exist), Floor 2 is Either (binary choices), Floor 1 is List (many possibilities).",
      haskell: "floor3 :: Maybe Agent\nfloor2 :: Either Error Agent\nfloor1 :: [Agent]"
    },
    {
      game_concept: "Rumors (State)",
      math_concept: "State Monad",
      explanation: "Rumors carry hidden state: credibility, spiciness, mutation count. As they propagate, the state threads through invisibly — this is the State monad.",
      haskell: "type Rumor = State RumorState String\npropagate :: Agent -> Rumor -> Rumor"
    },
    {
      game_concept: "Agent Registration",
      math_concept: "Pure / Return",
      explanation: "When an agent enters the building, they're lifted into the monadic context. This is 'return' — injecting a pure value into the monad.",
      haskell: "enterBuilding :: Agent -> Monad Agent\nenterBuilding = return"
    },
  ],
  philosophy: {
    leibniz: "Leibniz conceived of monads as the fundamental units of reality — simple substances with no windows, yet reflecting the entire universe from their unique perspective. Each agent in our building IS a Leibnizian monad: self-contained, perceiving the world through their personality lens, yet connected through pre-established harmony (the Landlord runtime).",
    name_layers: {
      programming: "Monads in Haskell — the M-word that terrifies juniors",
      philosophy: "Leibniz's Monadology (1714) — windowless mirrors of the universe",
      architecture: "The Monad apartment building — where agents live and drama unfolds",
      math: "Category theory — the abstract structure underlying it all",
    },
    blockchain: "This simulation explores the mathematical foundations of Monad blockchain: parallel execution across monads (floors), state transitions as monadic operations, smart contract composability as Kleisli composition, and consensus mechanisms as runtime enforcement of monad laws. From Leibniz's 1714 philosophy to 21st century distributed systems — it's monads all the way down. 🐢⛓️"
  }
};

export function MathView({ apiUrl }: MathViewProps) {
  const [mathData, setMathData] = useState<MathData>(FALLBACK_MATH);
  const [loading, setLoading] = useState(true);
  const [expandedCard, setExpandedCard] = useState<number | null>(null);

  useEffect(() => {
    const fetchMath = async () => {
      try {
        const res = await fetch(`${apiUrl}/math`);
        const data = await res.json();
        if (data.mappings) {
          setMathData(data);
        }
        setLoading(false);
      } catch {
        setLoading(false);
      }
    };

    fetchMath();
  }, [apiUrl]);

  return (
    <div className="max-w-6xl mx-auto p-8">
      {/* Header */}
      <div className="mb-10 text-center">
        <h1 className="font-serif text-5xl text-monad-gold mb-3">
          🧮 {mathData.title}
        </h1>
        <p className="text-xl text-monad-teal/70">
          {mathData.subtitle}
        </p>
      </div>

      {/* Mappings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
        {mathData.mappings.map((mapping, idx) => {
          const isExpanded = expandedCard === idx;
          return (
            <div
              key={idx}
              onClick={() => setExpandedCard(isExpanded ? null : idx)}
              className={`
                parchment-terminal p-5 rounded-lg cursor-pointer transition-all duration-300
                ${isExpanded ? 'md:col-span-2 shadow-[0_0_30px_rgba(212,175,55,0.1)]' : 'hover:bg-monad-cream/5'}
              `}
            >
              <div className="flex items-start justify-between gap-4 mb-3">
                <div>
                  <h3 className="font-bold text-monad-cream text-lg mb-1">
                    {mapping.game_concept}
                  </h3>
                  <div className="text-xs text-monad-gold font-mono px-2 py-0.5 bg-monad-gold/10 rounded inline-block">
                    {mapping.math_concept}
                  </div>
                </div>
                <span className="text-monad-cream/30 text-xs">
                  {isExpanded ? '▼' : '▶'}
                </span>
              </div>

              <p className={`text-sm text-monad-cream/70 leading-relaxed ${isExpanded ? '' : 'line-clamp-2'}`}>
                {mapping.explanation}
              </p>

              {/* Haskell code - always visible but expanded when clicked */}
              <div className={`mt-3 bg-monad-deep/60 p-3 rounded border border-monad-burgundy/30 ${isExpanded ? '' : 'max-h-12 overflow-hidden'}`}>
                <div className="text-[9px] text-monad-cream/30 uppercase tracking-wide mb-1">Haskell</div>
                <pre className="text-xs text-monad-teal font-mono overflow-x-auto">
                  {mapping.haskell}
                </pre>
              </div>
            </div>
          );
        })}
      </div>

      {/* Philosophy Section */}
      <div className="parchment-terminal p-8 rounded-lg monad-glow-gold mb-8">
        <h2 className="font-serif text-3xl text-monad-gold mb-6">
          📜 The Philosophy
        </h2>

        <div className="space-y-6">
          <div>
            <h3 className="font-bold text-monad-teal mb-3 text-lg">Leibniz's Monads</h3>
            <p className="text-monad-cream/80 leading-relaxed text-sm">
              {mathData.philosophy.leibniz}
            </p>
          </div>

          <div>
            <h3 className="font-bold text-monad-teal mb-3 text-lg">The Name Layers</h3>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(mathData.philosophy.name_layers || {}).map(([key, value]) => (
                <div key={key} className="bg-monad-deep/50 p-4 rounded border border-monad-burgundy/30">
                  <div className="text-xs text-monad-gold font-bold mb-2 uppercase tracking-wider">
                    {key.replace(/_/g, ' ')}
                  </div>
                  <div className="text-sm text-monad-cream/70 leading-relaxed">
                    {value as string}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Blockchain Connection */}
          {mathData.philosophy.blockchain && (
            <div className="pt-6 border-t border-monad-burgundy/30">
              <h3 className="font-bold text-monad-teal mb-3 text-lg flex items-center gap-2">
                ⛓️ The Monad Blockchain Connection
              </h3>
              <p className="text-monad-cream/80 leading-relaxed text-sm">
                {mathData.philosophy.blockchain}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center">
        <p className="text-2xl font-serif text-monad-gold/50 italic">
          🐢 It's monads all the way down.
        </p>
      </div>
    </div>
  );
}
