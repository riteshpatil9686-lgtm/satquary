import React from 'react';
import { GlobeScene } from './GlobeScene';
import { HeroQueryBox } from './HeroQueryBox';
import { Header } from '../shared/Header';
import type { AOIBounds } from '../../types/globe';

interface LandingPageProps {
  onAnalyze: (query: string, fileTokens: string[], aoi?: AOIBounds) => void;
  isLoading?: boolean;
}

export const LandingPage: React.FC<LandingPageProps> = ({ onAnalyze, isLoading }) => {
  const [selectedAOI] = React.useState<AOIBounds | null>(null);

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-space-black grid-overlay">
      {/* Fixed header */}
      <Header />

      {/* 3D Globe — fills entire viewport */}
      <GlobeScene selectedAOI={selectedAOI} />

      {/* Hero overlay content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none pt-16">
        {/* Tagline */}
        <div className="pointer-events-none text-center mb-8 animate-fade-in">
          <div className="flex items-center justify-center gap-2 mb-3">
            <div className="h-px w-12 bg-gradient-to-r from-transparent to-accent-cyan/40" />
            <span className="text-accent-cyan/60 text-xs font-mono tracking-widest uppercase">
              Earth Observation Intelligence
            </span>
            <div className="h-px w-12 bg-gradient-to-l from-transparent to-accent-cyan/40" />
          </div>
          <h1 className="text-4xl md:text-5xl font-bold text-text-primary leading-tight">
            Ask Earth.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-cyan to-accent-blue text-glow-cyan">
              Get Intelligence.
            </span>
          </h1>
          <p className="mt-3 text-text-secondary text-sm max-w-md mx-auto">
            Natural language → AI reasoning → Satellite data → Visual Earth Intelligence
          </p>
        </div>

        {/* Query box — pointer events enabled */}
        <div className="pointer-events-auto w-full max-w-xl px-4">
          <HeroQueryBox
            onSubmit={onAnalyze}
            selectedAOI={selectedAOI}
            isLoading={isLoading}
          />
        </div>

        {/* Bottom decorative coordinate readout */}
        <div className="pointer-events-none mt-6 flex items-center gap-4 text-[10px] font-mono text-text-secondary/40 animate-fade-in">
          <span>LAT 20.5937° N</span>
          <span>·</span>
          <span>LNG 78.9629° E</span>
          <span>·</span>
          <span>ALT 705 KM</span>
          <span>·</span>
          <span>Sentinel-2A</span>
        </div>
      </div>
    </div>
  );
};
