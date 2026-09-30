import React, { useState, useMemo, useRef } from 'react';
import { 
  Layers, ZoomIn, ZoomOut, RotateCcw, Eye, EyeOff, 
  MapPin, Shield, Compass, Hospital, Info, Sliders, Waves, Users
} from 'lucide-react';
import { 
  GeoJSONFeatureCollection, ImpactFinding, IsolatedCommunity, GeoJSONFeature 
} from '../types';

interface EventMapProps {
  floodLayer: GeoJSONFeatureCollection | null;
  changeLayer: GeoJSONFeatureCollection | null;
  roadsLayer: GeoJSONFeatureCollection | null;
  bridgesLayer: GeoJSONFeatureCollection | null;
  facilitiesLayer: GeoJSONFeatureCollection | null;
  isolationLayer: IsolatedCommunity[];
  findings: ImpactFinding[];
  onSelectFinding: (finding: ImpactFinding) => void;
}

export const EventMap: React.FC<EventMapProps> = ({
  floodLayer,
  changeLayer,
  roadsLayer,
  bridgesLayer,
  facilitiesLayer,
  isolationLayer,
  findings,
  onSelectFinding,
}) => {
  // Layer visibility toggles
  const [showFlood, setShowFlood] = useState(true);
  const [showChanges, setShowChanges] = useState(false);
  const [showRoads, setShowRoads] = useState(true);
  const [showFacilities, setShowFacilities] = useState(true);
  const [showIsolation, setShowIsolation] = useState(true);
  const [showFindings, setShowFindings] = useState(true);
  
  // Timeline mode: 'POST_EVENT' (Crisis) vs 'PRE_EVENT' (Baseline) vs 'DIFF' (Change)
  const [timelineMode, setTimelineMode] = useState<'POST_EVENT' | 'PRE_EVENT' | 'DIFF'>('POST_EVENT');

  // Zoom & Pan state
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Selected feature inspector
  const [selectedFeature, setSelectedFeature] = useState<any | null>(null);

  // Geographic Bounding Box computation
  const bounds = useMemo(() => {
    // Default bounding box for Sylhet Basin (91.80 to 92.15 Lon, 24.85 to 25.10 Lat)
    return {
      minLon: 91.80,
      maxLon: 92.15,
      minLat: 24.85,
      maxLat: 25.10,
    };
  }, []);

  // Viewport projection: converts [lon, lat] to SVG viewBox coordinates [0..1000, 0..700]
  const project = (lon: number, lat: number): [number, number] => {
    const x = ((lon - bounds.minLon) / (bounds.maxLon - bounds.minLon)) * 960 + 20;
    const y = ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat)) * 660 + 20;
    return [x, y];
  };

  // Convert GeoJSON Polygon coordinates to SVG path string
  const polygonToPath = (coords: any): string => {
    if (!coords || !coords[0]) return '';
    const ring = coords[0];
    return ring
      .map((pt: [number, number], idx: number) => {
        const [x, y] = project(pt[0], pt[1]);
        return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ') + ' Z';
  };

  // Convert GeoJSON LineString coordinates to SVG path string
  const lineToPath = (coords: [number, number][]): string => {
    if (!coords || coords.length < 2) return '';
    return coords
      .map((pt: [number, number], idx: number) => {
        const [x, y] = project(pt[0], pt[1]);
        return `${idx === 0 ? 'M' : 'L'} ${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(' ');
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setOffset({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleResetZoom = () => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
    setSelectedFeature(null);
  };

  return (
    <div className="relative w-full h-[760px] bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex flex-col">
      {/* Top Map Toolbar */}
      <div className="bg-slate-900/90 backdrop-blur border-b border-slate-800 px-4 py-2 flex flex-wrap items-center justify-between gap-3 z-20">
        {/* Timeline Slider / Mode Controls */}
        <div className="flex items-center space-x-1 bg-slate-950 p-1 rounded-md border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setTimelineMode('PRE_EVENT')}
            className={`px-2.5 py-1 rounded transition-colors ${
              timelineMode === 'PRE_EVENT' ? 'bg-slate-800 text-sky-300 font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Pre-Disaster Baseline
          </button>
          <button
            onClick={() => setTimelineMode('POST_EVENT')}
            className={`px-2.5 py-1 rounded transition-colors ${
              timelineMode === 'POST_EVENT' ? 'bg-sky-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Crisis Inundation (Peak)
          </button>
          <button
            onClick={() => setTimelineMode('DIFF')}
            className={`px-2.5 py-1 rounded transition-colors ${
              timelineMode === 'DIFF' ? 'bg-purple-900/80 text-purple-300 font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Bi-Temporal Change
          </button>
        </div>

        {/* Layer Visibility Toggles */}
        <div className="flex items-center space-x-2 text-xs font-mono">
          <button
            onClick={() => setShowFlood(!showFlood)}
            className={`px-2 py-1 rounded border flex items-center gap-1 transition-colors ${
              showFlood ? 'bg-sky-950/80 border-sky-700 text-sky-300' : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}
          >
            <Waves className="w-3.5 h-3.5 text-sky-400" />
            <span>Flood Mask</span>
          </button>

          <button
            onClick={() => setShowRoads(!showRoads)}
            className={`px-2 py-1 rounded border flex items-center gap-1 transition-colors ${
              showRoads ? 'bg-rose-950/80 border-rose-700 text-rose-300' : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}
          >
            <Compass className="w-3.5 h-3.5 text-rose-400" />
            <span>Passability</span>
          </button>

          <button
            onClick={() => setShowFacilities(!showFacilities)}
            className={`px-2 py-1 rounded border flex items-center gap-1 transition-colors ${
              showFacilities ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300' : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}
          >
            <Hospital className="w-3.5 h-3.5 text-emerald-400" />
            <span>Facilities</span>
          </button>

          <button
            onClick={() => setShowIsolation(!showIsolation)}
            className={`px-2 py-1 rounded border flex items-center gap-1 transition-colors ${
              showIsolation ? 'bg-amber-950/80 border-amber-700 text-amber-300' : 'bg-slate-900 border-slate-800 text-slate-500'
            }`}
          >
            <Users className="w-3.5 h-3.5 text-amber-400" />
            <span>Islands</span>
          </button>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setScale((s) => Math.min(s + 0.25, 3.5))}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setScale((s) => Math.max(s - 0.25, 0.75))}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={handleResetZoom}
            className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Interactive Map Canvas */}
      <div 
        className="relative flex-1 cursor-grab active:cursor-grabbing overflow-hidden bg-[#070b14] radar-grid"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          viewBox="0 0 1000 700"
          className="w-full h-full pointer-events-auto"
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.1s ease-out',
          }}
        >
          <defs>
            {/* Flood Inundation Pattern */}
            <pattern id="floodHatch" width="8" height="8" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="8" stroke="#38bdf8" strokeWidth="1.5" strokeOpacity="0.4" />
            </pattern>
            {/* Isolation Amber Hatch */}
            <pattern id="isolationHatch" width="12" height="12" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
              <line x1="0" y1="0" x2="0" y2="12" stroke="#f59e0b" strokeWidth="2" strokeOpacity="0.3" />
            </pattern>
          </defs>

          {/* 1. Base Geographical Grid & River Bed */}
          <g className="opacity-20 stroke-slate-800">
            {Array.from({ length: 10 }).map((_, i) => (
              <line key={`x-${i}`} x1={i * 100} y1={0} x2={i * 100} y2={700} strokeWidth="1" strokeDasharray="4 4" />
            ))}
            {Array.from({ length: 7 }).map((_, i) => (
              <line key={`y-${i}`} x1={0} y1={i * 100} x2={1000} y2={i * 100} strokeWidth="1" strokeDasharray="4 4" />
            ))}
          </g>

          {/* 2. Isolated Community Convex Hulls */}
          {showIsolation && isolationLayer.map((comm) => {
            if (!comm.boundary_polygon) return null;
            const pathData = polygonToPath(comm.boundary_polygon.coordinates);
            return (
              <g 
                key={comm.component_id} 
                onClick={(e) => { e.stopPropagation(); setSelectedFeature({ type: 'ISOLATED_COMMUNITY', data: comm }); }}
                className="cursor-pointer group"
              >
                <path
                  d={pathData}
                  fill="url(#isolationHatch)"
                  stroke="#f59e0b"
                  strokeWidth="2"
                  strokeDasharray="6 3"
                  className="transition-all hover:stroke-amber-300 hover:stroke-width-3"
                />
              </g>
            );
          })}

          {/* 3. Flood Polygons / Temporal Change Polygons */}
          {showFlood && timelineMode === 'POST_EVENT' && floodLayer?.features.map((feat, idx) => {
            const pathData = polygonToPath(feat.geometry.coordinates);
            return (
              <path
                key={`flood-${idx}`}
                d={pathData}
                fill="#0284c7"
                fillOpacity="0.45"
                stroke="#38bdf8"
                strokeWidth="1.2"
                onClick={(e) => { e.stopPropagation(); setSelectedFeature({ type: 'FLOOD_POLYGON', data: feat.properties }); }}
                className="cursor-pointer hover:fill-opacity-70 transition-all"
              />
            );
          })}

          {timelineMode === 'DIFF' && changeLayer?.features.map((feat, idx) => {
            const pathData = polygonToPath(feat.geometry.coordinates);
            const cat = feat.properties.change_category;
            const color = cat === 'NEWLY_FLOODED' ? '#ef4444' : cat === 'PERMANENT_WATER' ? '#0369a1' : '#a855f7';
            return (
              <path
                key={`change-${idx}`}
                d={pathData}
                fill={color}
                fillOpacity="0.5"
                stroke={color}
                strokeWidth="1.2"
                onClick={(e) => { e.stopPropagation(); setSelectedFeature({ type: 'CHANGE_POLYGON', data: feat.properties }); }}
                className="cursor-pointer hover:fill-opacity-80 transition-all"
              />
            );
          })}

          {/* 4. Transport Road Network Lines (Colored by Passability) */}
          {showRoads && roadsLayer?.features.map((road) => {
            const coords = road.geometry.coordinates;
            const pathData = lineToPath(coords);
            const state = road.properties.passability_state;
            const isBridge = road.properties.bridge === 'yes';

            let strokeColor = '#10b981'; // OPEN
            let strokeWidth = 3;
            if (state === 'BLOCKED') {
              strokeColor = '#ef4444'; // Red Blocked
              strokeWidth = isBridge ? 5 : 3.5;
            } else if (state === 'LIKELY_BLOCKED' || state === 'PARTIALLY_AFFECTED') {
              strokeColor = '#f59e0b'; // Amber Affected
              strokeWidth = 3;
            }

            return (
              <g 
                key={road.id || road.properties.id} 
                onClick={(e) => { e.stopPropagation(); setSelectedFeature({ type: isBridge ? 'BRIDGE' : 'ROAD', data: road.properties }); }}
                className="cursor-pointer group"
              >
                <path
                  d={pathData}
                  fill="none"
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="transition-all hover:stroke-white hover:stroke-width-5"
                />
                {isBridge && state === 'BLOCKED' && (
                  <circle
                    cx={project(coords[0][0], coords[0][1])[0]}
                    cy={project(coords[0][0], coords[0][1])[1]}
                    r="6"
                    fill="#ef4444"
                    className="animate-ping opacity-75"
                  />
                )}
              </g>
            );
          })}

          {/* 5. Critical Facilities (Hospitals, Clinics, Shelters) */}
          {showFacilities && facilitiesLayer?.features.map((fac) => {
            const [lon, lat] = fac.geometry.coordinates;
            const [x, y] = project(lon, lat);
            const isFlooded = fac.properties.is_flooded;
            const isHospital = fac.properties.facility_type === 'HOSPITAL';

            return (
              <g
                key={fac.id || fac.properties.id}
                transform={`translate(${x}, ${y})`}
                onClick={(e) => { e.stopPropagation(); setSelectedFeature({ type: 'CRITICAL_FACILITY', data: fac.properties }); }}
                className="cursor-pointer group"
              >
                <circle
                  r={isHospital ? 9 : 7}
                  fill={isFlooded ? '#ef4444' : '#10b981'}
                  stroke="#0f172a"
                  strokeWidth="2"
                  className={isFlooded ? 'animate-pulse' : ''}
                />
                <text
                  x="12"
                  y="4"
                  fontSize="10"
                  fill="#f8fafc"
                  className="font-mono font-medium drop-shadow-md select-none group-hover:fill-sky-300 transition-colors"
                >
                  {fac.properties.name}
                </text>
              </g>
            );
          })}

          {/* 6. Priority Finding Pins */}
          {showFindings && findings.map((f) => {
            const [x, y] = project(f.location_coordinates[0], f.location_coordinates[1]);
            const isCrit = f.priority === 'CRITICAL';
            const isVerify = f.priority === 'VERIFY';
            const color = isCrit ? '#dc2626' : isVerify ? '#f59e0b' : '#38bdf8';

            return (
              <g
                key={f.id}
                transform={`translate(${x}, ${y})`}
                onClick={(e) => { e.stopPropagation(); onSelectFinding(f); }}
                className="cursor-pointer group"
              >
                <polygon
                  points="0,-14 10,0 0,14 -10,0"
                  fill={color}
                  stroke="#ffffff"
                  strokeWidth="1.5"
                  className="hover:scale-125 transition-transform"
                />
                <circle r="3" fill="#ffffff" />
                <title>{f.title}</title>
              </g>
            );
          })}
        </svg>

        {/* Map Legend Overlay */}
        <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur border border-slate-800 p-3 rounded-md text-[11px] font-mono space-y-1.5 pointer-events-auto">
          <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px] pb-1 border-b border-slate-800">
            Geospatial Layer Legend
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 bg-sky-500/50 border border-sky-400 rounded-sm" />
            <span className="text-slate-300">Active Flood Inundation</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-4 h-1 bg-emerald-500 rounded" />
            <span className="text-slate-300">Open Passable Road</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-4 h-1 bg-amber-500 rounded" />
            <span className="text-slate-300">Partially Affected Road</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-4 h-1.5 bg-rose-500 rounded" />
            <span className="text-slate-300">Blocked / Submerged Arterial</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500 border border-slate-900" />
            <span className="text-slate-300">Functioning Hospital</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-rose-500 border border-slate-900" />
            <span className="text-slate-300">Cut-Off / Flooded Hospital</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 border border-dashed border-amber-500 bg-amber-500/20" />
            <span className="text-slate-300">Isolated Community Island</span>
          </div>
        </div>

        {/* Selected Feature Inspector Sidebar Drawer */}
        {selectedFeature && (
          <div className="absolute top-4 right-4 w-80 bg-slate-900/95 backdrop-blur border border-slate-800 p-4 rounded-lg shadow-2xl text-xs font-mono space-y-3 z-30 pointer-events-auto">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-sky-400 font-bold flex items-center gap-1.5 uppercase">
                <Info className="w-3.5 h-3.5" />
                {selectedFeature.type}
              </span>
              <button 
                onClick={() => setSelectedFeature(null)}
                className="text-slate-400 hover:text-white px-1.5 py-0.5 rounded bg-slate-800 text-[10px]"
              >
                ✕
              </button>
            </div>

            <div className="space-y-1.5 text-slate-300 max-h-80 overflow-y-auto pr-1">
              {Object.entries(selectedFeature.data).map(([k, v]) => {
                if (k === 'geometry' || k === 'coordinates') return null;
                return (
                  <div key={k} className="flex justify-between border-b border-slate-850 py-1">
                    <span className="text-slate-500 capitalize">{k.replace(/_/g, ' ')}:</span>
                    <span className="font-semibold text-slate-200 text-right max-w-[160px] truncate">
                      {typeof v === 'object' ? JSON.stringify(v) : String(v)}
                    </span>
                  </div>
                );
              })}
            </div>

            {selectedFeature.type === 'ISOLATED_COMMUNITY' && (
              <div className="p-2.5 rounded bg-amber-950/60 border border-amber-800 text-amber-200 space-y-1">
                <div className="font-bold flex items-center gap-1">
                  <Users className="w-3.5 h-3.5" />
                  Isolation Severity: {selectedFeature.data.isolation_score} / 100
                </div>
                <div className="text-[11px]">
                  Estimated Population: {selectedFeature.data.estimated_population.toLocaleString()}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
