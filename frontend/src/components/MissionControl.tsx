import React from 'react';
import { 
  Waves, AlertTriangle, Users, Compass, Hospital, ShieldCheck, 
  Satellite, Clock, ArrowRight, Eye, CheckCircle2, ChevronRight,
  TrendingUp, Radio
} from 'lucide-react';
import { MissionControlSummary, ImpactFinding } from '../types';

interface MissionControlProps {
  summary: MissionControlSummary | null;
  onSelectFinding: (finding: ImpactFinding) => void;
  onNavigateTab: (tab: string) => void;
}

export const MissionControl: React.FC<MissionControlProps> = ({
  summary,
  onSelectFinding,
  onNavigateTab,
}) => {
  if (!summary) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-3">
          <div className="animate-spin w-8 h-8 border-2 border-sky-500 border-t-transparent rounded-full mx-auto" />
          <p className="text-sm font-mono text-slate-400">Loading Disaster Mission Data...</p>
        </div>
      </div>
    );
  }

  const {
    event,
    flood_summary,
    infrastructure_summary,
    population_summary,
    isolation_summary,
    observations_summary,
    top_findings,
    is_demo_mode
  } = summary;

  const kpis = [
    {
      label: 'TOTAL FLOOD EXTENT',
      value: `${flood_summary.total_flooded_sqkm.toFixed(1)} km²`,
      subtitle: `+${flood_summary.newly_flooded_sqkm.toFixed(1)} km² newly inundated`,
      icon: Waves,
      color: 'text-sky-400',
      bg: 'bg-sky-500/10 border-sky-500/20'
    },
    {
      label: 'ISOLATED COMMUNITIES',
      value: isolation_summary.isolated_communities_count.toString(),
      subtitle: `${isolation_summary.total_isolated_population.toLocaleString()} residents severed`,
      icon: Users,
      color: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/20'
    },
    {
      label: 'DISRUPTED ROADS',
      value: `${infrastructure_summary.roads_blocked_count} Blocked`,
      subtitle: `${infrastructure_summary.roads_affected_count} partially impassable (${infrastructure_summary.roads_blocked_km.toFixed(1)} km)`,
      icon: Compass,
      color: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/20'
    },
    {
      label: 'SEVERED BRIDGES',
      value: `${infrastructure_summary.bridges_blocked_count} Submerged`,
      subtitle: `${infrastructure_summary.facilities_flooded_count} healthcare facility cut off`,
      icon: Hospital,
      color: 'text-red-400',
      bg: 'bg-red-500/10 border-red-500/20'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Event Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                ACTIVE INCIDENT
              </span>
              <span className="text-xs font-mono text-slate-400">ID: {event.id}</span>
              {is_demo_mode && (
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800">
                  DETERMINISTIC FIXTURE
                </span>
              )}
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-white mt-1">{event.name}</h1>
            <p className="text-xs text-slate-400 mt-1 max-w-3xl">{event.description}</p>
          </div>

          <div className="flex items-center space-x-3 bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs font-mono">
            <div>
              <span className="text-slate-500 block text-[10px]">ANALYSIS TIMELINE</span>
              <span className="text-slate-300">{event.pre_event_date} → {event.post_event_date}</span>
            </div>
            <div className="border-l border-slate-800 pl-3">
              <span className="text-slate-500 block text-[10px]">DATA CONFIDENCE</span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                {Math.round(observations_summary.overall_confidence * 100)}% Verified
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => {
          const Icon = kpi.icon;
          return (
            <div key={idx} className={`p-4 rounded-lg border ${kpi.bg}`}>
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono font-medium text-slate-400 tracking-wider">
                  {kpi.label}
                </span>
                <Icon className={`w-4 h-4 ${kpi.color}`} />
              </div>
              <div className="mt-2 text-2xl font-bold font-mono text-white">{kpi.value}</div>
              <div className="text-xs text-slate-400 mt-1 font-sans">{kpi.subtitle}</div>
            </div>
          );
        })}
      </div>

      {/* Middle Grid: Operational Findings & Sensor Integrity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: High Criticality Operational Findings */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-bold tracking-wide uppercase text-white font-mono">
                Priority Action Findings ({top_findings.length})
              </h2>
            </div>
            <button
              onClick={() => onNavigateTab('priorities')}
              className="text-xs font-mono text-sky-400 hover:text-sky-300 flex items-center space-x-1"
            >
              <span>View All Workbench</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {top_findings.map((f) => {
              const isCritical = f.priority === 'CRITICAL';
              const isVerify = f.priority === 'VERIFY';

              return (
                <div
                  key={f.id}
                  onClick={() => onSelectFinding(f)}
                  className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 hover:border-slate-700 transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                            isCritical
                              ? 'bg-rose-950 text-rose-300 border border-rose-800'
                              : isVerify
                              ? 'bg-amber-950 text-amber-300 border border-amber-800'
                              : 'bg-sky-950 text-sky-300 border border-sky-800'
                          }`}
                        >
                          {f.priority} ({f.criticality_score})
                        </span>
                        <span className="text-xs font-semibold text-white group-hover:text-sky-300 transition-colors">
                          {f.title}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">{f.summary}</p>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-xs font-mono text-slate-300 font-bold block">
                        {f.affected_population.toLocaleString()} pop
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400">
                        {Math.round(f.confidence * 100)}% conf
                      </span>
                    </div>
                  </div>

                  <div className="mt-3 pt-2 border-t border-slate-850 flex items-center justify-between text-[11px] font-mono text-slate-500">
                    <span>Target: {f.affected_infrastructure_ids.join(', ')}</span>
                    <span className="text-sky-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                      Inspect Chain <ArrowRight className="w-3 h-3" />
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Col: Satellite & Contextual Quality State */}
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4">
          <div className="border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold tracking-wide uppercase text-white font-mono flex items-center gap-2">
              <Satellite className="w-4 h-4 text-sky-400" />
              Earth Observation Ingestion
            </h2>
          </div>

          <div className="space-y-3">
            {observations_summary.quality_details.map((obs, idx) => (
              <div key={idx} className="p-3 rounded-md bg-slate-950 border border-slate-800/80 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-200 font-mono">{obs.modality}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
                    {obs.quality_state}
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-400">
                  Scene: {obs.scene_id.substring(0, 24)}...
                </div>
                <div className="text-[10px] text-slate-500">
                  {obs.notes}
                </div>
                <div className="flex justify-between text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-850">
                  <span>Res: {obs.spatial_resolution_meters}m</span>
                  <span>Age: {obs.age_hours}h ago</span>
                </div>
              </div>
            ))}
          </div>

          {/* Quick Counterfactual Callout */}
          <div className="p-4 rounded-lg bg-sky-950/40 border border-sky-800/60 space-y-2">
            <span className="text-xs font-bold font-mono text-sky-300 flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 animate-pulse text-sky-400" />
              Counterfactual Mission Simulator
            </span>
            <p className="text-xs text-slate-300">
              Evaluate prospective bridge restoration or pontoon deployments to compute reconnected population deltas.
            </p>
            <button
              onClick={() => onNavigateTab('simulator')}
              className="w-full mt-1 bg-sky-600 hover:bg-sky-500 text-white text-xs font-medium py-1.5 rounded transition-colors"
            >
              Open Response Simulator
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
