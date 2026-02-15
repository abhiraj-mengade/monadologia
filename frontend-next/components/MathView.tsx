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

export function MathView({ apiUrl }: MathViewProps) {
  const [mathData, setMathData] = useState<MathData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMath = async () => {
      try {
        const res = await fetch(`${apiUrl}/math`);
        const data = await res.json();
        setMathData(data);
        setLoading(false);
      } catch (err) {
        console.error('Failed to fetch math data:', err);
        setLoading(false);
      }
    };

    fetchMath();
  }, [apiUrl]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-monad-teal animate-pulse">Loading mathematical structure...</div>
      </div>
    );
  }

  if (!mathData) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-monad-coral">Failed to load math data</div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto p-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="font-serif text-5xl text-monad-gold mb-3">
          {mathData.title}
        </h1>
        <p className="text-xl text-monad-teal/80">
          {mathData.subtitle}
        </p>
      </div>

      {/* Mappings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
        {mathData.mappings.map((mapping, idx) => (
          <div
            key={idx}
            className="parchment-terminal p-6 rounded hover:bg-monad-cream/5 transition-all"
          >
            <div className="flex items-start justify-between gap-4 mb-3">
              <div>
                <h3 className="font-bold text-monad-cream text-lg mb-1">
                  {mapping.game_concept}
                </h3>
                <div className="text-xs text-monad-gold font-mono">
                  {mapping.math_concept}
                </div>
              </div>
            </div>

            <p className="text-sm text-monad-cream/80 mb-3 leading-relaxed">
              {mapping.explanation}
            </p>

            <div className="bg-monad-deep/50 p-3 rounded border border-monad-burgundy/30">
              <pre className="text-xs text-monad-teal font-mono overflow-x-auto">
                {mapping.haskell}
              </pre>
            </div>
          </div>
        ))}
      </div>

      {/* Philosophy Section */}
      <div className="parchment-terminal p-8 rounded-lg monad-glow-gold">
        <h2 className="font-serif text-3xl text-monad-gold mb-6">
          The Philosophy
        </h2>

        <div className="space-y-6">
          <div>
            <h3 className="font-bold text-monad-teal mb-2">Leibniz's Monads</h3>
            <p className="text-monad-cream/80 leading-relaxed">
              {mathData.philosophy.leibniz}
            </p>
          </div>

          <div>
            <h3 className="font-bold text-monad-teal mb-3">The Name Layers</h3>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(mathData.philosophy.name_layers || {}).map(([key, value]) => (
                <div key={key} className="bg-monad-deep/50 p-3 rounded border border-monad-burgundy/30">
                  <div className="text-xs text-monad-gold font-bold mb-1">
                    {key.replace(/_/g, ' ').toUpperCase()}
                  </div>
                  <div className="text-sm text-monad-cream/80">
                    {value as string}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Quote */}
      <div className="mt-8 text-center">
        <p className="text-2xl font-serif text-monad-gold/60 italic">
          🐢 It's monads all the way down.
        </p>
      </div>
    </div>
  );
}
