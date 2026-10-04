'use client';

import React, { useState } from 'react';
import {
  Search,
  Send,
  Sparkles,
  Database,
  ShieldAlert,
  Code,
  CheckCircle2,
  AlertTriangle,
  Info,
  FileText,
  GitCommit,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Table as TableIcon,
  Clock,
  Layers,
  HelpCircle,
  Activity
} from 'lucide-react';
import { sendQuery, ChatResponse, saveHistory } from '../lib/api'; // <-- added saveHistory

interface NewAnalysisViewProps {
  onSaveToHistory?: (response: ChatResponse) => void;
}

export default function NewAnalysisView({ onSaveToHistory }: NewAnalysisViewProps) {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copiedSql, setCopiedSql] = useState(false);
  const [showSql, setShowSql] = useState(true);
  const [activeTab, setActiveTab] = useState<'source' | 'quality' | 'provenance'>('source');
  const [tablePage, setTablePage] = useState(1);

  const samplePrompts = [
    "Show me all female patients over 65",
    "Find patients with a creatinine measurement above 1.5",
    "Patients who were prescribed Aspirin",
    "Retrieve ICU patients with a length of stay longer than 7 days"
  ];

  const handleRunQuery = async (searchQuery: string) => {
    if (!searchQuery.trim()) return;
    setQuery(searchQuery);
    setLoading(true);
    setError(null);
    setTablePage(1);

    try {
      const res = await sendQuery(searchQuery);
      setResponse(res);
      if (onSaveToHistory) {
        onSaveToHistory(res);
      }

      // ─── SAVE HISTORY (if user is logged in) ───
      const token = localStorage.getItem('access_token');
      if (token) {
        try {
          await saveHistory(
            searchQuery,                                          // user question
            res.sql_query,                                       // generated SQL
            res.total_rows,                                      // number of rows
            res.execution_time_ms,                               // execution time
            res.data_quality_report?.summary?.total_findings || 0 // quality flags count
          );
          console.log('History saved successfully');
        } catch (historyErr) {
          // Don't block the user experience; just log the error
          console.warn('Failed to save history:', historyErr);
        }
      }

    } catch (err: any) {
      setError(err.message || 'An error occurred while executing the query.');
    } finally {
      setLoading(false);
    }
  };

  const copySqlToClipboard = () => {
    if (response?.sql_query) {
      navigator.clipboard.writeText(response.sql_query);
      setCopiedSql(true);
      setTimeout(() => setCopiedSql(false), 2000);
    }
  };

  const rowsPerPage = 8;
  const totalResults = response?.results?.length || 0;
  const paginatedResults = response?.results
    ? response.results.slice((tablePage - 1) * rowsPerPage, tablePage * rowsPerPage)
    : [];

  return (
    <div className="flex-1 flex flex-col h-full overflow-y-auto p-6 space-y-6 font-sans">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 text-xs font-mono font-semibold uppercase tracking-wider mb-1">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Conversational Clinical Workspace</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Cohort & Quality Analysis Workspace</h1>
          <p className="text-xs text-slate-400 mt-1">
            Query the MIMIC-IV demo database with natural language to generate verified SQL, audit data quality, and inspect source provenance.
          </p>
        </div>
      </div>

      {/* Query Search Bar Box */}
      <div className="p-4 rounded-2xl bg-[#0f172a] border border-slate-800 shadow-xl space-y-3">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleRunQuery(query);
          }}
          className="relative flex items-center"
        >
          <Search className="w-5 h-5 absolute left-4 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a clinical question (e.g. 'Find ICU patients with heart failure and check lab coverage')..."
            className="w-full pl-12 pr-32 py-3.5 bg-slate-900/90 border border-slate-700/80 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-cyan-500 transition-colors"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 px-5 py-2 text-xs font-semibold rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-md hover:shadow-cyan-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center space-x-2"
          >
            {loading ? (
              <span>Analyzing...</span>
            ) : (
              <>
                <span>Execute</span>
                <Send className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </form>

        {/* Quick Sample Suggestions */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] font-mono text-slate-500 flex items-center space-x-1">
            <HelpCircle className="w-3 h-3 text-slate-400" />
            <span>Sample Prompts:</span>
          </span>
          {samplePrompts.map((promptText, idx) => (
            <button
              key={idx}
              onClick={() => handleRunQuery(promptText)}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-cyan-500/40 text-slate-300 hover:text-cyan-300 transition-all text-left truncate max-w-xs"
            >
              {promptText}
            </button>
          ))}
        </div>
      </div>

      {/* Loading Skeleton */}
      {loading && (
        <div className="p-8 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-4 animate-pulse">
          <div className="w-12 h-12 rounded-full bg-cyan-950/80 border border-cyan-800 text-cyan-400 flex items-center justify-center mx-auto">
            <Activity className="w-6 h-6 animate-spin" />
          </div>
          <h3 className="text-base font-bold text-slate-200">Executing Clinical Query Pipeline</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Generating SQL translation → Running database retrieval → Auditing relevant data quality rules → Mapping source tables...
          </p>
        </div>
      )}

      {/* Error Card */}
      {error && !loading && (
        <div className="p-5 rounded-2xl bg-rose-950/30 border border-rose-800/60 text-rose-200 flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-sm text-rose-300">Query Execution Failure</h4>
            <p className="text-xs mt-1 text-rose-200/80">{error}</p>
          </div>
        </div>
      )}

      {/* Dynamic Results Workspace */}
      {response && !loading && (
        <div className="space-y-6 animate-fadeIn">
          {/* Query Summary & Execution Stats Bar */}
          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
            <div className="flex items-center space-x-3">
              <span className="px-2.5 py-1 rounded-md bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono font-semibold">
                Cohort: {response.total_rows} Records
              </span>
              <span className="px-2.5 py-1 rounded-md bg-slate-800 text-slate-300 font-mono flex items-center space-x-1">
                <Clock className="w-3 h-3 text-slate-400" />
                <span>{response.execution_time_ms} ms</span>
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <span className="badge-source-data px-2 py-0.5 rounded text-[10px] font-bold font-mono">
                SOURCE DATA
              </span>
              <span className="badge-computed-results px-2 py-0.5 rounded text-[10px] font-bold font-mono">
                COMPUTED RESULTS
              </span>
              <span className="badge-quality-flags px-2 py-0.5 rounded text-[10px] font-bold font-mono">
                QUALITY FLAGS ({response.data_quality_report?.summary?.total_findings || 0})
              </span>
              <span className="badge-ai-explanation px-2 py-0.5 rounded text-[10px] font-bold font-mono">
                AI EXPLANATION
              </span>
            </div>
          </div>

          {/* 1. Cohort Criteria & SQL Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Inclusion / Exclusion Criteria Box */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                  <span>Cohort Definition</span>
                </h3>
                <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/50">
                  HUMAN-READABLE RULES
                </span>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <span className="font-semibold text-slate-400 block mb-2 uppercase tracking-wider text-[10px]">
                    Inclusion Criteria
                  </span>
                  <ul className="space-y-1.5">
                    {response.inclusion_criteria && response.inclusion_criteria.length > 0 ? (
                      response.inclusion_criteria.map((item, i) => (
                        <li key={i} className="text-slate-300 font-mono text-[11px]">
                          {item}
                        </li>
                      ))
                    ) : (
                      <li className="text-slate-500 italic">No specific inclusion filters defined.</li>
                    )}
                  </ul>
                </div>

                {response.exclusion_criteria && response.exclusion_criteria.length > 0 && (
                  <div className="pt-2 border-t border-slate-800">
                    <span className="font-semibold text-slate-400 block mb-2 uppercase tracking-wider text-[10px]">
                      Exclusion Criteria
                    </span>
                    <ul className="space-y-1.5">
                      {response.exclusion_criteria.map((item, i) => (
                        <li key={i} className="text-amber-300 font-mono text-[11px]">
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* Generated Executable SQL Box */}
            <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-200 flex items-center space-x-2">
                  <Code className="w-4 h-4 text-blue-400" />
                  <span>Generated SQL</span>
                </h3>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={copySqlToClipboard}
                    className="p-1 text-slate-400 hover:text-cyan-400 transition-colors flex items-center space-x-1 text-xs"
                  >
                    {copiedSql ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedSql ? 'Copied' : 'Copy'}</span>
                  </button>
                  <button
                    onClick={() => setShowSql(!showSql)}
                    className="text-slate-400 hover:text-white"
                  >
                    {showSql ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {showSql && (
                <div className="p-3 rounded-xl bg-[#060911] border border-slate-800 font-mono text-[11px] text-cyan-300 overflow-x-auto max-h-36">
                  <pre>{response.sql_query}</pre>
                </div>
              )}
            </div>
          </div>

          {/* 2. Interactive Data & Findings Panel */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
            {/* Inner Navigation Tabs */}
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex space-x-2">
                <button
                  onClick={() => setActiveTab('source')}
                  className={`px-4 py-2 rounded-lg font-semibold text-xs transition-all flex items-center space-x-2 ${activeTab === 'source'
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/80 shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                >
                  <TableIcon className="w-4 h-4" />
                  <span>Retrieved Cohort Data ({totalResults})</span>
                  <span className="badge-source-data px-1.5 py-0.5 text-[9px] rounded font-mono">SOURCE</span>
                </button>

                <button
                  onClick={() => setActiveTab('quality')}
                  className={`px-4 py-2 rounded-lg font-semibold text-xs transition-all flex items-center space-x-2 ${activeTab === 'quality'
                    ? 'bg-amber-950 text-amber-300 border border-amber-800/80 shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                >
                  <ShieldAlert className="w-4 h-4" />
                  <span>Data Quality Flags ({response.data_quality_report?.summary?.total_findings || 0})</span>
                  <span className="badge-quality-flags px-1.5 py-0.5 text-[9px] rounded font-mono">QUALITY</span>
                </button>

                <button
                  onClick={() => setActiveTab('provenance')}
                  className={`px-4 py-2 rounded-lg font-semibold text-xs transition-all flex items-center space-x-2 ${activeTab === 'provenance'
                    ? 'bg-purple-950 text-purple-300 border border-purple-800/80 shadow-md'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                >
                  <GitCommit className="w-4 h-4" />
                  <span>Provenance ({response.source_tables?.length || 0})</span>
                  <span className="badge-computed-results px-1.5 py-0.5 text-[9px] rounded font-mono">EVIDENCE</span>
                </button>
              </div>
            </div>

            {/* TAB 1: Source Data Table */}
            {activeTab === 'source' && (
              <div>
                {totalResults === 0 ? (
                  <div className="py-8 text-center text-slate-500 text-xs">
                    No rows retrieved for this specific query criteria.
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="overflow-x-auto rounded-xl border border-slate-800">
                      <table className="w-full text-left text-xs text-slate-300">
                        <thead className="bg-[#0a0e1a] text-slate-400 font-mono text-[11px] border-b border-slate-800 uppercase tracking-wider">
                          <tr>
                            {Object.keys(response.results[0]).map((colKey) => (
                              <th key={colKey} className="px-4 py-3 font-semibold">
                                {colKey}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                          {paginatedResults.map((row, rowIdx) => (
                            <tr key={rowIdx} className="hover:bg-slate-900/60 transition-colors">
                              {Object.values(row).map((val, cellIdx) => (
                                <td key={cellIdx} className="px-4 py-2.5 font-mono text-slate-200 whitespace-nowrap">
                                  {val === null || val === undefined ? (
                                    <span className="text-slate-600 italic">null</span>
                                  ) : (
                                    String(val)
                                  )}
                                </td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* Pagination Bar */}
                    <div className="flex items-center justify-between text-xs text-slate-400 pt-2 font-mono">
                      <span>
                        Showing {Math.min((tablePage - 1) * rowsPerPage + 1, totalResults)} to{' '}
                        {Math.min(tablePage * rowsPerPage, totalResults)} of {totalResults} rows
                      </span>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setTablePage((p) => Math.max(p - 1, 1))}
                          disabled={tablePage === 1}
                          className="px-3 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          Previous
                        </button>
                        <span>Page {tablePage} of {Math.ceil(totalResults / rowsPerPage)}</span>
                        <button
                          onClick={() => setTablePage((p) => Math.min(p + 1, Math.ceil(totalResults / rowsPerPage)))}
                          disabled={tablePage >= Math.ceil(totalResults / rowsPerPage)}
                          className="px-3 py-1 rounded bg-slate-900 border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                          Next
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* TAB 2: Data Quality Flags */}
            {activeTab === 'quality' && (
              <div className="space-y-4">
                {/* Summary Counter Bar */}
                <div className="grid grid-cols-3 gap-3 font-mono text-xs">
                  <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-800/50 flex items-center justify-between">
                    <span className="text-rose-300 font-bold">Errors</span>
                    <span className="text-rose-400 font-extrabold text-base">
                      {response.data_quality_report?.summary?.errors || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-800/50 flex items-center justify-between">
                    <span className="text-amber-300 font-bold">Warnings</span>
                    <span className="text-amber-400 font-extrabold text-base">
                      {response.data_quality_report?.summary?.warnings || 0}
                    </span>
                  </div>
                  <div className="p-3 rounded-xl bg-blue-950/30 border border-blue-800/50 flex items-center justify-between">
                    <span className="text-blue-300 font-bold">Informational</span>
                    <span className="text-blue-400 font-extrabold text-base">
                      {response.data_quality_report?.summary?.info || 0}
                    </span>
                  </div>
                </div>

                {/* Findings List */}
                <div className="space-y-3">
                  {[
                    ...(response.data_quality_report?.row_findings || []),
                    ...(response.data_quality_report?.dataset_findings || [])
                  ].length === 0 ? (
                    <div className="py-6 text-center text-slate-500 text-xs">
                      No data quality anomalies flagged for this query cohort.
                    </div>
                  ) : (
                    [
                      ...(response.data_quality_report?.row_findings || []),
                      ...(response.data_quality_report?.dataset_findings || [])
                    ].map((finding, fIdx) => (
                      <div
                        key={fIdx}
                        className="p-4 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-all space-y-2 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span
                              className={`px-2 py-0.5 rounded font-mono font-bold text-[10px] ${finding.severity === 'ERROR'
                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                : finding.severity === 'WARNING'
                                  ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                  : 'bg-blue-950 text-blue-300 border border-blue-800'
                                }`}
                            >
                              {finding.severity}
                            </span>
                            <span className="font-mono text-cyan-400 font-bold">{finding.rule_id}</span>
                            <span className="font-bold text-slate-200">{finding.rule_name}</span>
                          </div>
                          <span className="text-[10px] font-mono text-slate-400">
                            Count: {finding.count}
                          </span>
                        </div>

                        <p className="text-slate-300">{finding.description}</p>
                        {finding.impact_summary && (
                          <p className="text-slate-400 font-mono text-[11px]">
                            Impact: {finding.impact_summary}
                          </p>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            {/* TAB 3: Provenance (source tables only) */}
            {activeTab === 'provenance' && (
              <div className="space-y-4">
                <p className="text-xs text-slate-400">
                  Source tables used by this analysis query.
                </p>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <h4 className="text-sm font-bold text-purple-200">Provenance</h4>
                  <div>
                    <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 block mb-2">
                      Tables
                    </span>
                    {response.source_tables && response.source_tables.length > 0 ? (
                      <ul className="space-y-2">
                        {response.source_tables.map((tableName) => (
                          <li
                            key={tableName}
                            className="flex items-center space-x-2 text-sm font-mono text-slate-200"
                          >
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                            <span>{tableName}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-slate-500 italic">
                        No source tables identified for this query.
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 3. AI Clinical Explanation (structured output) */}
          <div className="p-6 rounded-2xl bg-gradient-to-br from-[#13112a] to-[#0d1527] border border-purple-900/60 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-purple-400">
                <Sparkles className="w-5 h-5" />
                <h3 className="text-base font-bold text-purple-200">AI Research Synthesis</h3>
              </div>
              <span className="badge-ai-explanation px-2.5 py-0.5 rounded text-[10px] font-bold font-mono">
                AI GENERATED EXPLANATION
              </span>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              {response.ai_explanation?.summary || response.explanation}
            </p>

            {response.ai_explanation?.key_findings && response.ai_explanation.key_findings.length > 0 && (
              <div className="pt-3 border-t border-purple-900/50 space-y-2">
                <span className="text-xs font-semibold text-purple-300 block">Key Findings</span>
                <ul className="space-y-1 text-xs text-slate-300">
                  {response.ai_explanation.key_findings.map((finding, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="text-purple-400 font-bold">•</span>
                      <span>{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {(response.ai_explanation?.limitations?.length || response.limitations?.length) ? (
              <div className="pt-3 border-t border-purple-900/50 space-y-2">
                <span className="text-xs font-semibold text-purple-300 block">Limitations</span>
                <ul className="space-y-1 text-xs text-slate-400">
                  {(response.ai_explanation?.limitations?.length
                    ? response.ai_explanation.limitations
                    : response.limitations || []
                  ).map((lim, lIdx) => (
                    <li key={lIdx} className="flex items-start space-x-2">
                      <span className="text-purple-400 font-bold">•</span>
                      <span>{lim}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {response.ai_explanation?.uncertainty && response.ai_explanation.uncertainty.length > 0 && (
              <div className="pt-3 border-t border-purple-900/50 space-y-2">
                <span className="text-xs font-semibold text-purple-300 block">Uncertainty</span>
                <ul className="space-y-1 text-xs text-slate-400">
                  {response.ai_explanation.uncertainty.map((item, idx) => (
                    <li key={idx} className="flex items-start space-x-2">
                      <span className="text-purple-400 font-bold">?</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <div className="pt-2 text-[10px] text-purple-400/70 italic border-t border-purple-950 font-mono">
              Notice: AI explanations are generated strictly for academic cohort understanding. Do not use for patient triage, diagnostic decisions, or treatment planning.
            </div>
          </div>
        </div>
      )}
    </div>
  );
}