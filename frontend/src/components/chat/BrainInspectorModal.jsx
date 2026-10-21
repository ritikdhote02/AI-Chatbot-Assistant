import React from 'react';
import { Modal } from '../common/Modal';
import { Database, Cpu, Brain, Layers, ArrowRight, ShieldCheck, Zap } from 'lucide-react';

export function BrainInspectorModal({ isOpen, onClose }) {
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Chat Point Architecture & Memory Model"
      maxWidth="max-w-3xl"
    >
      <div className="space-y-6">
        <p className="text-sm text-slate-300 leading-relaxed">
          The AI Knowledge Assistant features a dual-persistence hybrid cognitive architecture.
          Every chat request is augmented with both relational context from SQLite and semantic
          memory vectors retrieved from ChromaDB.
        </p>

        {/* 3-Tier Context Model */}
        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-indigo-400" />
            3-Tier Dynamic Prompt Assembly
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {/* Tier 1 */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-blue-400">Tier 1: Short-Term</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-300 border border-blue-500/30">
                  SQLite
                </span>
              </div>
              <h5 className="text-sm font-medium text-white">Latest 20 Messages</h5>
              <p className="text-xs text-slate-400 leading-relaxed">
                Direct conversational history reconstructed from the relational SQLite messages table.
              </p>
            </div>

            {/* Tier 2 */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-purple-400">Tier 2: Episodic</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/30">
                  ChromaDB
                </span>
              </div>
              <h5 className="text-sm font-medium text-white">Top 3 Episodes</h5>
              <p className="text-xs text-slate-400 leading-relaxed">
                Semantic cosine search against past conversation summaries, embedded with Azure OpenAI.
              </p>
            </div>

            {/* Tier 3 */}
            <div className="p-4 rounded-xl bg-slate-800/50 border border-slate-700/60 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-emerald-400">Tier 3: Long-Term</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
                  ChromaDB
                </span>
              </div>
              <h5 className="text-sm font-medium text-white">Top 5 Memories</h5>
              <p className="text-xs text-slate-400 leading-relaxed">
                Facts, preferences, goals, decisions, and corrections user-scoped with cosine similarity.
              </p>
            </div>
          </div>
        </div>

        {/* Extraction Pipeline */}
        <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/20 space-y-3">
          <div className="flex items-center gap-2 text-indigo-300 font-semibold text-sm">
            <Zap className="w-4 h-4 text-indigo-400" />
            Background Memory Extraction Pipeline
          </div>
          <div className="flex flex-col sm:flex-row items-center gap-3 text-xs text-slate-300">
            <div className="bg-slate-900/90 px-3 py-2 rounded-lg border border-slate-700/80 text-center w-full sm:w-auto">
              Every 5 User Messages
            </div>
            <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0 hidden sm:block" />
            <div className="bg-slate-900/90 px-3 py-2 rounded-lg border border-slate-700/80 text-center w-full sm:w-auto">
              FastAPI Background Task
            </div>
            <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0 hidden sm:block" />
            <div className="bg-slate-900/90 px-3 py-2 rounded-lg border border-slate-700/80 text-center w-full sm:w-auto">
              Structured Extraction LLM
            </div>
            <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0 hidden sm:block" />
            <div className="bg-slate-900/90 px-3 py-2 rounded-lg border border-slate-700/80 text-center w-full sm:w-auto">
              Persist into ChromaDB
            </div>
          </div>
        </div>

        {/* Security & User Isolation */}
        <div className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/50 text-xs text-slate-300">
          <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <p>
            <strong>Strict User Scoping:</strong> All conversations, messages, episodic summaries,
            and long-term memories are filtered by your authenticated user ID at both the SQLite query
            and ChromaDB vector filter levels.
          </p>
        </div>

        <div className="flex justify-end pt-2 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-white bg-slate-800 hover:bg-slate-700 rounded-xl transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </Modal>
  );
}
