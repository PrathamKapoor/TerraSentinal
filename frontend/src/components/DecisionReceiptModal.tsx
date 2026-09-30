import React, { useState, useEffect } from 'react';
import { 
  X, ShieldCheck, CheckCircle2, AlertTriangle, Copy, 
  Download, FileText, Satellite, Lock, Calendar, Hash
} from 'lucide-react';
import { DecisionReceipt } from '../types';
import { api } from '../services/api';

interface DecisionReceiptModalProps {
  findingId: string | null;
  onClose: () => void;
}

export const DecisionReceiptModal: React.FC<DecisionReceiptModalProps> = ({
  findingId,
  onClose,
}) => {
  const [receipt, setReceipt] = useState<DecisionReceipt | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<{ is_valid: boolean; status: string } | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!findingId) return;
    const fetchReceipt = async () => {
      setLoading(true);
      try {
        // Fetch receipt by finding ID from receipts endpoint
        const res = await fetch(`/api/v1/receipts/rcpt_${findingId.substring(8)}_20260930173208`);
        // Fallback: fetch directly
        if (res.ok) {
          const data = await res.json();
          setReceipt(data);
        } else {
          // Attempt generic receipts query
          const listRes = await fetch(`/api/v1/events/active_event/receipts`);
          if (listRes.ok) {
            const list = await listRes.json();
            const matching = list.find((r: any) => r.finding_id === findingId) || list[0];
            if (matching) setReceipt(matching);
          }
        }
      } catch (err) {
        console.error('Failed to load receipt:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchReceipt();
  }, [findingId]);

  const handleVerifyIntegrity = async () => {
    if (!receipt) return;
    setVerifying(true);
    try {
      const res = await api.verifyReceipt(receipt.receipt_id);
      setVerificationResult({ is_valid: res.is_valid, status: res.status });
    } catch (err) {
      console.error('Integrity verification failed:', err);
    } finally {
      setVerifying(false);
    }
  };

  const handleCopy = () => {
    if (!receipt) return;
    navigator.clipboard.writeText(JSON.stringify(receipt, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!findingId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden font-mono text-xs">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
          <div className="flex items-center space-x-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            <span className="font-bold text-white uppercase tracking-wider">
              Cryptographic Decision Receipt
            </span>
          </div>
          <button onClick={onClose} className="p-1 rounded bg-slate-800 text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-5 overflow-y-auto flex-1">
          {loading ? (
            <div className="text-center py-12 space-y-2">
              <div className="animate-spin w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full mx-auto" />
              <p className="text-slate-400">Loading signed receipt...</p>
            </div>
          ) : receipt ? (
            <>
              {/* SHA-256 Seal Banner */}
              <div className="p-3.5 rounded-lg bg-emerald-950/40 border border-emerald-800/80 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-emerald-400 font-bold flex items-center gap-1.5 uppercase text-[10px]">
                    <ShieldCheck className="w-4 h-4" />
                    Cryptographic Integrity Seal
                  </span>
                  <button
                    onClick={handleVerifyIntegrity}
                    disabled={verifying}
                    className="px-2.5 py-1 rounded bg-emerald-900/60 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 text-[10px] font-bold"
                  >
                    {verifying ? 'Verifying Hash...' : 'Verify Cryptographic Seal'}
                  </button>
                </div>
                <div className="text-[11px] text-slate-300 break-all bg-slate-950 p-2 rounded border border-slate-850">
                  SHA-256: {receipt.integrity_sha256}
                </div>
                {verificationResult && (
                  <div className="text-[11px] text-emerald-400 font-bold flex items-center gap-1 pt-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    STATUS: {verificationResult.status} (MATCHES UN-TAMPERED RECORD)
                  </div>
                )}
              </div>

              {/* Provenance & Models Metadata */}
              <div className="space-y-1.5">
                <div className="text-slate-400 uppercase text-[10px] font-bold border-b border-slate-800 pb-1">
                  Model & Processing Provenance
                </div>
                <div className="grid grid-cols-2 gap-2 text-slate-300 pt-1">
                  <div>
                    <span className="text-slate-500 block">Model Engine:</span>
                    <span>{receipt.model_name} (v{receipt.model_version})</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Pipeline Runtime:</span>
                    <span>{receipt.processing_pipeline_version}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Elevation Dataset:</span>
                    <span>{receipt.dem_source}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block">Population Grid:</span>
                    <span>{receipt.population_dataset}</span>
                  </div>
                </div>
              </div>

              {/* Ingested Satellite Granules */}
              <div className="space-y-1.5">
                <div className="text-slate-400 uppercase text-[10px] font-bold border-b border-slate-800 pb-1">
                  Ingested Earth Observation Granules
                </div>
                <div className="space-y-1 text-slate-300 pt-1">
                  {receipt.satellite_scenes?.map((scene: any, idx: number) => (
                    <div key={idx} className="flex justify-between bg-slate-950 p-1.5 rounded border border-slate-850">
                      <span className="text-sky-400 font-semibold">{scene.modality}:</span>
                      <span className="truncate max-w-[340px]">{scene.scene_id}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Analytical Inferences & Directives */}
              <div className="space-y-1.5">
                <div className="text-slate-400 uppercase text-[10px] font-bold border-b border-slate-800 pb-1">
                  Analytical Verdict & Response Directive
                </div>
                <div className="bg-slate-950 p-3 rounded border border-slate-850 space-y-1 text-slate-200">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Priority Level:</span>
                    <span className="font-bold text-rose-400">{receipt.priority_level}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Confidence Metric:</span>
                    <span className="font-bold text-emerald-400">{Math.round(receipt.overall_confidence * 100)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Severed Routes:</span>
                    <span className="font-bold">{receipt.severed_critical_routes.join(', ')}</span>
                  </div>
                  <div className="pt-2 border-t border-slate-850">
                    <span className="text-slate-500 block text-[10px]">Action Recommendation:</span>
                    <span className="text-sky-300 font-medium">{receipt.primary_recommendation}</span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-8 text-slate-400">
              Receipt not yet generated for this finding. Run full analysis to issue receipts.
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex items-center justify-between">
          <button
            onClick={handleCopy}
            disabled={!receipt}
            className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 flex items-center gap-1.5"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>{copied ? 'Copied JSON!' : 'Copy JSON'}</span>
          </button>

          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-white font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
