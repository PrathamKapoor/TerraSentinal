import React, { useState } from 'react';
import { 
  ListOrdered, Filter, ArrowUpDown, ShieldAlert, CheckCircle2, 
  AlertTriangle, Eye, Users, Compass, Hospital, FileText
} from 'lucide-react';
import { ImpactFinding, PriorityLevel } from '../types';

interface PriorityWorkbenchProps {
  findings: ImpactFinding[];
  onSelectFinding: (finding: ImpactFinding) => void;
  onOpenReceipt: (findingId: string) => void;
}

export const PriorityWorkbench: React.FC<PriorityWorkbenchProps> = ({
  findings,
  onSelectFinding,
  onOpenReceipt,
}) => {
  const [filterPriority, setFilterPriority] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = findings.filter((f) => {
    if (filterPriority !== 'ALL' && f.priority !== filterPriority) return false;
    if (searchTerm && !f.title.toLowerCase().includes(searchTerm.toLowerCase()) && !f.summary.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Workbench Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-5 rounded-lg">
        <div>
          <div className="flex items-center space-x-2">
            <ListOrdered className="w-5 h-5 text-sky-400" />
            <h1 className="text-xl font-bold text-white font-mono uppercase tracking-tight">
              Operational Priority Workbench
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Explainable multi-criteria ranking of disaster impacts by human population, critical facility loss, and network centrality.
          </p>
        </div>

        {/* Filter Toolbar */}
        <div className="flex items-center space-x-2 text-xs font-mono">
          <input
            type="text"
            placeholder="Search findings..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="bg-slate-950 border border-slate-700 px-3 py-1.5 rounded text-white focus:outline-none focus:border-sky-500"
          />

          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="bg-slate-950 border border-slate-700 px-3 py-1.5 rounded text-sky-300 focus:outline-none"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="HIGH">High Only</option>
            <option value="VERIFY">Verification Needed</option>
          </select>
        </div>
      </div>

      {/* Findings Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-4">Priority / Score</th>
                <th className="py-3 px-4">Finding & Causal Target</th>
                <th className="py-3 px-4">Human Impact</th>
                <th className="py-3 px-4">Confidence / Sensor</th>
                <th className="py-3 px-4">Verification State</th>
                <th className="py-3 px-4 text-right">Operational Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filtered.map((f) => {
                const isCrit = f.priority === 'CRITICAL';
                const isVerify = f.priority === 'VERIFY';

                return (
                  <tr key={f.id} className="hover:bg-slate-850/60 transition-colors">
                    <td className="py-4 px-4 font-mono whitespace-nowrap">
                      <div className="flex items-center space-x-1.5">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isCrit
                              ? 'bg-rose-950 text-rose-300 border border-rose-800'
                              : isVerify
                              ? 'bg-amber-950 text-amber-300 border border-amber-800'
                              : 'bg-sky-950 text-sky-300 border border-sky-800'
                          }`}
                        >
                          {f.priority}
                        </span>
                        <span className="font-bold text-white">{f.criticality_score}</span>
                      </div>
                    </td>

                    <td className="py-4 px-4 max-w-md">
                      <div 
                        onClick={() => onSelectFinding(f)}
                        className="font-bold text-white hover:text-sky-300 cursor-pointer transition-colors"
                      >
                        {f.title}
                      </div>
                      <div className="text-xs text-slate-400 mt-1 line-clamp-1">{f.summary}</div>
                      <div className="text-[10px] font-mono text-slate-500 mt-1">
                        Affected Targets: {f.affected_infrastructure_ids.join(', ')}
                      </div>
                    </td>

                    <td className="py-4 px-4 font-mono whitespace-nowrap">
                      <span className="text-white font-bold block">{f.affected_population.toLocaleString()} pop</span>
                      <span className="text-[10px] text-slate-500">severed access</span>
                    </td>

                    <td className="py-4 px-4 font-mono whitespace-nowrap">
                      <span className="text-emerald-400 font-bold block">
                        {Math.round(f.confidence * 100)}%
                      </span>
                      {f.conflict_state !== 'NONE' ? (
                        <span className="text-[10px] text-amber-400 block font-semibold">
                          CONFLICT DETECTED
                        </span>
                      ) : (
                        <span className="text-[10px] text-slate-500 block">SAR + Optical Agree</span>
                      )}
                    </td>

                    <td className="py-4 px-4 font-mono whitespace-nowrap">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        f.verification_status === 'CONFIRMED'
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : 'bg-slate-800 text-slate-400'
                      }`}>
                        {f.verification_status}
                      </span>
                    </td>

                    <td className="py-4 px-4 text-right space-x-2 whitespace-nowrap">
                      <button
                        onClick={() => onSelectFinding(f)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
                      >
                        Inspect
                      </button>
                      <button
                        onClick={() => onOpenReceipt(f.id)}
                        className="px-2.5 py-1 rounded bg-sky-950 hover:bg-sky-900 border border-sky-800 text-sky-400 text-xs font-mono font-medium transition-colors"
                      >
                        Receipt
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
