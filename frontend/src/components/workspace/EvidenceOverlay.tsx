import React from 'react';
import type { EvidenceItem } from '../../types/api';
import { ProvenanceBadge } from '../shared/ModeBadge';
import { LimitationNotice } from './LimitationNotice';

interface EvidenceOverlayProps {
  evidence: EvidenceItem[];
  grounding_supported: boolean;
  imageWidth: number;
  imageHeight: number;
  containerWidth: number;
  containerHeight: number;
}

/**
 * Renders bounding boxes from result.evidence[].
 * GUARD: If evidence is empty AND grounding_supported=false, shows LimitationNotice.
 * NEVER creates a bounding box that is not in evidence[].
 */
export const EvidenceOverlay: React.FC<EvidenceOverlayProps> = ({
  evidence,
  grounding_supported,
  imageWidth,
  imageHeight,
  containerWidth,
  containerHeight,
}) => {
  const scaleX = containerWidth / (imageWidth || 500);
  const scaleY = containerHeight / (imageHeight || 500);

  // Guard: No evidence + no grounding → show limitation notice
  if (evidence.length === 0) {
    if (!grounding_supported) {
      return (
        <div className="absolute bottom-2 left-2 right-2">
          <LimitationNotice message="Spatial grounding is unavailable for the selected model." />
        </div>
      );
    }
    return null; // grounding supported but no detections — silent (no fabricated boxes)
  }

  return (
    <>
      {evidence.map((ev) => {
        if (ev.type !== 'bounding_box' || !ev.coordinates) return null;
        const [x1, y1, x2, y2] = ev.coordinates;
        const left = x1 * scaleX;
        const top = y1 * scaleY;
        const width = (x2 - x1) * scaleX;
        const height = (y2 - y1) * scaleY;

        return (
          <div key={ev.id}>
            {/* Bounding box */}
            <div
              className="absolute border-2 border-accent-cyan rounded-sm pointer-events-none animate-fade-in"
              style={{ left, top, width, height, boxShadow: '0 0 8px rgba(0,212,255,0.3)' }}
            />
            {/* Label with provenance */}
            <div
              className="absolute flex items-center gap-1.5 animate-fade-in"
              style={{ left, top: top - 22 }}
            >
              <span className="text-[10px] font-mono text-accent-cyan bg-space-navy/80 px-1.5 py-0.5 rounded truncate max-w-xs">
                {ev.label}
              </span>
              <ProvenanceBadge
                provenance={ev.provenance}
              />
            </div>
          </div>
        );
      })}
    </>
  );
};
