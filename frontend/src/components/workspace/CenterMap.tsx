import React, { useEffect, useRef, useState } from 'react';
import type { AnalysisResult } from '../../types/api';
import { EvidenceOverlay } from './EvidenceOverlay';
import { Map } from 'lucide-react';

interface CenterMapProps {
  result: AnalysisResult;
  fileUrl?: string;
}

export const CenterMap: React.FC<CenterMapProps> = ({ result, fileUrl }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [imgDims, setImgDims] = useState({ w: 500, h: 500 });
  const [containerDims, setContainerDims] = useState({ w: 500, h: 500 });

  // Collect all evidence items across subtasks
  const allEvidence = result.subtasks.flatMap((s) => s.evidence);
  const groundingSupported = result.grounding_supported;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => {
      setContainerDims({ w: el.clientWidth, h: el.clientHeight });
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full bg-space-navy rounded-xl overflow-hidden border border-tech"
    >
      {fileUrl ? (
        <img
          ref={imgRef}
          src={fileUrl}
          alt="Satellite imagery"
          className="w-full h-full object-contain"
          onLoad={(e) => {
            const img = e.currentTarget;
            setImgDims({ w: img.naturalWidth, h: img.naturalHeight });
          }}
        />
      ) : (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <Map size={32} className="text-border-dim mx-auto mb-2" />
            <p className="text-text-secondary text-xs">Satellite imagery viewer</p>
            <p className="text-text-secondary/40 text-[10px] mt-1">Upload a GeoTIFF to display imagery</p>
          </div>
        </div>
      )}

      {/* Evidence overlay — gated on backend evidence[] */}
      <EvidenceOverlay
        evidence={allEvidence}
        grounding_supported={groundingSupported}
        imageWidth={imgDims.w}
        imageHeight={imgDims.h}
        containerWidth={containerDims.w}
        containerHeight={containerDims.h}
      />

      {/* Compatibility warning badge */}
      {result.compatibility_status === 'warning' && result.compatibility_message && (
        <div className="absolute top-2 left-2 right-2">
          <div className="flex items-center gap-1.5 px-2 py-1 rounded bg-yellow-500/10 border border-yellow-500/25 text-[10px] font-mono text-yellow-400">
            ⚠ {result.gsd_limitation_note ?? result.compatibility_message}
          </div>
        </div>
      )}

      {/* Corner coordinate decoration */}
      <div className="absolute bottom-2 right-2 coord-readout opacity-40">
        {result.temporal_pair ? 'TEMPORAL PAIR' : 'SINGLE SCENE'}
      </div>
    </div>
  );
};
