import React, { useState } from 'react';
import { 
  Network, Satellite, Eye, Cpu, Compass, Users, 
  AlertTriangle, CheckCircle2, ShieldCheck, ArrowRight, Layers
} from 'lucide-react';
import { EvidenceGraphResponse, EvidenceNode, EvidenceEdge } from '../types';

interface EvidenceExplorerProps {
  graph: EvidenceGraphResponse | null;
}

export const EvidenceExplorer: React.FC<EvidenceExplorerProps> = ({ graph }) => {
  const [selectedNode, setSelectedNode] = useState<EvidenceNode | null>(null);

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[50vh] bg-slate-900 border border-slate-800 rounded-lg p-8">
        <div className="text-center space-y-2">
          <Network className="w-8 h-8 text-sky-400 mx-auto animate-pulse" />
          <p className="text-sm font-mono text-slate-400">Loading Multi-Hop Evidence Graph...</p>
        </div>
      </div>
    );
  }

  // Node position layout calculation
  // Tier 1: Satellite Scenes (x: 100)
  // Tier 2: Model Inference (x: 350)
  // Tier 3: Flood / Infrastructure (x: 600)
  // Tier 4: Findings & Recommendations (x: 850)
  const getNodePosition = (node: EvidenceNode, idx: number): [number, number] => {
    if (node.node_type === 'SatelliteScene' || node.node_type === 'ElevationModel') {
      return [120, 100 + (idx % 3) * 140];
    }
    if (node.node_type === 'ModelInference') {
      return [380, 240];
    }
    return [760, 120 + (idx % 4) * 140];
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Network className="w-5 h-5 text-sky-400" />
            <h1 className="text-xl font-bold text-white font-mono uppercase tracking-tight">
              Multimodal Evidence Graph Explorer
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Audit causal multi-hop evidence relationships connecting raw satellite telemetry to operational directives.
          </p>
        </div>

        <div className="flex items-center space-x-3 text-xs font-mono">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-sky-400" />
            {graph.nodes.length} Evidence Entities
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            {graph.edges.length} Causal Links
          </span>
        </div>
      </div>

      {/* Main Graph Canvas Container */}
      <div className="relative w-full h-[640px] bg-slate-950 border border-slate-800 rounded-lg overflow-hidden flex">
        <svg viewBox="0 0 1000 600" className="w-full h-full">
          <defs>
            <marker id="arrow" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#475569" />
            </marker>
            <marker id="arrow-conflict" viewBox="0 0 10 10" refX="22" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
              <path d="M 0 0 L 10 5 L 0 10 z" fill="#f59e0b" />
            </marker>
          </defs>

          {/* Render Edges */}
          {graph.edges.map((edge, idx) => {
            const sourceNode = graph.nodes.find((n) => n.id === edge.source);
            const targetNode = graph.nodes.find((n) => n.id === edge.target);
            if (!sourceNode || !targetNode) return null;

            const sIdx = graph.nodes.indexOf(sourceNode);
            const tIdx = graph.nodes.indexOf(targetNode);
            const [x1, y1] = getNodePosition(sourceNode, sIdx);
            const [x2, y2] = getNodePosition(targetNode, tIdx);

            const isConflict = edge.has_conflict;

            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={isConflict ? '#f59e0b' : '#334155'}
                  strokeWidth={isConflict ? 2.5 : 1.5}
                  strokeDasharray={isConflict ? '5 5' : 'none'}
                  markerEnd={isConflict ? 'url(#arrow-conflict)' : 'url(#arrow)'}
                />
                <text
                  x={(x1 + x2) / 2}
                  y={(y1 + y2) / 2 - 8}
                  fill={isConflict ? '#f59e0b' : '#64748b'}
                  fontSize="10"
                  textAnchor="middle"
                  className="font-mono font-semibold"
                >
                  {edge.relationship}
                </text>
              </g>
            );
          })}

          {/* Render Nodes */}
          {graph.nodes.map((node, idx) => {
            const [x, y] = getNodePosition(node, idx);
            const isSelected = selectedNode?.id === node.id;
            const isFinding = node.node_type === 'ImpactFinding';
            const isModel = node.node_type === 'ModelInference';

            return (
              <g
                key={node.id}
                transform={`translate(${x}, ${y})`}
                onClick={() => setSelectedNode(node)}
                className="cursor-pointer group"
              >
                <circle
                  r={isFinding ? 24 : isModel ? 22 : 20}
                  fill={isFinding ? '#0369a1' : isModel ? '#1e293b' : '#0f172a'}
                  stroke={isSelected ? '#38bdf8' : isFinding ? '#38bdf8' : '#475569'}
                  strokeWidth={isSelected ? 3 : 1.8}
                  className="transition-all hover:stroke-white"
                />
                <text
                  textAnchor="middle"
                  y="4"
                  fontSize="10"
                  fill="#f8fafc"
                  className="font-mono font-bold select-none"
                >
                  {Math.round(node.confidence * 100)}%
                </text>
                <text
                  textAnchor="middle"
                  y="36"
                  fontSize="11"
                  fill="#94a3b8"
                  className="font-mono font-medium select-none group-hover:fill-sky-300 transition-colors"
                >
                  {node.label}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Selected Node Inspector Drawer */}
        {selectedNode && (
          <div className="absolute top-4 right-4 w-80 bg-slate-900/95 backdrop-blur border border-slate-800 p-4 rounded-lg shadow-2xl text-xs font-mono space-y-3 z-30">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <span className="text-sky-400 font-bold uppercase">{selectedNode.node_type}</span>
              <button 
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-white px-1.5 py-0.5 rounded bg-slate-800 text-[10px]"
              >
                ✕
              </button>
            </div>

            <div className="font-bold text-white text-sm">{selectedNode.label}</div>
            <div className="flex justify-between text-slate-300 border-b border-slate-850 pb-2">
              <span className="text-slate-500">Node ID:</span>
              <span className="font-mono">{selectedNode.id}</span>
            </div>

            <div className="flex justify-between text-slate-300 border-b border-slate-850 pb-2">
              <span className="text-slate-500">Calculated Confidence:</span>
              <span className="text-emerald-400 font-bold">{Math.round(selectedNode.confidence * 100)}%</span>
            </div>

            <div className="space-y-1">
              <span className="text-slate-500 block">Metadata:</span>
              <pre className="bg-slate-950 p-2.5 rounded border border-slate-850 text-[10px] text-slate-300 overflow-x-auto">
                {JSON.stringify(selectedNode.data, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
