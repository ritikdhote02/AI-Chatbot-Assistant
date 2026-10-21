import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { useToast } from '../context/ToastContext';
import { MarkdownContent } from '../components/chat/MarkdownContent';
import { ExtractMemoriesModal } from '../components/chat/ExtractMemoriesModal';
import { CreateEpisodeModal } from '../components/chat/CreateEpisodeModal';
import {
  Send,
  Sparkles,
  Brain,
  ScrollText,
  Loader2,
  Bot,
  User,
  ArrowDown,
  Info,
  Clock,
  Layers,
  Zap,
} from 'lucide-react';

export function ChatView() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const [isExtractModalOpen, setIsExtractModalOpen] = useState(false);
  const [isEpisodeModalOpen, setIsEpisodeModalOpen] = useState(false);

  const messagesEndRef = useRef(null);
  const scrollContainerRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = (behavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  };

  const handleScroll = () => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 120;
    setShowScrollBottom(!isAtBottom);
  };

  // Load messages whenever conversationId changes
  const loadMessages = useCallback(async (id) => {
    if (!id) return;
    setLoadingMessages(true);
    try {
      const data = await api.conversations.getMessages(id);
      setMessages(data || []);
      setTimeout(() => scrollToBottom('auto'), 50);
    } catch (err) {
      toast.error(err.message || 'Could not load conversation messages', 'Error');
    } finally {
      setLoadingMessages(false);
    }
  }, [toast]);

  useEffect(() => {
    if (conversationId) {
      loadMessages(conversationId);
    } else {
      // Check if user has existing conversations or create a new one
      api.conversations.list().then((list) => {
        if (list && list.length > 0) {
          navigate(`/chat/${list[0].id}`, { replace: true });
        }
      });
    }
  }, [conversationId, loadMessages, navigate]);

  const handleSend = async (textToSend) => {
    const messageContent = (textToSend || inputText).trim();
    if (!messageContent || sending || !conversationId) return;

    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Optimistically append user message
    const tempUserMessage = {
      id: Date.now(),
      role: 'user',
      content: messageContent,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMessage]);
    setSending(true);
    setTimeout(() => scrollToBottom('smooth'), 50);

    try {
      const response = await api.conversations.sendMessage(conversationId, messageContent);

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.answer,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setTimeout(() => scrollToBottom('smooth'), 50);

      // Check if message count hits a multiple of 5 for subtle user delight
      const userCount = messages.filter((m) => m.role === 'user').length + 1;
      if (userCount > 0 && userCount % 5 === 0) {
        toast.info(
          'Message threshold reached: background memory extraction queued!',
          'Auto-Memory'
        );
      }
    } catch (err) {
      toast.error(err.message || 'Failed to send message', 'Chat Error');
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaInput = (e) => {
    setInputText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 180)}px`;
  };

  const userMessagesCount = messages.filter((m) => m.role === 'user').length;

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 relative overflow-hidden">
      {/* Top Conversation Header */}
      <header className="px-4 py-3 bg-slate-900/70 border-b border-slate-800 backdrop-blur-md flex items-center justify-between z-10 shrink-0">
        <div className="flex items-center gap-2.5 min-w-0 pr-2">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shrink-0" />
          <div className="min-w-0">
            <h2 className="text-sm font-semibold text-white truncate">
              Chat Point Session
            </h2>
            <div className="flex items-center gap-2 text-[11px] text-slate-400">
              <span>{userMessagesCount} user exchange{userMessagesCount === 1 ? '' : 's'}</span>
              <span>•</span>
              <span className="flex items-center gap-1 text-indigo-400">
                <Zap className="w-3 h-3" />
                Auto-extracts every 5 msgs
              </span>
            </div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setIsExtractModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-indigo-300 bg-indigo-950/60 hover:bg-indigo-900/70 border border-indigo-500/30 transition-all shadow-sm hover:border-indigo-400/50"
            title="Extract long-term memories immediately from this conversation"
          >
            <Brain className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Extract Memories</span>
          </button>

          <button
            type="button"
            onClick={() => setIsEpisodeModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium text-purple-300 bg-purple-950/60 hover:bg-purple-900/70 border border-purple-500/30 transition-all shadow-sm hover:border-purple-400/50"
            title="Summarize conversation into ChromaDB episodic memory"
          >
            <ScrollText className="w-3.5 h-3.5 text-purple-400" />
            <span className="hidden sm:inline">Summarize Episode</span>
          </button>
        </div>
      </header>

      {/* Message Stream */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6"
      >
        {loadingMessages ? (
          <div className="h-full flex flex-col items-center justify-center space-y-3 text-slate-400">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
            <p className="text-xs">Loading conversation history...</p>
          </div>
        ) : messages.length === 0 ? (
          /* Empty State / Starter Journey */
          <div className="max-w-2xl mx-auto py-8 sm:py-12 space-y-8 animate-in fade-in duration-500">
            <div className="text-center space-y-3">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-3xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 shadow-2xl shadow-indigo-500/30 border border-white/20">
                <Sparkles className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                How can I assist your knowledge today?
              </h1>
              <p className="text-xs sm:text-sm text-slate-400 max-w-lg mx-auto leading-relaxed">
                I continuously recall your preferences, goals, and facts across conversations using
                hybrid SQLite history and ChromaDB vector search.
              </p>
            </div>

            {/* Prompt Starter Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {[
                {
                  title: 'Store a Goal or Preference',
                  prompt: 'Remember that my primary goal is mastering distributed AI agents, and I prefer clean TypeScript & React architectures.',
                  tag: 'Long-term Memory',
                },
                {
                  title: 'Inspect Known Preferences',
                  prompt: 'What facts, decisions, and preferences do you currently recall about me from past conversations?',
                  tag: 'Vector Recall',
                },
                {
                  title: 'Architectural Analysis',
                  prompt: 'Explain the technical difference between our SQLite conversational context and ChromaDB episodic memory.',
                  tag: 'System Knowledge',
                },
                {
                  title: 'Summarization & Extraction',
                  prompt: 'Please explain when you trigger automatic structured memory extraction during our chats.',
                  tag: 'Cognitive Loop',
                },
              ].map((card, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSend(card.prompt)}
                  className="p-4 rounded-2xl glass-card text-left transition-all group flex flex-col justify-between"
                >
                  <div>
                    <span className="text-[10px] font-semibold text-indigo-400 uppercase tracking-wider">
                      {card.tag}
                    </span>
                    <h3 className="text-sm font-semibold text-white mt-1 group-hover:text-indigo-300 transition-colors">
                      {card.title}
                    </h3>
                    <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                      "{card.prompt}"
                    </p>
                  </div>
                  <span className="text-[11px] font-medium text-indigo-400 group-hover:translate-x-1 transition-transform inline-flex items-center gap-1 mt-3">
                    Click to ask →
                  </span>
                </button>
              ))}
            </div>

            {/* Info Pill */}
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400 flex items-center justify-center gap-2">
              <Info className="w-4 h-4 text-indigo-400 shrink-0" />
              <span>
                Memory Retrieval: Top 20 SQLite messages + Top 3 ChromaDB episodes + Top 5 durable memories.
              </span>
            </div>
          </div>
        ) : (
          /* Render Message Bubbles */
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((msg) => {
              const isUser = msg.role === 'user';

              return (
                <div
                  key={msg.id}
                  className={`flex gap-3.5 ${isUser ? 'justify-end' : 'justify-start'} animate-in fade-in duration-200`}
                >
                  {!isUser && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shrink-0 shadow-md border border-indigo-400/30">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}

                  <div
                    className={`max-w-[85%] sm:max-w-[78%] rounded-2xl p-4 sm:p-5 shadow-md ${
                      isUser
                        ? 'bg-gradient-to-br from-indigo-600 to-indigo-700 text-white rounded-tr-sm'
                        : 'bg-slate-900/90 border border-slate-800/90 text-slate-100 rounded-tl-sm'
                    }`}
                  >
                    {isUser ? (
                      <p className="text-sm leading-relaxed whitespace-pre-wrap break-words font-normal">
                        {msg.content}
                      </p>
                    ) : (
                      <MarkdownContent content={msg.content} />
                    )}

                    <div
                      className={`mt-2 flex items-center gap-1.5 text-[10px] ${
                        isUser ? 'text-indigo-200 justify-end' : 'text-slate-500 justify-start'
                      }`}
                    >
                      <Clock className="w-3 h-3" />
                      <span>
                        {new Date(msg.created_at).toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                  </div>

                  {isUser && (
                    <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 shadow-sm text-slate-300">
                      <User className="w-4 h-4" />
                    </div>
                  )}
                </div>
              );
            })}

            {/* Thinking / Streaming Indicator */}
            {sending && (
              <div className="flex gap-3.5 justify-start animate-in fade-in duration-200">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 flex items-center justify-center shrink-0 shadow-md border border-indigo-400/30">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl rounded-tl-sm p-4 flex items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" />
                    <span className="w-2 h-2 rounded-full bg-purple-400 animate-bounce [animation-delay:0.2s]" />
                    <span className="w-2 h-2 rounded-full bg-pink-400 animate-bounce [animation-delay:0.4s]" />
                  </div>
                  <span className="text-xs text-slate-400">
                    Retrieving semantic context & formulating response...
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Floating Scroll to Bottom button */}
      {showScrollBottom && (
        <button
          type="button"
          onClick={() => scrollToBottom('smooth')}
          className="absolute bottom-24 right-8 z-20 p-2.5 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white shadow-xl shadow-indigo-600/30 transition-all hover:scale-110"
          aria-label="Scroll to newest message"
        >
          <ArrowDown className="w-4 h-4" />
        </button>
      )}

      {/* Input Bar */}
      <div className="p-3 sm:p-4 bg-slate-900/80 border-t border-slate-800 backdrop-blur-md shrink-0">
        <div className="max-w-3xl mx-auto">
          <div className="relative flex items-end gap-2 bg-slate-950/90 border border-slate-800 rounded-2xl p-2 focus-within:border-indigo-500/80 focus-within:ring-1 focus-within:ring-indigo-500/20 transition-all shadow-xl">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputText}
              onChange={handleTextareaInput}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything or share a goal/preference... (Shift+Enter for newline)"
              className="flex-1 bg-transparent border-0 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none py-1.5 px-2 max-h-40 min-h-[38px]"
              maxLength={10000}
            />

            <button
              type="button"
              onClick={() => handleSend()}
              disabled={sending || !inputText.trim()}
              className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-40 disabled:hover:bg-indigo-600 shrink-0"
              aria-label="Send message"
            >
              {sending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>

          <div className="flex items-center justify-between text-[11px] text-slate-500 px-2 mt-1.5">
            <span>Press Enter to send, Shift+Enter for new line</span>
            <span>{inputText.length}/10,000</span>
          </div>
        </div>
      </div>

      {/* Extract Memories Modal */}
      <ExtractMemoriesModal
        isOpen={isExtractModalOpen}
        onClose={() => setIsExtractModalOpen(false)}
        conversationId={conversationId}
      />

      {/* Create Episode Modal */}
      <CreateEpisodeModal
        isOpen={isEpisodeModalOpen}
        onClose={() => setIsEpisodeModalOpen(false)}
        conversationId={conversationId}
      />
    </div>
  );
}
