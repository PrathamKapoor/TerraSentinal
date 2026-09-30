import React, { useState } from 'react';
import { 
  GitFork, Play, CheckCircle2, Users, Hospital, Clock, 
  TrendingDown, ShieldAlert, ArrowRight, RotateCcw, AlertTriangle
} from 'lucide-react';
import { SimulationResponse, PassabilityState } from '../types';
import { api } from '../services/api';

interface ResponseSimulatorProps {
  eventId: string;
}

export const ResponseSimulator: React.FC<ResponseSimulatorProps> = ({ eventId }) => {
  const [selectedIntervention, setSelectedIntervention] = useState<string>('bridge_b14_surma');
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<SimulationResponse | null>(null);

  const candidateActions = [
    {
      id: 'bridge_b14_surma',
      name: 'Deploy Rapid Military Pontoon on Bridge B-14',
      type: 'DEPLOY_PONTOON',
      description: 'Bypasses the submerged Surma River truss bridge with an army pontoon bridge to reconnect the western and eastern sectors.',
      estimatedHours: 4.5,
    },
    {
      id: 'road_r183_sec1',
      name: 'Clear Debris & Sandbag Rural Road R-183',
      type: 'RESTORE_ROAD',
      description: 'Erects temporary flood berms and pumps floodwaters from the primary feeder road into Gowainghat Valley.',
      estimatedHours: 6.0,
    },
    {
      id: 'road_hwy_n2_sec2',
      name: 'Armored Vehicle Convoy Shuttle across Causeway',
      type: 'RESTORE_ROAD',
      description: 'Establishes high-clearance military vehicle shuttles across 1.2 km of partially submerged causeway.',
      estimatedHours: 2.0,
    },
  ];

  const handleRunSimulation = async () => {
    setSimulating(true);
    const action = candidateActions.find((a) => a.id === selectedIntervention);
    if (!action) return;

    try {
      const res = await api.runSimulation({
        event_id: eventId,
        scenario_name: action.name,
        interventions: [
          {
            intervention_type: action.type,
            target_infrastructure_id: action.id,
            target_name: action.name,
            new_state: 'OPEN' as PassabilityState,
            cost_estimate_hours: action.estimatedHours,
          },
        ],
      });
      setSimulationResult(res);
    } catch (err) {
      console.error('Simulation execution failed:', err);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <GitFork className="w-5 h-5 text-sky-400" />
            <h1 className="text-xl font-bold text-white font-mono uppercase tracking-tight">
              Counterfactual Response Simulator
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Simulate prospective infrastructure interventions (pontoon bridges, road clearing) to evaluate humanitarian return-on-investment.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-amber-950/80 text-amber-300 border border-amber-800 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5" />
            SIMULATION / COUNTERFACTUAL
          </span>
        </div>
      </div>

      {/* Intervention Configuration & Comparison Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Candidate Intervention Picker */}
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-lg space-y-4">
          <h2 className="text-sm font-bold tracking-wide uppercase text-white font-mono">
            Candidate Interventions
          </h2>

          <div className="space-y-3">
            {candidateActions.map((action) => {
              const isSelected = selectedIntervention === action.id;
              return (
                <div
                  key={action.id}
                  onClick={() => setSelectedIntervention(action.id)}
                  className={`p-3.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-sky-950/50 border-sky-600 ring-1 ring-sky-500/50'
                      : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-white">{action.name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      ~{action.estimatedHours}h
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1.5">{action.description}</p>
                </div>
              );
            })}
          </div>

          <button
            onClick={handleRunSimulation}
            disabled={simulating}
            className="w-full mt-4 bg-sky-600 hover:bg-sky-500 text-white font-medium text-xs py-2.5 rounded-md flex items-center justify-center gap-2 transition-all shadow-lg shadow-sky-600/20 active:scale-95"
          >
            <Play className={`w-4 h-4 ${simulating ? 'animate-spin' : ''}`} />
            <span>{simulating ? 'Simulating Dynamic Graph...' : 'Execute Counterfactual Run'}</span>
          </button>
        </div>

        {/* Right 2 Columns: Simulated Humanitarian Consequence Output */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 p-5 rounded-lg space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold tracking-wide uppercase text-white font-mono flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-emerald-400" />
              Humanitarian Impact Delta
            </h2>

            {simulationResult && (
              <span className="text-xs font-mono text-slate-400">
                Scenario: <span className="text-sky-300 font-semibold">{simulationResult.scenario_name}</span>
              </span>
            )}
          </div>

          {simulationResult ? (
            <div className="space-y-6">
              {/* Delta KPI Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-lg bg-emerald-950/40 border border-emerald-800/80">
                  <div className="flex items-center justify-between text-emerald-400">
                    <span className="text-[11px] font-mono font-bold uppercase">RECONNECTED POPULATION</span>
                    <Users className="w-4 h-4" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-white mt-2">
                    +{simulationResult.delta.reconnected_population.toLocaleString()}
                  </div>
                  <div className="text-xs text-emerald-300 mt-1">
                    Isolated: {simulationResult.baseline_isolated_population.toLocaleString()} → {simulationResult.simulated_isolated_population.toLocaleString()}
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-sky-950/40 border border-sky-800/80">
                  <div className="flex items-center justify-between text-sky-400">
                    <span className="text-[11px] font-mono font-bold uppercase">HOSPITAL ACCESS RESTORED</span>
                    <Hospital className="w-4 h-4" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-white mt-2">
                    +{simulationResult.delta.restored_hospitals_count} Facility
                  </div>
                  <div className="text-xs text-sky-300 mt-1">
                    Osmani Trauma Center accessible
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-amber-950/40 border border-amber-800/80">
                  <div className="flex items-center justify-between text-amber-400">
                    <span className="text-[11px] font-mono font-bold uppercase">AVG DETOUR SAVED</span>
                    <Clock className="w-4 h-4" />
                  </div>
                  <div className="text-2xl font-bold font-mono text-white mt-2">
                    -{simulationResult.delta.average_travel_time_saved_minutes} min
                  </div>
                  <div className="text-xs text-amber-300 mt-1">
                    Emergency response transit recovery
                  </div>
                </div>
              </div>

              {/* Analytical Narrative Explanation */}
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2">
                <span className="text-xs font-mono font-bold uppercase text-slate-400">
                  Algorithmic Rationale & Decision Trade-Off
                </span>
                <p className="text-xs text-slate-200 leading-relaxed font-sans">
                  {simulationResult.explanation}
                </p>
              </div>

              <div className="p-3 rounded bg-slate-950/80 border border-slate-800 text-[11px] font-mono text-slate-400 flex items-center justify-between">
                <span>Simulation ID: {simulationResult.simulation_id}</span>
                <span className="text-amber-400 font-bold">{simulationResult.simulation_badge}</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 space-y-3">
              <div className="w-10 h-10 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto">
                <Play className="w-5 h-5 ml-0.5" />
              </div>
              <p className="text-xs font-mono text-slate-400">
                Select an infrastructure intervention and click "Execute Counterfactual Run" to recalculate network connectivity.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
