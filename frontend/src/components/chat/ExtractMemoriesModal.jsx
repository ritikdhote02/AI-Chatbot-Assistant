import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { api } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import { Sparkles, Brain, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export function ExtractMemoriesModal({ isOpen, onClose, conversationId, onMemoriesExtracted }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const toast = useToast();

  const handleExtract = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const data = await api.conversations.extractMemories(conversationId);
      setResult(data);
      toast.success(
        `Extracted ${data.candidates_found} candidates; ${data.saved_count} memories persisted to ChromaDB!`,
        'Memories Extracted'
      );
      if (onMemoriesExtracted) {
        onMemoriesExtracted(data);
      }
    } catch (err) {
      setError(err.message || 'Failed to extract memories.');
      toast.error(err.message || 'Extraction failed', 'Error');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Extract Long-Term Memories"
      maxWidth="max-w-2xl"
    >
      <div className="space-y-5">
        <p className="text-sm text-slate-300">
          Analyze this conversation transcript using Azure OpenAI structured extraction to
          automatically discover and persist durable user facts, preferences, goals, decisions,
          and corrections directly into your ChromaDB vector store.
        </p>

        {!result && !loading && !error && (
          <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/20 text-indigo-200 text-xs flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-indigo-100">Automatic vs Manual Extraction</p>
              <p className="mt-1 text-slate-300">
                The assistant also triggers background memory extraction automatically every 5 user messages.
                You can trigger manual extraction at any moment here.
              </p>
            </div>
          </div>
        )}

        {loading && (
          <div className="py-12 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="w-10 h-10 text-indigo-400 animate-spin" />
            <div className="text-center">
              <p className="text-sm font-medium text-slate-200">Analyzing conversation context...</p>
              <p className="text-xs text-slate-400 mt-1">Filtering facts, preferences, and goals</p>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Extraction Error</p>
              <p className="mt-0.5 text-xs text-rose-300/90">{error}</p>
            </div>
          </div>
        )}

        {result && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-center">
                <span className="text-2xl font-bold text-indigo-400">{result.candidates_found}</span>
                <p className="text-xs text-slate-400 mt-1">Candidates Identified</p>
              </div>
              <div className="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 text-center">
                <span className="text-2xl font-bold text-emerald-400">{result.saved_count}</span>
                <p className="text-xs text-slate-400 mt-1">Saved to ChromaDB</p>
              </div>
            </div>

            {result.memories?.length > 0 ? (
              <div className="space-y-2 mt-4">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                  Extracted Memories
                </h4>
                <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                  {result.memories.map((mem) => {
                    const categoryColors = {
                      fact: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
                      preference: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
                      goal: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
                      decision: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
                      correction: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
                    }[mem.category] || 'bg-slate-700 text-slate-300';

                    return (
                      <div
                        key={mem.id}
                        className="p-3 rounded-lg bg-slate-800/40 border border-slate-700/50 space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-xs font-semibold text-indigo-300">
                            {mem.memory_key}
                          </span>
                          <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full border ${categoryColors}`}>
                            {mem.category}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300">{mem.memory_value}</p>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-slate-400 text-xs">
                No new durable memories met the extraction criteria in this conversation segment.
              </div>
            )}
          </div>
        )}

        {/* Modal Actions */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            {result ? 'Done' : 'Cancel'}
          </button>
          {!result && (
            <button
              type="button"
              onClick={handleExtract}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 rounded-xl shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Extracting...</span>
                </>
              ) : (
                <>
                  <Brain className="w-4 h-4" />
                  <span>Start Extraction</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
