import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api/client';
import { useToast } from '../context/ToastContext';
import { Modal } from '../components/common/Modal';
import {
  Brain,
  Plus,
  Search,
  Trash2,
  Edit3,
  ExternalLink,
  Copy,
  Check,
  Tag,
  Loader2,
  AlertCircle,
  Calendar,
  Sparkles,
} from 'lucide-react';

const CATEGORIES = ['fact', 'preference', 'goal', 'decision', 'correction'];

const CATEGORY_STYLES = {
  fact: {
    bg: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    dot: 'bg-blue-400',
  },
  preference: {
    bg: 'bg-purple-500/10 text-purple-400 border-purple-500/30',
    dot: 'bg-purple-400',
  },
  goal: {
    bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    dot: 'bg-amber-400',
  },
  decision: {
    bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    dot: 'bg-emerald-400',
  },
  correction: {
    bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    dot: 'bg-rose-400',
  },
};

export function MemoriesPage() {
  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingMemory, setEditingMemory] = useState(null);
  const [deletingMemoryId, setDeletingMemoryId] = useState(null);

  // Form states for Create
  const [createKey, setCreateKey] = useState('');
  const [createValue, setCreateValue] = useState('');
  const [createCategory, setCreateCategory] = useState('fact');
  const [createSourceId, setCreateSourceId] = useState('');
  const [submittingCreate, setSubmittingCreate] = useState(false);

  // Form states for Edit
  const [editValue, setEditValue] = useState('');
  const [editCategory, setEditCategory] = useState('fact');
  const [submittingEdit, setSubmittingEdit] = useState(false);

  // Copied indicator
  const [copiedId, setCopiedId] = useState(null);

  const toast = useToast();

  const fetchMemories = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.memories.list();
      setMemories(data || []);
    } catch (err) {
      toast.error(err.message || 'Could not fetch memories', 'Error');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchMemories();
  }, [fetchMemories]);

  // Handle Copy
  const handleCopy = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Create Memory
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    const normalizedKey = createKey.trim().toLowerCase();

    if (!/^[a-z0-9_]+$/.test(normalizedKey)) {
      toast.error('Memory key must be lowercase snake_case (e.g. preferred_database)', 'Invalid Key');
      return;
    }

    setSubmittingCreate(true);
    try {
      const newMem = await api.memories.create({
        memory_key: normalizedKey,
        memory_value: createValue.trim(),
        category: createCategory,
        source_conversation_id: createSourceId.trim() || null,
      });

      setMemories((prev) => [newMem, ...prev]);
      toast.success(`Memory '${newMem.memory_key}' created in ChromaDB!`, 'Created');
      setIsCreateOpen(false);
      setCreateKey('');
      setCreateValue('');
      setCreateCategory('fact');
      setCreateSourceId('');
    } catch (err) {
      toast.error(err.message || 'Failed to create memory', 'Error');
    } finally {
      setSubmittingCreate(false);
    }
  };

  // Open Edit Modal
  const openEdit = (mem) => {
    setEditingMemory(mem);
    setEditValue(mem.memory_value);
    setEditCategory(mem.category);
  };

  // Submit Edit
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editingMemory) return;

    setSubmittingEdit(true);
    try {
      const updated = await api.memories.update(editingMemory.id, {
        memory_value: editValue.trim(),
        category: editCategory,
      });

      setMemories((prev) =>
        prev.map((m) => (m.id === editingMemory.id ? updated : m))
      );
      toast.success('Memory updated successfully!', 'Saved');
      setEditingMemory(null);
    } catch (err) {
      toast.error(err.message || 'Failed to update memory', 'Error');
    } finally {
      setSubmittingEdit(false);
    }
  };

  // Delete Memory
  const handleDelete = async () => {
    if (!deletingMemoryId) return;

    try {
      await api.memories.delete(deletingMemoryId);
      setMemories((prev) => prev.filter((m) => m.id !== deletingMemoryId));
      toast.success('Memory removed from vector store', 'Deleted');
      setDeletingMemoryId(null);
    } catch (err) {
      toast.error(err.message || 'Failed to delete memory', 'Error');
    }
  };

  // Filter logic
  const filteredMemories = memories.filter((mem) => {
    const matchesCategory =
      selectedCategory === 'all' || mem.category === selectedCategory;
    const matchesQuery =
      mem.memory_key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      mem.memory_value.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesQuery;
  });

  const getCategoryCount = (cat) =>
    memories.filter((m) => m.category === cat).length;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 overflow-y-auto">
      {/* Page Header */}
      <div className="p-4 sm:p-6 lg:p-8 max-w-6xl w-full mx-auto space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/30">
                <Brain className="w-5 h-5" />
              </div>
              <h1 className="text-xl sm:text-2xl font-bold text-white tracking-tight">
                Long-Term Memory Vault
              </h1>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 mt-1">
              User-scoped durable facts, preferences, goals, decisions, and corrections in ChromaDB.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setIsCreateOpen(true)}
            className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-medium text-xs text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 shadow-lg shadow-indigo-600/25 transition-all shrink-0"
          >
            <Plus className="w-4 h-4" />
            <span>Create Memory</span>
          </button>
        </div>

        {/* Search & Category Filter Pills */}
        <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by key or value content..."
              className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 scrollbar-none">
            <button
              type="button"
              onClick={() => setSelectedCategory('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors shrink-0 ${
                selectedCategory === 'all'
                  ? 'bg-slate-800 text-white border border-slate-700 font-semibold'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              All ({memories.length})
            </button>
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium capitalize transition-colors shrink-0 ${
                  selectedCategory === cat
                    ? 'bg-indigo-950/80 text-indigo-300 border border-indigo-500/40 font-semibold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                {cat} ({getCategoryCount(cat)})
              </button>
            ))}
          </div>
        </div>

        {/* Memory Grid */}
        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center space-y-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            <p className="text-xs">Loading long-term memories...</p>
          </div>
        ) : filteredMemories.length === 0 ? (
          <div className="py-20 text-center space-y-4 rounded-3xl glass-card border border-dashed border-slate-800">
            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto border border-indigo-500/20">
              <Brain className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-white">No memories found</h3>
              <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
                {searchQuery || selectedCategory !== 'all'
                  ? 'Try adjusting your search query or category filter.'
                  : 'You have no memories stored yet. Create one or extract memories from a conversation!'}
              </p>
            </div>
            {!(searchQuery || selectedCategory !== 'all') && (
              <button
                type="button"
                onClick={() => setIsCreateOpen(true)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Your First Memory
              </button>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredMemories.map((mem) => {
              const catStyle = CATEGORY_STYLES[mem.category] || {
                bg: 'bg-slate-800 text-slate-300',
                dot: 'bg-slate-400',
              };

              return (
                <div
                  key={mem.id}
                  className="rounded-2xl glass-card p-4 sm:p-5 flex flex-col justify-between space-y-4 group transition-all"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-semibold border ${catStyle.bg}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${catStyle.dot}`} />
                        <span className="capitalize">{mem.category}</span>
                      </span>

                      <div className="flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => handleCopy(mem.memory_value, mem.id)}
                          className="p-1 text-slate-400 hover:text-white rounded-md hover:bg-slate-800 transition-colors"
                          title="Copy memory value"
                        >
                          {copiedId === mem.id ? (
                            <Check className="w-3.5 h-3.5 text-emerald-400" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                        <button
                          type="button"
                          onClick={() => openEdit(mem)}
                          className="p-1 text-slate-400 hover:text-indigo-400 rounded-md hover:bg-slate-800 transition-colors"
                          title="Edit memory"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={() => setDeletingMemoryId(mem.id)}
                          className="p-1 text-slate-400 hover:text-rose-400 rounded-md hover:bg-slate-800 transition-colors"
                          title="Delete memory"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <span className="font-mono text-xs font-bold text-indigo-300 tracking-tight">
                        {mem.memory_key}
                      </span>
                      <p className="text-xs text-slate-300 mt-1 leading-relaxed break-words">
                        {mem.memory_value}
                      </p>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(mem.created_at).toLocaleDateString()}
                    </span>

                    {mem.source_conversation_id && (
                      <Link
                        to={`/chat/${mem.source_conversation_id}`}
                        className="inline-flex items-center gap-1 text-indigo-400 hover:text-indigo-300"
                        title="View source conversation"
                      >
                        <span>Chat Source</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </Link>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create Memory Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Long-Term Memory"
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Memory Key <span className="text-[10px] text-slate-400 lowercase">(snake_case)</span>
            </label>
            <input
              type="text"
              required
              maxLength={100}
              value={createKey}
              onChange={(e) => setCreateKey(e.target.value)}
              placeholder="preferred_framework or primary_career_goal"
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Category
            </label>
            <select
              value={createCategory}
              onChange={(e) => setCreateCategory(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500 capitalize"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c} className="capitalize">
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Memory Value / Statement
            </label>
            <textarea
              required
              rows={3}
              maxLength={2000}
              value={createValue}
              onChange={(e) => setCreateValue(e.target.value)}
              placeholder="State the durable fact or preference clearly..."
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
            />
            <span className="block text-right text-[10px] text-slate-500 mt-0.5">
              {createValue.length}/2000
            </span>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Source Conversation ID <span className="text-[10px] text-slate-500">(Optional)</span>
            </label>
            <input
              type="text"
              value={createSourceId}
              onChange={(e) => setCreateSourceId(e.target.value)}
              placeholder="Optional conversation UUID"
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700/70 text-xs text-white placeholder-slate-500 font-mono focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setIsCreateOpen(false)}
              className="px-4 py-2 text-xs text-slate-400 hover:text-white rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingCreate}
              className="flex items-center gap-1.5 px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-all disabled:opacity-50"
            >
              {submittingCreate ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Plus className="w-3.5 h-3.5" />
                  <span>Save Memory</span>
                </>
              )}
            </button>
          </div>
        </form>
      </Modal>

      {/* Edit Memory Modal */}
      <Modal
        isOpen={!!editingMemory}
        onClose={() => setEditingMemory(null)}
        title="Edit Memory"
        maxWidth="max-w-lg"
      >
        <form onSubmit={handleEditSubmit} className="space-y-4">
          <div>
            <span className="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Memory Key
            </span>
            <div className="px-3.5 py-2 rounded-xl bg-slate-950/60 border border-slate-800 font-mono text-xs text-indigo-300">
              {editingMemory?.memory_key}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Category
            </label>
            <select
              value={editCategory}
              onChange={(e) => setEditCategory(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500 capitalize"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c} className="capitalize">
                  {c}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1">
              Memory Value
            </label>
            <textarea
              required
              rows={4}
              maxLength={2000}
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              className="w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
            />
            <span className="block text-right text-[10px] text-slate-500 mt-0.5">
              {editValue.length}/2000
            </span>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setEditingMemory(null)}
              className="px-4 py-2 text-xs text-slate-400 hover:text-white rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submittingEdit}
              className="flex items-center gap-1.5 px-5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-all disabled:opacity-50"
            >
              {submittingEdit ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Updating...</span>
                </>
              ) : (
                <span>Update Memory</span>
              )}
            </button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingMemoryId}
        onClose={() => setDeletingMemoryId(null)}
        title="Delete Memory"
        maxWidth="max-w-md"
      >
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 text-xs">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-rose-200">Are you sure?</p>
              <p className="mt-0.5">
                This will permanently delete this memory document and its embedding vectors from ChromaDB.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
            <button
              type="button"
              onClick={() => setDeletingMemoryId(null)}
              className="px-4 py-2 text-xs text-slate-400 hover:text-white rounded-xl transition-colors"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDelete}
              className="px-4 py-2 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-500 rounded-xl transition-colors"
            >
              Yes, Delete
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
