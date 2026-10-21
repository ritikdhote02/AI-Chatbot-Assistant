import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useToast } from '../context/ToastContext';
import {
  ScrollText,
  Search,
  ExternalLink,
  MessageSquare,
  Calendar,
  Sparkles,
  Loader2,
  Copy,
  Check,
  Layers,
} from 'lucide-react';

export function EpisodesPage() {
  const [episodes, setEpisodes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState(null);

  const toast = useToast();

  const fetchEpisodes = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.episodes.list();
      setEpisodes(data || []);
    } catch (err) {
      toast.error(err.message || 'Could not load episodic memories', 'Error');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchEpisodes();
  }, [fetchEpisodes]);

  const handleCopy = (summary, id) => {
    navigator.clipboard.writeText(summary);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredEpisodes = episodes.filter(
    (ep) =>
      ep.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ep.summary.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 overflow-y-auto">
      <div className="p-4 sm:p-6 lg:p-8 max-w-5xl w-full mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/30">
                <ScrollText className="w-5 h-5" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                Episodic Memories
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              Synthesized conversation episodes stored as dense vector embeddings in ChromaDB.
            </p>
          </div>
        </div>

        {/* Informational Card */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-950/40 via-indigo-950/30 to-slate-900 border border-purple-500/20 flex items-start gap-3.5">
          <Sparkles className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
          <div className="text-xs text-slate-300 space-y-1">
            <p className="font-semibold text-purple-200">
              How Episodic Memory Powers Conversations
            </p>
            <p className="text-slate-400 leading-relaxed">
              When you ask questions in any conversation, the top 3 semantically related episodes are
              retrieved using cosine similarity and injected into the assistant's system prompt. You can
              create an episode at any time from the chat toolbar.
            </p>
          </div>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search episodic summaries..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-purple-500 transition-colors"
          />
        </div>

        {/* Episodes List */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
            <p className="text-xs">Loading episodic memories...</p>
          </div>
        ) : filteredEpisodes.length === 0 ? (
          <div className="py-20 text-center space-y-4 rounded-3xl glass-card border border-dashed border-slate-800">
            <div className="w-12 h-12 rounded-2xl bg-purple-500/10 text-purple-400 flex items-center justify-center mx-auto border border-purple-500/20">
              <ScrollText className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">No episodic memories yet</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                {searchQuery
                  ? 'No episodes match your search query.'
                  : 'Open any conversation with at least 2 messages and click "Summarize Episode" to record your first episode!'}
              </p>
            </div>
            {!searchQuery && (
              <Link
                to="/chat"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-purple-600 hover:bg-purple-500"
              >
                Go to Chats →
              </Link>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredEpisodes.map((ep) => (
              <div
                key={ep.id}
                className="rounded-2xl glass-card p-5 sm:p-6 space-y-4 transition-all"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
                      <ScrollText className="w-4 h-4" />
                    </div>
                    <h3 className="text-base font-semibold text-white">
                      {ep.title}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2 text-xs">
                    <span className="px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700/80 font-mono text-[11px]">
                      {ep.source_message_count} messages
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopy(ep.summary, ep.id)}
                      className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
                      title="Copy summary"
                    >
                      {copiedId === ep.id ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 text-xs sm:text-sm text-slate-300 leading-relaxed">
                  {ep.summary}
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-2 border-t border-slate-800/60">
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5" />
                    Created: {new Date(ep.created_at).toLocaleDateString()}
                  </span>

                  <Link
                    to={`/chat/${ep.conversation_id}`}
                    className="inline-flex items-center gap-1.5 text-purple-400 hover:text-purple-300 font-medium"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>Open Conversation</span>
                    <ExternalLink className="w-3 h-3" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
