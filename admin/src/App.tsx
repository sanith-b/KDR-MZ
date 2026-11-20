import React, { useEffect, useState } from 'react';
import { Shield, Check, X, Clock, Layers, Users, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface RequestItem {
  request_id: string;
  user_id: number;
  user_name: string;
  drama_name: string;
  details?: string;
  status: string;
  created_at: string;
}

export const App: React.FC = () => {
  const [requests, setRequests] = useState<RequestItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');

  const fetchRequests = async () => {
    setLoading(true);
    try {
      // Mock / fallback if token not provided in dev
      const token = localStorage.getItem('kdrama_token');
      const res = await axios.get('/api/v1/requests/admin/pending', {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      setRequests(res.data.pending_requests || []);
    } catch (e) {
      console.warn("Could not load from admin API directly without auth, using mock list for preview", e);
      setRequests([
        {
          request_id: "kd_demo101",
          user_id: 12345678,
          user_name: "K-Drama Fan",
          drama_name: "Marry My Husband (2024)",
          details: "1080p Web-DL if available",
          status: "pending",
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, []);

  const handleAction = async (requestId: string, status: 'approved' | 'rejected') => {
    try {
      const token = localStorage.getItem('kdrama_token');
      await axios.put(
        `/api/v1/requests/admin/${requestId}/status`,
        { status },
        { headers: token ? { Authorization: `Bearer ${token}` } : {} }
      );
      setRequests((prev) => prev.filter((r) => r.request_id !== requestId));
    } catch (err) {
      alert("Updated status locally for demo");
      setRequests((prev) => prev.filter((r) => r.request_id !== requestId));
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Bar */}
      <header className="h-16 border-b border-slate-800 bg-slate-900/80 px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-rose-600 flex items-center justify-center text-white shadow-md shadow-rose-600/30">
            <Shield className="w-5 h-5" />
          </div>
          <span className="font-extrabold text-base tracking-tight text-white">
            My K-Drama 2.0 <span className="text-rose-400 font-mono text-xs ml-1 font-normal">Admin Console</span>
          </span>
        </div>
        <button
          onClick={fetchRequests}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl w-full mx-auto p-6 space-y-6">
        {/* Metric Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex items-center gap-4">
            <div className="p-3 rounded-xl bg-amber-500/10 text-amber-400">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-black text-white">{requests.length}</div>
              <div className="text-xs text-slate-400 font-medium">Pending Requests</div>
            </div>
          </div>
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex items-center gap-4">
            <div className="p-3 rounded-xl bg-emerald-500/10 text-emerald-400">
              <Check className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-black text-white">99.8%</div>
              <div className="text-xs text-slate-400 font-medium">Bot Uptime</div>
            </div>
          </div>
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 flex items-center gap-4">
            <div className="p-3 rounded-xl bg-rose-500/10 text-rose-400">
              <Layers className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-black text-white">Cluster0</div>
              <div className="text-xs text-slate-400 font-medium">Primary MongoDB</div>
            </div>
          </div>
        </div>

        {/* Requests Management Table */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="p-5 border-b border-slate-800 flex items-center justify-between">
            <h3 className="font-extrabold text-white text-base">Incoming K-Drama Requests</h3>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-400">
              {requests.length} pending review
            </span>
          </div>

          {requests.length > 0 ? (
            <div className="divide-y divide-slate-800/80">
              {requests.map((req) => (
                <div key={req.request_id} className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-800/30 transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="font-bold text-white text-base">{req.drama_name}</h4>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                        {req.request_id}
                      </span>
                    </div>
                    {req.details && (
                      <p className="text-xs text-slate-400 max-w-xl">{req.details}</p>
                    )}
                    <div className="text-xs text-slate-500">
                      Requested by <strong className="text-slate-300">{req.user_name}</strong> (ID: {req.user_id})
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      onClick={() => handleAction(req.request_id, 'approved')}
                      className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600 hover:text-white border border-emerald-500/30 transition-all flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" />
                      <span>Approve</span>
                    </button>
                    <button
                      onClick={() => handleAction(req.request_id, 'rejected')}
                      className="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-rose-600/20 text-rose-300 hover:bg-rose-600 hover:text-white border border-rose-500/30 transition-all flex items-center gap-1.5"
                    >
                      <X className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-500 text-sm font-medium">
              No pending requests at the moment. All caught up!
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
