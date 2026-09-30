import React from 'react';
import { 
  ShieldAlert, Activity, Map, ListOrdered, Network, GitFork, 
  FlaskConical, RefreshCw, AlertTriangle, CheckCircle2, Clock
} from 'lucide-react';
import { EventResponse, AnalysisRunResponse } from '../types';

interface NavbarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  events: EventResponse[];
  activeEvent: EventResponse | null;
  setActiveEventId: (id: string) => void;
  latestRun: AnalysisRunResponse | null;
  onTriggerRun: () => void;
  isRunning: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentTab,
  setCurrentTab,
  events,
  activeEvent,
  setActiveEventId,
  latestRun,
  onTriggerRun,
  isRunning,
}) => {
  const tabs = [
    { id: 'control', label: 'Mission Control', icon: Activity },
    { id: 'map', label: 'Event Map', icon: Map },
    { id: 'priorities', label: 'Priority Workbench', icon: ListOrdered },
    { id: 'evidence', label: 'Evidence Explorer', icon: Network },
    { id: 'simulator', label: 'Response Simulator', icon: GitFork },
    { id: 'research', label: 'Research Lab', icon: FlaskConical },
  ];

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-sky-500/10 border border-sky-500/20 rounded-lg text-sky-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg tracking-tight text-white">TerraSentinel</span>
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-950 text-sky-400 border border-sky-800">
                  v1.2.0-EO
                </span>
              </div>
              <p className="text-[11px] text-slate-400 tracking-wide font-mono">Evidence-Grounded Disaster Intelligence</p>
            </div>
          </div>

          {/* Event Selector & Fixture Badge */}
          <div className="hidden md:flex items-center space-x-3">
            <div className="flex items-center space-x-2 bg-slate-950/80 px-3 py-1.5 rounded-md border border-slate-800">
              <span className="text-xs text-slate-400 font-mono">EVENT:</span>
              <select
                value={activeEvent?.id || ''}
                onChange={(e) => setActiveEventId(e.target.value)}
                className="bg-transparent text-xs font-semibold text-sky-300 focus:outline-none cursor-pointer"
              >
                {events.map((e) => (
                  <option key={e.id} value={e.id} className="bg-slate-900 text-white">
                    {e.name}
                  </option>
                ))}
              </select>
            </div>

            {activeEvent?.is_fixture_mode && (
              <span className="flex items-center space-x-1 text-[11px] font-mono px-2 py-1 rounded bg-amber-950/60 border border-amber-800/80 text-amber-300" title="Deterministic benchmark scenario dataset">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>FIXTURE MODE</span>
              </span>
            )}

            {/* Run Analysis Action */}
            <button
              onClick={onTriggerRun}
              disabled={isRunning}
              className={`flex items-center space-x-1.5 text-xs font-medium px-3 py-1.5 rounded-md transition-all ${
                isRunning
                  ? 'bg-sky-900/50 text-sky-400 border border-sky-800 cursor-not-allowed'
                  : 'bg-sky-600 hover:bg-sky-500 text-white shadow-lg shadow-sky-600/20 active:scale-95'
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRunning ? 'animate-spin' : ''}`} />
              <span>{isRunning ? 'Analyzing...' : 'Run Analysis'}</span>
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-1 overflow-x-auto py-1.5 scrollbar-none border-t border-slate-800/60">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = currentTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setCurrentTab(tab.id)}
                className={`flex items-center space-x-2 px-3.5 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-slate-800 text-sky-400 shadow-sm border border-slate-700/80'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-500'}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Global Progress Bar (Active Run) */}
        {latestRun && latestRun.status === 'RUNNING' && (
          <div className="pb-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-sky-300 pb-1">
              <span>{latestRun.stage_message || latestRun.stage}</span>
              <span>{Math.round((latestRun.progress || 0) * 100)}%</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div
                className="bg-sky-500 h-full transition-all duration-300 rounded-full"
                style={{ width: `${Math.round((latestRun.progress || 0) * 100)}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </header>
  );
};
