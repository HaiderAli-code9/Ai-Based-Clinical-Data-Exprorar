'use client';

import React, { useEffect, useState } from 'react';
import { 
  BarChart3, 
  Database, 
  ShieldAlert, 
  Layers, 
  Activity, 
  AlertTriangle, 
  RefreshCw, 
  FileCheck, 
  Tag, 
  CheckCircle2, 
  HelpCircle,
  Table as TableIcon
} from 'lucide-react';
import { fetchDatasetInsights, fetchQualityRules, InsightsResponse, QualityRule } from '../lib/api';

export default function DatasetInsightsView() {
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [rules, setRules] = useState<QualityRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'missingness' | 'units' | 'coding' | 'rules'>('overview');

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [insightsData, rulesData] = await Promise.all([
        fetchDatasetInsights(),
        fetchQualityRules(),
      ]);
      setInsights(insightsData);
      setRules(rulesData.rules || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load dataset insights from backend server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono font-semibold uppercase tracking-wider mb-1">
            <BarChart3 className="w-3.5 h-3.5" />
            <span>Database Insights Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Dataset Health & Quality Audit</h1>
          <p className="text-xs text-slate-400 mt-1">
            Independent, dataset-level analysis of all 10 MIMIC-IV clinical tables, unit variations, and coding patterns.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500/50 text-slate-300 hover:text-cyan-300 transition-all flex items-center space-x-2 self-start"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Analysis</span>
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div className="py-16 text-center space-y-4 animate-pulse">
          <div className="w-12 h-12 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-400 flex items-center justify-center mx-auto">
            <BarChart3 className="w-6 h-6 animate-spin" />
          </div>
          <h3 className="text-sm font-bold text-slate-200">Analyzing Clinical Database Health</h3>
          <p className="text-xs text-slate-400">Scanning 912,284 rows across 10 tables for data completeness and unit variations...</p>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="p-5 rounded-2xl bg-rose-950/30 border border-rose-800/60 text-rose-200 flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-sm text-rose-300">Insights Service Offline</h4>
            <p className="text-xs mt-1 text-rose-200/80">{error}</p>
          </div>
        </div>
      )}

      {/* Content */}
      {insights && !loading && (
        <div className="space-y-6 animate-fadeIn">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/40 transition-all">
              <span className="text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider">Total Tables</span>
              <p className="text-3xl font-extrabold text-cyan-400 mt-2 font-mono">{insights.database_overview.total_tables}</p>
              <p className="text-[11px] text-slate-500 mt-1">MIMIC-IV clinical schema</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-blue-500/40 transition-all">
              <span className="text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider">Total Records</span>
              <p className="text-3xl font-extrabold text-blue-400 mt-2 font-mono">{insights.database_overview.total_rows.toLocaleString()}</p>
              <p className="text-[11px] text-slate-500 mt-1">Largest: {insights.database_overview.largest_table}</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/40 transition-all">
              <span className="text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider">Missingness Issues</span>
              <p className="text-3xl font-extrabold text-amber-400 mt-2 font-mono">{insights.missingness_report.length}</p>
              <p className="text-[11px] text-slate-500 mt-1">Columns with missing values</p>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-purple-500/40 transition-all">
              <span className="text-[11px] font-mono font-semibold text-slate-400 uppercase tracking-wider">Quality Flags</span>
              <p className="text-3xl font-extrabold text-purple-400 mt-2 font-mono">
                {insights.quality_summary?.total_flags ?? 0}
              </p>
              <p className="text-[11px] text-slate-500 mt-1">Dataset-level data-quality flags detected</p>
            </div>
          </div>

          {/* Navigation Bar */}
          <div className="flex space-x-2 border-b border-slate-800 pb-3">
            {[
              { id: 'overview', label: 'Table Inventory' },
              { id: 'missingness', label: `Missingness (${insights.missingness_report.length})` },
              { id: 'units', label: 'Unit Variation' },
              { id: 'coding', label: 'ICD Coding Patterns' },
              { id: 'rules', label: `Quality Rules Registry (${rules.length})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-4 py-2 rounded-lg font-semibold text-xs transition-all ${
                  activeTab === tab.id
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* TAB 1: Table Inventory (no bar charts) */}
          {activeTab === 'overview' && (
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                <TableIcon className="w-4 h-4 text-cyan-400" />
                <span>Clinical Database Tables</span>
              </h3>

              <div className="grid grid-cols-1 gap-4">
                {insights.table_inventory.map((t, idx) => (
                  <div key={idx} className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3 text-xs">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div className="space-y-1">
                        <span className="font-bold text-slate-100 font-mono text-sm">{t.table_name}</span>
                        <p className="text-slate-400 text-[11px] leading-relaxed max-w-2xl">{t.purpose}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded bg-slate-900 text-cyan-400 border border-slate-800 font-mono">
                          {t.row_count.toLocaleString()} rows
                        </span>
                        <span className="px-2 py-0.5 rounded bg-slate-900 text-blue-300 border border-slate-800 font-mono">
                          {t.column_count} columns
                        </span>
                      </div>
                    </div>

                    {/* REMOVED: the data_summary section with progress bars */}

                    <div className="flex flex-wrap gap-1 pt-1">
                      {t.columns.slice(0, 8).map((col, cIdx) => (
                        <span key={cIdx} className="px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 font-mono text-[10px]">
                          {col.name} ({col.type})
                        </span>
                      ))}
                      {t.columns.length > 8 && (
                        <span className="text-[10px] text-slate-500 font-mono self-center">
                          +{t.columns.length - 8} more
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 2: Missingness Analysis */}
          {activeTab === 'missingness' && (
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <span>Field Missingness Report</span>
              </h3>

              <div className="overflow-x-auto rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-[#0a0e1a] text-slate-400 font-mono text-[11px] border-b border-slate-800 uppercase">
                    <tr>
                      <th className="px-4 py-3">Table Name</th>
                      <th className="px-4 py-3">Column Name</th>
                      <th className="px-4 py-3">Missing Rows</th>
                      <th className="px-4 py-3">Missing %</th>
                      <th className="px-4 py-3">Severity</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 bg-slate-950/40 font-mono">
                    {insights.missingness_report.map((m, idx) => (
                      <tr key={idx} className="hover:bg-slate-900/60 transition-colors">
                        <td className="px-4 py-2.5 font-bold text-slate-200">{m.table_name}</td>
                        <td className="px-4 py-2.5 text-cyan-300">{m.column_name}</td>
                        <td className="px-4 py-2.5">{m.missing_rows.toLocaleString()} / {m.total_rows.toLocaleString()}</td>
                        <td className="px-4 py-2.5 font-bold text-amber-400">{m.missing_pct}%</td>
                        <td className="px-4 py-2.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            m.severity === 'HIGH' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                            m.severity === 'MEDIUM' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                            'bg-blue-950 text-blue-300 border border-blue-800'
                          }`}>
                            {m.severity}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: Unit Variation */}
          {activeTab === 'units' && (
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                <Tag className="w-4 h-4 text-purple-400" />
                <span>Unit Variation Audit (Lab & Chart Measurements)</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-200">Lab Events Unit Variation</span>
                    <span className="px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800 font-mono font-bold">
                      {insights.unit_variation.labevents_unit_variation.items_with_multiple_units} Multiple Units
                    </span>
                  </div>

                  <div className="space-y-2">
                    {insights.unit_variation.labevents_unit_variation.details.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                        <div className="flex justify-between font-bold text-cyan-300 font-mono">
                          <span>{item.label}</span>
                          <span>ID: {item.item_id}</span>
                        </div>
                        <div className="flex flex-wrap gap-2 text-[11px] font-mono text-slate-400 pt-1">
                          {Object.entries(item.unit_counts).map(([unitName, count]) => (
                            <span key={unitName} className="px-2 py-0.5 bg-slate-950 rounded border border-slate-800">
                              {unitName || 'null'}: {count} records
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-slate-200">Chart Events Unit Variation</span>
                    <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono font-bold">
                      {insights.unit_variation.chartevents_unit_variation.items_with_multiple_units} Variations
                    </span>
                  </div>
                  <p className="text-slate-400 text-xs">
                    Chart events units (mmHg, bpm, %, Deg F) are consistent across the demo cohort dataset.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: ICD Coding */}
          {activeTab === 'coding' && (
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                <FileCheck className="w-4 h-4 text-blue-400" />
                <span>ICD Diagnosis Coding Patterns</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <span className="font-bold text-slate-200">ICD Version Distribution</span>
                  <div className="space-y-2 font-mono">
                    {Object.entries(insights.coding_patterns.icd_version_distribution).map(([ver, cnt]) => (
                      <div key={ver} className="flex justify-between items-center p-2 rounded bg-slate-900">
                        <span>ICD-{ver} Code Records:</span>
                        <span className="font-bold text-cyan-400">{cnt.toLocaleString()}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <span className="font-bold text-slate-200">Mixed ICD Version Auditing</span>
                  <p className="text-slate-400">
                    Admissions with mixed ICD-9 and ICD-10 diagnosis codes during the same stay:
                  </p>
                  <div className="p-3 rounded bg-slate-900 font-mono font-bold text-emerald-400 flex items-center space-x-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>{insights.coding_patterns.admissions_with_mixed_icd_versions} Mixed Admissions Flagged</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: Quality Rules Registry */}
          {activeTab === 'rules' && (
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
              <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                <ShieldAlert className="w-4 h-4 text-cyan-400" />
                <span>Registered Quality Audit Rules (12 Active)</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {rules.map((rule) => (
                  <div key={rule.rule_id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-cyan-400 font-bold">{rule.rule_id}</span>
                      <span className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${
                        rule.severity === 'ERROR' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                        rule.severity === 'WARNING' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                        'bg-blue-950 text-blue-300 border border-blue-800'
                      }`}>
                        {rule.severity}
                      </span>
                    </div>
                    <h4 className="font-bold text-slate-100">{rule.name}</h4>
                    <p className="text-slate-400 leading-relaxed">{rule.description}</p>
                    <div className="flex justify-between text-[10px] text-slate-500 font-mono pt-1">
                      <span>Category: {rule.category}</span>
                      <span>v{rule.version}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}