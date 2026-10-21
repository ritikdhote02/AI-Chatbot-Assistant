import React, { useState, useEffect, useCallback } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../api/client';
import { BrainInspectorModal } from '../chat/BrainInspectorModal';
import {
  MessageSquare,
  Plus,
  Brain,
  ScrollText,
  Cpu,
  LogOut,
  Menu,
  X,
  Search,
  Sparkles,
  ChevronRight,
  ShieldCheck,
  Loader2,
} from 'lucide-react';

export function AppLayout() {
  const { user, logout } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const [conversations, setConversations] = useState([]);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isBrainModalOpen, setIsBrainModalOpen] = useState(false);
  const [creatingChat, setCreatingChat] = useState(false);

  const fetchConversations = useCallback(async () => {
    try {
      const data = await api.conversations.list();
      // Sort by updated_at or created_at descending
      const sorted = (data || []).sort(
        (a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at)
      );
      setConversations(sorted);
    } catch (err) {
      console.error('Failed to load conversations:', err);
    } finally {
      setLoadingConversations(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations, location.pathname]);

  const handleCreateNewChat = async () => {
    setCreatingChat(true);
    try {
      const newConv = await api.conversations.create();
      setConversations((prev) => [newConv, ...prev]);
      navigate(`/chat/${newConv.id}`);
      setMobileMenuOpen(false);
      toast.success('Started a fresh conversation.', 'New Chat');
    } catch (err) {
      toast.error(err.message || 'Could not create new chat', 'Error');
    } finally {
      setCreatingChat(false);
    }
  };

  const filteredConversations = conversations.filter((c) =>
    (c.title || 'New conversation').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const isCurrentChat = (id) => location.pathname === `/chat/${id}`;

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      {/* Mobile Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-72 bg-slate-900/90 border-r border-slate-800 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 flex items-center justify-between border-b border-slate-800/80">
          <NavLink to="/chat" className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20 border border-indigo-400/30">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-base font-extrabold text-white tracking-tight">
                Chat<span className="gradient-text"> Point</span>
              </span>
              <span className="block text-[10px] text-slate-400 tracking-wider uppercase font-semibold">
                Knowledge Assistant
              </span>
            </div>
          </NavLink>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(false)}
            className="lg:hidden p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action: New Chat Button */}
        <div className="p-3">
          <button
            type="button"
            onClick={handleCreateNewChat}
            disabled={creatingChat}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl font-semibold text-xs text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50"
          >
            {creatingChat ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Creating...</span>
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                <span>New Conversation</span>
              </>
            )}
          </button>
        </div>

        {/* Global Navigation Links */}
        <div className="px-3 py-1 space-y-1">
          <NavLink
            to="/memories"
            onClick={() => setMobileMenuOpen(false)}
            className={({ isActive }) =>
              `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-indigo-950/60 text-indigo-300 border border-indigo-500/30 font-semibold'
                  : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
              }`
            }
          >
            <div className="flex items-center gap-2.5">
              <Brain className="w-4 h-4 text-indigo-400" />
              <span>Memory Vault</span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">
              ChromaDB
            </span>
          </NavLink>

          <NavLink
            to="/episodes"
            onClick={() => setMobileMenuOpen(false)}
            className={({ isActive }) =>
              `flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                isActive
                  ? 'bg-purple-950/60 text-purple-300 border border-purple-500/30 font-semibold'
                  : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
              }`
            }
          >
            <div className="flex items-center gap-2.5">
              <ScrollText className="w-4 h-4 text-purple-400" />
              <span>Episodic Memories</span>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20 font-mono">
              Summaries
            </span>
          </NavLink>

          <button
            type="button"
            onClick={() => {
              setIsBrainModalOpen(true);
              setMobileMenuOpen(false);
            }}
            className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium text-slate-300 hover:bg-slate-800/60 hover:text-white transition-colors"
          >
            <div className="flex items-center gap-2.5">
              <Cpu className="w-4 h-4 text-amber-400" />
              <span>Brain Architecture</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-500" />
          </button>
        </div>

        {/* Conversation List Header & Search */}
        <div className="px-3 pt-3 pb-1 border-t border-slate-800/80 mt-2">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-wider text-slate-400 px-1 mb-2">
            <span>Conversations</span>
            <span className="font-mono text-slate-500">{conversations.length}</span>
          </div>

          <div className="relative mb-2">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search chats..."
              className="w-full pl-8 pr-2.5 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500/60"
            />
          </div>
        </div>

        {/* Scrollable Conversation List */}
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          {loadingConversations ? (
            <div className="p-4 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              Loading chats...
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">
              {searchQuery ? 'No matching chats found' : 'No chats yet. Start a new one!'}
            </div>
          ) : (
            filteredConversations.map((conv) => (
              <NavLink
                key={conv.id}
                to={`/chat/${conv.id}`}
                onClick={() => setMobileMenuOpen(false)}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs transition-colors ${
                  isCurrentChat(conv.id)
                    ? 'bg-slate-800 text-white font-medium border border-slate-700/80 shadow-sm'
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0 pr-2">
                  <MessageSquare
                    className={`w-3.5 h-3.5 shrink-0 ${
                      isCurrentChat(conv.id) ? 'text-indigo-400' : 'text-slate-500'
                    }`}
                  />
                  <span className="truncate">{conv.title || 'New conversation'}</span>
                </div>
                <span className="text-[10px] text-slate-600 group-hover:text-slate-500 shrink-0">
                  {new Date(conv.created_at).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                </span>
              </NavLink>
            ))
          )}
        </div>

        {/* User Footer Profile */}
        <div className="p-3 border-t border-slate-800 bg-slate-900/60">
          <div className="flex items-center justify-between">
            <div className="min-w-0 pr-2">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-white truncate">
                  {user?.name || 'User'}
                </span>
                {user?.is_email_verified && (
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" title="Verified Account" />
                )}
              </div>
              <p className="text-[11px] text-slate-400 truncate">{user?.email}</p>
            </div>
            <button
              type="button"
              onClick={logout}
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden relative">
        {/* Mobile Header Bar */}
        <div className="lg:hidden flex items-center justify-between p-3.5 bg-slate-900 border-b border-slate-800 z-30">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            className="p-1.5 text-slate-300 hover:text-white rounded-lg hover:bg-slate-800"
            aria-label="Open navigation sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-bold text-white">Chat Point</span>
          </div>
          <button
            type="button"
            onClick={handleCreateNewChat}
            className="p-1.5 text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 rounded-lg"
            aria-label="New chat"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>

        <main className="flex-1 flex flex-col min-h-0 overflow-hidden">
          <Outlet />
        </main>
      </div>

      {/* Brain Inspector Modal */}
      <BrainInspectorModal
        isOpen={isBrainModalOpen}
        onClose={() => setIsBrainModalOpen(false)}
      />
    </div>
  );
}
