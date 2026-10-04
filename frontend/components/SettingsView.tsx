'use client';

import React, { useState, useEffect } from 'react';
import { Settings, Server, ShieldCheck, Database, RefreshCw, CheckCircle2, AlertTriangle, Table as TableIcon } from 'lucide-react';
import { checkBackendHealth, fetchSchema, API_BASE_URL } from '../lib/api';

export default function SettingsView() {
  const [health, setHealth] = useState<{ status: string; service?: string; error?: string } | null>(null);
  const [schemaData, setSchemaData] = useState<{ total_tables: number; schema: Record<string, any> } | null>(null);
  const [loading, setLoading] = useState(false);
  const [exportFormat, setExportFormat] = useState<'csv' | 'json'>('json');

  const checkStatus = async () => {
    setLoading(true);
    try {
      const res = await checkBackendHealth();
      setHealth(res);
      const schemaRes = await fetchSchema();
      setSchemaData(schemaRes);
    } catch (err: any) {
      setHealth({ status: 'error', error: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 space-y-6 font-sans">
      {/* Header */}
      <div className="pb-4 border-b border-slate-800/80">
        <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono font-semibold uppercase tracking-wider mb-1">
          <Settings className="w-3.5 h-3.5" />
          <span>System Diagnostics & Preferences</span>
        </div>
        <h1 className="text-2xl font-bold text-slate-100">Application Settings</h1>
        <p className="text-xs text-slate-400 mt-1">
          Inspect backend API connections, database schemas, and export preferences.
        </p>
      </div>

      <div className="space-y-6 max-w-4xl">
        {/* API Server Diagnostics Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
              <Server className="w-4 h-4 text-cyan-400" />
              <span>Backend API Server Endpoint</span>
            </h3>
            <button
              onClick={checkStatus}
              disabled={loading}
              className="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 hover:border-cyan-500/50 text-slate-300 text-xs font-semibold flex items-center space-x-1.5"
            >
              <RefreshCw className={`w-3 h-3 ${loading ? 'animate-spin' : ''}`} />
              <span>Test Endpoint</span>
            </button>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs font-mono">
            <div>
              <span className="text-slate-500 block">Base URL:</span>
              <span className="text-cyan-300 font-bold">{API_BASE_URL}</span>
            </div>

            {health?.status === 'ok' ? (
              <div className="flex items-center space-x-2 text-emerald-400 font-bold bg-emerald-950/60 px-3 py-1 rounded-lg border border-emerald-800">
                <CheckCircle2 className="w-4 h-4" />
                <span>ONLINE ({health.service})</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-rose-400 font-bold bg-rose-950/60 px-3 py-1 rounded-lg border border-rose-800">
                <AlertTriangle className="w-4 h-4" />
                <span>OFFLINE</span>
              </div>
            )}
          </div>
        </div>

        {/* Database Schema Visualizer Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
            <Database className="w-4 h-4 text-blue-400" />
            <span>MIMIC-IV Active Database Schema ({schemaData?.total_tables || 0} Tables)</span>
          </h3>

          {schemaData ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              {Object.entries(schemaData.schema).map(([tableName, tableInfo]) => {
                const columns = tableInfo.columns || [];
                const rowCount = tableInfo.row_count ?? 0;
               return (
  <div
    key={tableName}
    className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 space-y-1"
  >
    <div className="flex items-center justify-between font-mono font-bold text-cyan-300">
      <span>{tableName}</span>
      <span className="text-[10px] text-slate-500">
        {columns.length} fields · {rowCount.toLocaleString()} rows
      </span>
    </div>

    <div className="flex flex-wrap gap-1 pt-1">
      {columns.slice(0, 5).map(
        (col: { name: string }, cIdx: number) => (
          <span
            key={cIdx}
            className="px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 font-mono text-[10px]"
          >
            {col.name}
          </span>
        )
      )}

      {columns.length > 5 && (
        <span className="text-[10px] text-slate-500 font-mono self-center">
          +{columns.length - 5} more
        </span>
      )}
    </div>
  </div>
);
              })}
            </div>
          ) : (
            <div className="text-xs text-slate-500 py-4 text-center">Loading database schema...</div>
          )}
        </div>

        {/* Export Preference Card */}
        <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-purple-400" />
            <span>Export & Audit Format Preferences</span>
          </h3>

          <div className="flex items-center space-x-4 text-xs font-mono">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                name="exportFormat"
                value="json"
                checked={exportFormat === 'json'}
                onChange={() => setExportFormat('json')}
                className="text-cyan-500"
              />
              <span className="text-slate-200 font-bold">JSON Provenance Stream</span>
            </label>

            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                name="exportFormat"
                value="csv"
                checked={exportFormat === 'csv'}
                onChange={() => setExportFormat('csv')}
                className="text-cyan-500"
              />
              <span className="text-slate-200 font-bold">CSV Cohort Table</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
}
