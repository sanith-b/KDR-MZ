import React, { useState } from 'react';
import { X, Send, Sparkles, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

interface RequestModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const RequestModal: React.FC<RequestModalProps> = ({ isOpen, onClose }) => {
  const [dramaName, setDramaName] = useState('');
  const [details, setDetails] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!dramaName.trim()) return;

    setLoading(true);
    setStatus('idle');
    try {
      await api.createRequest(dramaName.trim(), details.trim());
      setStatus('success');
      setMessage('Your request has been submitted! Bot moderators will review it shortly.');
      setTimeout(() => {
        setDramaName('');
        setDetails('');
        setStatus('idle');
        onClose();
      }, 2500);
    } catch (err: any) {
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Failed to submit request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-lg w-full shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-slate-400 hover:text-white p-1 rounded-full hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2 text-rose-400 mb-1">
          <Sparkles className="w-4 h-4" />
          <span className="text-xs font-bold uppercase tracking-wider">K-Drama Request Center</span>
        </div>
        <h2 className="text-xl font-extrabold text-white">Can't find your favorite drama?</h2>
        <p className="text-sm text-slate-400 mt-1">
          Submit the title below. Our automated system queries TMDb and notifies our moderators instantly.
        </p>

        {status === 'success' ? (
          <div className="my-6 p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 flex items-start gap-3 text-emerald-300">
            <CheckCircle className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
            <div className="text-sm font-medium">{message}</div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            {status === 'error' && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/30 flex items-center gap-2 text-rose-300 text-sm">
                <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
                <span>{message}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                Drama Title *
              </label>
              <input
                type="text"
                required
                value={dramaName}
                onChange={(e) => setDramaName(e.target.value)}
                placeholder="e.g. Lovely Runner, Queen of Tears, Goblin"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500/80 focus:ring-1 focus:ring-rose-500/50"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
                Extra Details (Optional)
              </label>
              <textarea
                rows={3}
                value={details}
                onChange={(e) => setDetails(e.target.value)}
                placeholder="Release year, requested quality, specific episodes, or notes..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500/80 focus:ring-1 focus:ring-rose-500/50 resize-none"
              />
            </div>

            <div className="pt-2 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || !dramaName.trim()}
                className="px-5 py-2 rounded-xl text-sm font-bold bg-gradient-to-r from-rose-600 to-pink-600 hover:from-rose-500 hover:to-pink-500 text-white shadow-lg shadow-rose-600/25 flex items-center gap-2 disabled:opacity-50 transition-all"
              >
                <Send className="w-4 h-4" />
                <span>{loading ? 'Submitting...' : 'Send Request'}</span>
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
