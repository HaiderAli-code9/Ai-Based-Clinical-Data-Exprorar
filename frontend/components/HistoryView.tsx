'use client';

import React, { useEffect, useState } from 'react';
import { History, Clock, ArrowRight, Trash2, Search, CheckCircle2, Loader2 } from 'lucide-react';
import { getHistory, HistoryItem } from '../lib/api';

interface HistoryViewProps {
  onSelectQuery: (queryText: string) => void;
  onClearHistory?: () => void; // optional, we'll handle clearing via backend later
}

export default function HistoryView({ onSelectQuery, onClearHistory }: HistoryViewProps) {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getHistory();
      setHistory(data.history);
    } catch (err: any) {
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const handleClear = () => {
    // For now, just clear local state; you can later implement a DELETE endpoint
    setHistory([]);
    if (onClearHistory) onClearHistory();
  };

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 space-y-6 font-sans">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono font-semibold uppercase tracking-wider mb-1">
            <History className="w-3.5 h-3.5" />
            <span>Audit Trail & Session Memory</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Query Session History</h1>
          <p className="text-xs text-slate-400 mt-1">
            Review past cohort queries, execution durations, row outputs, and data quality findings.
          </p>
        </div>

        {history.length > 0 && (
          <button
            onClick={handleClear}
            className="px-3.5 py-2 text-xs font-semibold rounded-lg bg-rose-950/40 border border-rose-800/60 hover:bg-rose-900/60 text-rose-300 transition-all flex items-center space-x-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Loading */}
      {loading && (
        <div className="py-20 text-center space-y-3 bg-slate-900/40 border border-slate-800 rounded-2xl">
          <Loader2 className="w-10 h-10 text-cyan-400 mx-auto animate-spin" />
          <h3 className="text-sm font-bold text-slate-300">Loading history...</h3>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="p-5 rounded-2xl bg-rose-950/30 border border-rose-800/60 text-rose-200 flex items-start space-x-3">
          <Search className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-sm text-rose-300">Failed to Load History</h4>
            <p className="text-xs mt-1 text-rose-200/80">{error}</p>
          </div>
        </div>
      )}

      {/* History List */}
      {!loading && !error && (
        <>
          {history.length === 0 ? (
            <div className="py-20 text-center space-y-3 bg-slate-900/40 border border-slate-800 rounded-2xl">
              <History className="w-10 h-10 text-slate-600 mx-auto" />
              <h3 className="text-sm font-bold text-slate-300">No Query History Yet</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Execute clinical queries in the New Analysis workspace to populate your interactive session audit log.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition-all space-y-3 text-xs"
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <span className="font-bold text-slate-100 text-sm block">{item.query}</span>
                      <div className="flex items-center space-x-3 font-mono text-slate-400 text-[11px]">
                        <span className="text-cyan-400 font-bold">{item.total_rows} Records</span>
                        <span>•</span>
                        <span className="flex items-center space-x-1">
                          <Clock className="w-3 h-3 text-slate-500" />
                          <span>{item.execution_time_ms} ms</span>
                        </span>
                        <span>•</span>
                        <span className="text-amber-400">
                          {item.quality_flags_count} Quality Flags
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => onSelectQuery(item.query)}
                      className="px-3 py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 font-semibold text-xs transition-all flex items-center space-x-1.5 shrink-0"
                    >
                      <span>Rerun</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* SQL snippet */}
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-[11px] text-slate-400 truncate">
                    {item.sql_query}
                  </div>

                  <div className="text-[10px] text-slate-500 flex justify-between">
                    <span>Executed: {new Date(item.created_at).toLocaleString()}</span>
                    <span>ID: #{item.id}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}