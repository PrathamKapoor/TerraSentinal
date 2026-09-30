import React, { useState } from 'react';
import { 
  X, ShieldAlert, CheckCircle2, AlertTriangle, FileText, 
  ArrowRight, Users, Compass, Satellite, ShieldCheck, UserCheck
} from 'lucide-react';
import { ImpactFinding, VerificationStatus } from '../types';
import { api } from '../services/api';

interface FindingDetailModalProps {
  finding: ImpactFinding | null;
  onClose: () => void;
  onOpenReceipt: (findingId: string) => void;
  onFindingUpdated: (updated: ImpactFinding) => void;
}

export const FindingDetailModal: React.FC<FindingDetailModalProps> = ({
  finding,
  onClose,
  onOpenReceipt,
  onFindingUpdated,
}) => {
  const [verifying, setVerifying] = useState(false);
  const [notes, setNotes] = useState('');

  if (!finding) return null;

  const handleVerify = async (status: VerificationStatus) => {
    setVerifying(true);
    try {
      const updated = await api.verifyFinding(finding.id, {
        status,
        responder_id: 'IncidentCommander-01',
        notes: notes || 'Verified via operational mission protocol.',
        ground_truth_modality: 'FIELD_GROUND_TRUTH'
      });
      onFindingUpdated(updated);
    } catch (err) {
      console.error('Failed to verify finding:', err);
    } finally {
      setVerifying(false);
    }
  };

  const isCritical = finding.priority === 'CRITICAL';
  const isVerify = finding.priority === 'VERIFY';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-3xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-start justify-between bg-slate-950/60">
          <div>
            <div className="flex items-center space-x-2">
              <span
                className={`text-xs font-mono font-bold px-2 py-0.5 rounded ${
                  isCritical
                    ? 'bg-rose-950 text-rose-300 border border-rose-800'
                    : isVerify
                    ? 'bg-amber-950 text-amber-300 border border-amber-800'
                    : 'bg-sky-950 text-sky-300 border border-sky-800'
                }`}
              >
                {finding.priority} ({finding.criticality_score}/100)
              </span>
              <span className="text-xs font-mono text-slate-400">ID: {finding.id}</span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                Confidence: {Math.round(finding.confidence * 100)}%
              </span>
            </div>
            <h2 className="text-lg font-bold text-white mt-1.5">{finding.title}</h2>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1 font-sans">
          {/* Situation Summary */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
              Operational Impact Summary
            </h3>
            <p className="text-sm text-slate-200 leading-relaxed bg-slate-950 p-4 rounded-lg border border-slate-850">
              {finding.summary}
            </p>
          </div>

          {/* Action Directive / Recommendation */}
          <div className="p-4 rounded-lg bg-sky-950/30 border border-sky-800/60 space-y-2">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-sky-400 flex items-center gap-1.5">
              <Compass className="w-4 h-4" />
              Response Action Recommendation
            </h3>
            <p className="text-sm text-sky-200 font-medium">
              {finding.recommendation}
            </p>
          </div>

          {/* Causal Multi-Hop Evidence Chain */}
          <div className="space-y-3">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
              <Satellite className="w-4 h-4 text-sky-400" />
              Observable Evidence Traceability Chain
            </h3>
            
            <div className="space-y-2.5">
              {finding.evidence_chain.map((item, idx) => (
                <div key={idx} className="flex items-start space-x-3 p-3 rounded-md bg-slate-950/70 border border-slate-800 text-xs">
                  <div className="w-6 h-6 rounded-full bg-sky-950 border border-sky-800 text-sky-400 flex items-center justify-center font-mono font-bold shrink-0 mt-0.5">
                    {item.step}
                  </div>
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center justify-between font-mono">
                      <span className="font-semibold text-slate-300">{item.layer}</span>
                      <span className="text-[10px] text-emerald-400 font-bold">
                        {Math.round(item.confidence * 100)}% conf
                      </span>
                    </div>
                    <p className="text-slate-400">{item.description}</p>
                    <div className="text-[10px] font-mono text-slate-500">Source: {item.source_id}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Human Ground Truth Verification Form */}
          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <UserCheck className="w-4 h-4 text-emerald-400" />
                Responder Verification Protocol
              </h3>
              <span className={`text-[11px] font-mono font-semibold px-2 py-0.5 rounded ${
                finding.verification_status === 'CONFIRMED'
                  ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {finding.verification_status}
              </span>
            </div>

            <input
              type="text"
              placeholder="Operational field notes or ground reconnaissance report..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
            />

            <div className="flex items-center space-x-2 pt-1">
              <button
                onClick={() => handleVerify('CONFIRMED')}
                disabled={verifying}
                className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium py-2 rounded transition-colors flex items-center justify-center gap-1"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Confirm Field Truth</span>
              </button>
              <button
                onClick={() => handleVerify('REJECTED')}
                disabled={verifying}
                className="flex-1 bg-rose-900/60 hover:bg-rose-800 text-rose-200 border border-rose-700 text-xs font-medium py-2 rounded transition-colors flex items-center justify-center gap-1"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Reject / False Alarm</span>
              </button>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between">
          <span className="text-xs font-mono text-slate-500">
            Coordinates: [{finding.location_coordinates.join(', ')}]
          </span>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => onOpenReceipt(finding.id)}
              className="px-4 py-2 rounded-md bg-slate-800 hover:bg-slate-700 text-sky-400 border border-slate-700 text-xs font-mono font-medium flex items-center gap-1.5 transition-colors"
            >
              <FileText className="w-4 h-4" />
              <span>Auditable Decision Receipt</span>
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
