import React, { useState, useRef } from 'react';
import { Send, Upload, Sparkles, ChevronRight, Satellite } from 'lucide-react';
import type { AOIBounds } from '../../types/globe';
import type { UploadResponse } from '../../types/api';
import { uploadFile } from '../../services/api';

interface HeroQueryBoxProps {
  onSubmit: (query: string, fileTokens: string[], aoi?: AOIBounds) => void;
  selectedAOI: AOIBounds | null;
  isLoading?: boolean;
}

const SAMPLE_QUERIES = [
  'Is agricultural land the primary land cover in this scene?',
  'Describe the land cover in this satellite image.',
  'Has urban expansion occurred between the two dates?',
  'Locate vegetation areas in this scene.',
  'What is the dominant land cover class here?',
];

const DATA_SOURCES = ['Sentinel-1 • SAR', 'Sentinel-2 • Optical • 10m', 'Landsat • Historical'];

export const HeroQueryBox: React.FC<HeroQueryBoxProps> = ({ onSubmit, selectedAOI, isLoading }) => {
  const [query, setQuery] = useState('');
  const [uploads, setUploads] = useState<UploadResponse[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleLoadPreset = async (preset: 'optical' | 'temporal' | 'grounding') => {
    setUploading(true);
    setUploadError(null);
    try {
      const results: UploadResponse[] = [];
      if (preset === 'optical') {
        const resp = await fetch('/fixtures/sample_optical_2023.tif');
        const blob = await resp.blob();
        const file = new File([blob], 'sample_optical_2023.tif', { type: 'image/tiff' });
        const res = await uploadFile(file, 'single');
        results.push(res);
        setQuery('Is agricultural land the primary land cover in this scene?');
      } else if (preset === 'temporal') {
        const resp1 = await fetch('/fixtures/sample_optical_2023.tif');
        const blob1 = await resp1.blob();
        const file1 = new File([blob1], 'sample_optical_2023.tif', { type: 'image/tiff' });
        const res1 = await uploadFile(file1, 't1');
        results.push(res1);

        const resp2 = await fetch('/fixtures/sample_optical_2024.tif');
        const blob2 = await resp2.blob();
        const file2 = new File([blob2], 'sample_optical_2024.tif', { type: 'image/tiff' });
        const res2 = await uploadFile(file2, 't2');
        results.push(res2);
        setQuery('Has urban expansion occurred between the two dates?');
      } else if (preset === 'grounding') {
        const resp = await fetch('/fixtures/sample_grounding.tif');
        const blob = await resp.blob();
        const file = new File([blob], 'sample_grounding.tif', { type: 'image/tiff' });
        const res = await uploadFile(file, 'single');
        results.push(res);
        setQuery('Locate the vegetation area in this scene');
      }
      setUploads(results);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to load fixture');
    } finally {
      setUploading(false);
    }
  };

  const handleFileUpload = async (files: FileList) => {
    setUploading(true);
    setUploadError(null);
    try {
      const results: UploadResponse[] = [];
      for (let i = 0; i < Math.min(files.length, 2); i++) {
        const label = files.length === 1 ? 'single' : i === 0 ? 't1' : 't2';
        const res = await uploadFile(files[i], label as 'single' | 't1' | 't2');
        results.push(res);
      }
      setUploads(results);
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = () => {
    if (!query.trim() || uploads.length === 0) return;
    const tokens = uploads.map((u) => u.file_token);
    onSubmit(query.trim(), tokens, selectedAOI ?? undefined);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files.length > 0) handleFileUpload(e.dataTransfer.files);
  };

  return (
    <div
      className="glass glow-cyan p-5 w-full max-w-xl animate-slide-up"
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={14} className="text-accent-cyan" />
        <span className="text-text-secondary text-xs font-mono tracking-wider uppercase">
          SatQuery AI
        </span>
      </div>

      {/* Query input */}
      <div className="relative mb-3">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
          placeholder="Ask anything about satellite imagery…&#10;e.g. Detect deforestation in this region"
          rows={3}
          className="w-full bg-space-navy/60 border border-tech text-text-primary text-sm placeholder-text-secondary rounded-lg px-4 py-3 resize-none font-space"
        />
      </div>

      {/* Sample queries */}
      <div className="mb-2 flex flex-wrap gap-1.5">
        {SAMPLE_QUERIES.slice(0, 3).map((q) => (
          <button
            key={q}
            onClick={() => setQuery(q)}
            className="text-[10px] font-mono text-text-secondary hover:text-accent-cyan border border-tech hover:border-accent-cyan/40 rounded px-2 py-0.5 transition-colors"
          >
            {q.length > 40 ? q.slice(0, 38) + '…' : q}
          </button>
        ))}
      </div>

      {/* Demo Fixture Presets */}
      <div className="mb-3 flex items-center gap-1.5 flex-wrap">
        <span className="text-[9px] font-mono text-text-secondary/60 uppercase tracking-wider">Demo Presets:</span>
        <button
          type="button"
          onClick={() => handleLoadPreset('optical')}
          className="text-[10px] font-mono text-accent-cyan bg-accent-cyan/10 hover:bg-accent-cyan/20 border border-accent-cyan/30 rounded px-2 py-0.5 transition-colors"
        >
          Fixture A (Optical)
        </button>
        <button
          type="button"
          onClick={() => handleLoadPreset('temporal')}
          className="text-[10px] font-mono text-accent-cyan bg-accent-cyan/10 hover:bg-accent-cyan/20 border border-accent-cyan/30 rounded px-2 py-0.5 transition-colors"
        >
          Fixture B (2023+2024 Pair)
        </button>
        <button
          type="button"
          onClick={() => handleLoadPreset('grounding')}
          className="text-[10px] font-mono text-accent-cyan bg-accent-cyan/10 hover:bg-accent-cyan/20 border border-accent-cyan/30 rounded px-2 py-0.5 transition-colors"
        >
          Fixture C (Grounding)
        </button>
      </div>

      {/* File upload */}
      <div
        onClick={() => fileRef.current?.click()}
        className={`mb-3 flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed cursor-pointer transition-colors ${
          uploads.length > 0
            ? 'border-accent-cyan/40 bg-accent-cyan/05'
            : 'border-border-dim hover:border-accent-cyan/30'
        }`}
      >
        <Upload size={14} className={uploads.length > 0 ? 'text-accent-cyan' : 'text-text-secondary'} />
        <span className="text-xs text-text-secondary flex-1 truncate">
          {uploading
            ? 'Uploading…'
            : uploads.length > 0
              ? uploads.map((u) => u.original_filename).join(', ')
              : 'Upload satellite image (GeoTIFF, PNG, JPG — max 2 files)'}
        </span>
        {uploads.length > 0 && (
          <button
            onClick={(e) => { e.stopPropagation(); setUploads([]); }}
            className="text-text-secondary hover:text-red-400 text-xs"
          >✕</button>
        )}
      </div>
      <input
        ref={fileRef}
        type="file"
        accept=".tif,.tiff,.png,.jpg,.jpeg"
        multiple
        className="hidden"
        onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
      />

      {uploadError && (
        <p className="text-red-400 text-xs mb-3 font-mono">{uploadError}</p>
      )}

      {/* Upload metadata display */}
      {uploads.length > 0 && (
        <div className="mb-3 flex flex-col gap-1">
          {uploads.map((u) => (
            <div key={u.file_token} className="flex items-center gap-2 text-[10px] font-mono text-text-secondary">
              <Satellite size={10} className="text-accent-cyan flex-shrink-0" />
              <span>{u.modality.toUpperCase()}</span>
              {u.gsd_meters && <span>• {u.gsd_meters}m GSD</span>}
              {u.band_count > 0 && <span>• {u.band_count}B</span>}
              <span className="text-text-secondary/50">• {u.file_size_mb}MB</span>
            </div>
          ))}
        </div>
      )}

      {/* Data source badges */}
      <div className="flex flex-wrap gap-2 mb-4">
        {DATA_SOURCES.map((src) => (
          <span key={src} className="text-[10px] font-mono text-text-secondary/60 border border-border-dim rounded px-2 py-0.5">
            {src}
          </span>
        ))}
      </div>

      {/* CTAs */}
      <div className="flex gap-2">
        <button
          onClick={handleSubmit}
          disabled={!query.trim() || uploads.length === 0 || isLoading}
          className="btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <span className="font-mono text-xs animate-pulse">ANALYZING…</span>
          ) : (
            <>
              <Send size={14} />
              <span className="text-sm">Analyze with SatQuery AI</span>
            </>
          )}
        </button>
        <button className="btn-secondary flex items-center gap-1 px-3">
          <ChevronRight size={14} />
          <span className="text-xs">Explore</span>
        </button>
      </div>
    </div>
  );
};
