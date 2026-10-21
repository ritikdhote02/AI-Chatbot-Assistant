import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { api } from '../../api/client';
import { useToast } from '../../context/ToastContext';
import { ScrollText, Loader2, Sparkles, AlertCircle } from 'lucide-react';

export function CreateEpisodeModal({ isOpen, onClose, conversationId, onEpisodeCreated }) {
  const [loading, setLoading] = useState(false);
  const [episode, setEpisode] = useState(null);
  const [error, setError] = useState(null);
  const toast = useToast();

  const handleSummarize = async () => {
    setLoading(true);
    setError(null);
    setEpisode(null);

    try {
      const data = await api.conversations.createEpisode(conversationId);
      setEpisode(data);
      toast.success('Conversation summarized into episodic memory!', 'Episode Created');
      if (onEpisodeCreated) {
        onEpisodeCreated(data);
      }
    } catch (err) {
      setError(err.message || 'Failed to summarize conversation. Ensure it has at least 2 messages.');
      toast.error(err.message || 'Episode creation failed', 'Error');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setEpisode(null);
    setError(null);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Generate Episodic Memory"
      maxWidth="max-w-2xl"
    >
      <div className="space-y-5">
        <p className="text-sm text-slate-300">
          Synthesize this conversation into an episodic memory. The summary is embedded via
          Azure OpenAI and stored in ChromaDB, enabling semantic retrieval of past conversation
          context during future chats.
        </p>

        {!episode && !loading && !error && (
          <div className="p-4 rounded-xl bg-purple-950/30 border border-purple-500/20 text-purple-200 text-xs flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-purple-100">Episodic Memory Retrieval</p>
              <p className="mt-1 text-slate-300">
                During future chat requests, the top 3 semantically relevant episodes are automatically
                loaded into the assistant's context window. (Requires at least 2 messages in conversation)
              </p>
            </div>
          </div>
        )}

        {loading && (
          <div className="py-12 flex flex-col items-center justify-center space-y-4">
            <Loader2 className="w-10 h-10 text-purple-400 animate-spin" />
            <div className="text-center">
              <p className="text-sm font-medium text-slate-200">Summarizing conversation exchange...</p>
              <p className="text-xs text-slate-400 mt-1">Generating dense semantic summary</p>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Summarization Error</p>
              <p className="mt-0.5 text-xs text-rose-300/90">{error}</p>
            </div>
          </div>
        )}

        {episode && (
          <div className="space-y-4 bg-slate-950/60 p-4 rounded-xl border border-slate-800">
            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400">
                Episode Title
              </span>
              <h4 className="text-base font-semibold text-white mt-0.5">
                {episode.title}
              </h4>
            </div>

            <div>
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Summary
              </span>
              <p className="text-sm text-slate-300 mt-1 leading-relaxed bg-slate-900/80 p-3.5 rounded-lg border border-slate-800">
                {episode.summary}
              </p>
            </div>

            <div className="flex items-center gap-4 text-xs text-slate-400 pt-2 border-t border-slate-800/80">
              <span>Source Messages: <strong className="text-slate-200">{episode.source_message_count}</strong></span>
              <span>Updated: <strong className="text-slate-200">{new Date(episode.updated_at).toLocaleDateString()}</strong></span>
            </div>
          </div>
        )}

        {/* Modal Actions */}
        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 text-sm text-slate-300 hover:text-white hover:bg-slate-800 rounded-xl transition-colors"
          >
            {episode ? 'Close' : 'Cancel'}
          </button>
          {!episode && (
            <button
              type="button"
              onClick={handleSummarize}
              disabled={loading}
              className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-purple-600 hover:bg-purple-500 active:bg-purple-700 rounded-xl shadow-lg shadow-purple-600/25 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <ScrollText className="w-4 h-4" />
                  <span>Generate Episode</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </Modal>
  );
}
