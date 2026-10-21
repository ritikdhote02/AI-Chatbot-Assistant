import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../api/client';
import { CheckCircle2, AlertCircle, Loader2, Sparkles, KeyRound } from 'lucide-react';

export function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const tokenFromUrl = searchParams.get('token') || '';
  const [token, setToken] = useState(tokenFromUrl);
  const [status, setStatus] = useState(tokenFromUrl ? 'verifying' : 'idle');
  const [message, setMessage] = useState('');

  const executeVerification = async (tokenToVerify) => {
    if (!tokenToVerify) return;
    setStatus('verifying');
    setMessage('');

    try {
      await api.auth.verifyEmail(tokenToVerify);
      setStatus('success');
      setMessage('Your email address has been successfully verified! You can now log in.');
    } catch (err) {
      setStatus('error');
      setMessage(err.message || 'The verification link is invalid or has expired.');
    }
  };

  useEffect(() => {
    if (tokenFromUrl) {
      executeVerification(tokenFromUrl);
    }
  }, [tokenFromUrl]);

  const handleManualSubmit = (e) => {
    e.preventDefault();
    if (token.trim()) {
      executeVerification(token.trim());
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-slate-950">
      <div className="w-full max-w-md relative z-10">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 shadow-xl shadow-indigo-500/20 mb-3 border border-indigo-400/30">
            <Sparkles className="w-7 h-7 text-white" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Chat<span className="gradient-text"> Point</span>
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Email Verification
          </p>
        </div>

        <div className="glass-panel p-6 sm:p-8 rounded-3xl shadow-2xl relative text-center">
          {status === 'verifying' && (
            <div className="py-8 space-y-4">
              <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mx-auto" />
              <h2 className="text-lg font-bold text-white">Verifying your email...</h2>
              <p className="text-xs text-slate-400">Validating token with server...</p>
            </div>
          )}

          {status === 'success' && (
            <div className="py-4 space-y-4">
              <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto border border-emerald-500/30">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-white">Email Verified!</h2>
              <p className="text-sm text-slate-300">{message}</p>
              <div className="pt-2">
                <Link
                  to="/login"
                  className="inline-flex items-center justify-center w-full py-3 px-4 rounded-xl font-semibold text-sm text-white bg-indigo-600 hover:bg-indigo-500 transition-colors shadow-lg shadow-indigo-600/30"
                >
                  Proceed to Sign In →
                </Link>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="py-4 space-y-4">
              <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center mx-auto border border-rose-500/30">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-white">Verification Failed</h2>
              <p className="text-sm text-rose-300">{message}</p>
              <div className="pt-2 flex flex-col gap-2">
                <Link
                  to="/login"
                  className="w-full py-2.5 px-4 rounded-xl text-center font-semibold text-xs text-white bg-slate-800 hover:bg-slate-700 transition-colors"
                >
                  Back to Sign In
                </Link>
              </div>
            </div>
          )}

          {status === 'idle' && (
            <form onSubmit={handleManualSubmit} className="space-y-4 text-left">
              <h2 className="text-lg font-bold text-white text-center">Verify Email Token</h2>
              <p className="text-xs text-slate-400 text-center">
                Paste the token code from your verification email below:
              </p>
              <div>
                <label htmlFor="verify-token" className="block text-xs font-semibold uppercase tracking-wider text-slate-300 mb-1.5">
                  Token Code
                </label>
                <div className="relative">
                  <KeyRound className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                  <input
                    id="verify-token"
                    type="text"
                    required
                    value={token}
                    onChange={(e) => setToken(e.target.value)}
                    placeholder="Paste verification token..."
                    className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-slate-900/90 border border-slate-700 text-white placeholder-slate-500 text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-xl font-semibold text-xs text-white bg-indigo-600 hover:bg-indigo-500 transition-colors"
              >
                Verify Token
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
