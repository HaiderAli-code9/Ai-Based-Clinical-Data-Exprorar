'use client';

import React, { useState } from 'react';
import { 
  Activity, 
  Database, 
  ShieldAlert, 
  GitCommit, 
  Search, 
  ArrowRight, 
  FileText, 
  CheckCircle2, 
  Sparkles,
  Lock,
  UserCheck,
  Server,
  Layers
} from 'lucide-react';
import AuthModal from './AuthModal';

interface LandingPageProps {
  onGetStarted: () => void;
}

export default function LandingPage({ onGetStarted }: LandingPageProps) {
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');

  const openAuth = (mode: 'login' | 'signup') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#070b14] text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-white">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 bg-[#090d16]/90 backdrop-blur-md border-b border-slate-800/80 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-cyan-400 bg-clip-text text-transparent">
              ClinData Explorer
            </h1>
            <p className="text-xs text-slate-400 font-mono">v2.0 Clinical Research Platform</p>
          </div>
        </div>

        <nav className="hidden md:flex items-center space-x-8 text-sm font-medium text-slate-300">
          <a href="#features" className="hover:text-cyan-400 transition-colors">Features</a>
          <a href="#pipeline" className="hover:text-cyan-400 transition-colors">How It Works</a>
          <a href="#disclaimer" className="hover:text-cyan-400 transition-colors">Safety & Ethics</a>
        </nav>

        <div className="flex items-center space-x-3">
          <button 
            onClick={() => openAuth('login')}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 rounded-lg transition-all"
          >
            Login
          </button>
          <button 
            onClick={() => openAuth('signup')}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white hover:bg-slate-800/60 rounded-lg transition-all"
          >
            Sign Up
          </button>
          <button 
            onClick={onGetStarted}
            className="px-5 py-2.5 text-sm font-semibold rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center space-x-2"
          >
            <span>Launch Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-20 pb-24 px-6 max-w-7xl mx-auto text-center flex flex-col items-center">
        {/* Background Ambient Glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-gradient-to-r from-cyan-600/20 via-blue-600/20 to-purple-600/20 blur-[120px] rounded-full pointer-events-none" />

        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-full bg-cyan-950/60 border border-cyan-800/50 text-cyan-300 text-xs font-semibold tracking-wide uppercase mb-6 shadow-inner">
          <Sparkles className="w-3.5 h-3.5" />
          <span>MIMIC-IV Demo Cohort & Data Quality Engine</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-100 tracking-tight leading-tight max-w-4xl">
          Turn Clinical Data Into{' '}
          <span className="bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
            Explainable Insights.
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-400 max-w-2xl font-light leading-relaxed">
          Transparent, clinical research-oriented platform for natural language cohort discovery, automated data-quality audits, and row-level record provenance.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row items-center gap-4">
          <button 
            onClick={onGetStarted}
            className="w-full sm:w-auto px-8 py-4 text-base font-bold rounded-xl bg-gradient-to-r from-cyan-500 via-blue-600 to-purple-600 text-white shadow-xl shadow-cyan-500/25 hover:shadow-cyan-500/40 hover:scale-[1.03] transition-all flex items-center justify-center space-x-3"
          >
            <span>Start Cohort Analysis</span>
            <ArrowRight className="w-5 h-5" />
          </button>
          
          <button
            onClick={() => {
              const el = document.getElementById('pipeline');
              el?.scrollIntoView({ behavior: 'smooth' });
            }}
            className="w-full sm:w-auto px-6 py-4 text-base font-semibold rounded-xl bg-slate-900/80 border border-slate-800 text-slate-300 hover:text-white hover:bg-slate-800 transition-all flex items-center justify-center space-x-2"
          >
            <Layers className="w-5 h-5 text-slate-400" />
            <span>Explore Workflow</span>
          </button>
        </div>

        {/* Quick Database Stats Bar */}
        <div className="mt-16 w-full max-w-4xl grid grid-cols-2 sm:grid-cols-4 gap-4 p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-md">
          <div className="text-center p-3 border-r border-slate-800/60 last:border-0">
            <p className="text-2xl sm:text-3xl font-extrabold text-cyan-400 font-mono">10</p>
            <p className="text-xs text-slate-400 uppercase tracking-wider mt-1">Clinical Tables</p>
          </div>
          <div className="text-center p-3 border-r border-slate-800/60 last:border-0">
            <p className="text-2xl sm:text-3xl font-extrabold text-blue-400 font-mono">912,284</p>
            <p className="text-xs text-slate-400 uppercase tracking-wider mt-1">Database Records</p>
          </div>
          <div className="text-center p-3 border-r border-slate-800/60 last:border-0">
            <p className="text-2xl sm:text-3xl font-extrabold text-amber-400 font-mono">12</p>
            <p className="text-xs text-slate-400 uppercase tracking-wider mt-1">Quality Rules</p>
          </div>
          <div className="text-center p-3">
            <p className="text-2xl sm:text-3xl font-extrabold text-purple-400 font-mono">100%</p>
            <p className="text-xs text-slate-400 uppercase tracking-wider mt-1">Traceable Provenance</p>
          </div>
        </div>
      </section>

      {/* Feature Cards Section */}
      <section id="features" className="py-20 px-6 max-w-7xl mx-auto w-full">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold text-slate-100">Four Pillars of Clinical Transparency</h2>
          <p className="text-slate-400 mt-2">Built explicitly for medical researchers, epidemiologists, and data scientists.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500/50 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400 group-hover:scale-110 transition-transform mb-4">
              <Search className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-200">Cohort Explorer</h3>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">
              Formulate complex patient inclusion & exclusion criteria using simple natural language query translation to standard SQL.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-amber-500/50 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-amber-950/80 border border-amber-800/60 flex items-center justify-center text-amber-400 group-hover:scale-110 transition-transform mb-4">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-200">Data Quality Audit</h3>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">
              Automated detection of unit variations, missing lab records, temporal misalignments, and coding discrepancies across cohort subsets.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-blue-500/50 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-blue-950/80 border border-blue-800/60 flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform mb-4">
              <Activity className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-200">Measurement Analysis</h3>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">
              Full visibility into chartevents and labevents coverage, reference range outliers, and prescription timeline alignments.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-purple-500/50 transition-all group">
            <div className="w-12 h-12 rounded-xl bg-purple-950/80 border border-purple-800/60 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform mb-4">
              <GitCommit className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-slate-200">Provenance & Evidence</h3>
            <p className="text-sm text-slate-400 mt-2 leading-relaxed">
              Trace every single finding back to its precise source table, field, record ID, subject ID, and timestamp with zero black-box summaries.
            </p>
          </div>
        </div>
      </section>

      {/* How It Works Pipeline Section */}
      <section id="pipeline" className="py-20 px-6 max-w-7xl mx-auto w-full border-t border-slate-800/80">
        <div className="text-center mb-16">
          <span className="text-xs font-mono font-semibold uppercase text-cyan-400 tracking-wider">End-to-End Pipeline</span>
          <h2 className="text-3xl font-bold text-slate-100 mt-2">How ClinData Explorer Works</h2>
          <p className="text-slate-400 mt-2 max-w-2xl mx-auto">
            A deterministic, fully auditable analytical workflow designed to eliminate AI hallucination risks in healthcare data.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 items-center relative">
          {[
            { step: '1', title: 'Natural Language', desc: 'Researcher prompt' },
            { step: '2', title: 'Cohort Definition', desc: 'Inclusion & Exclusion' },
            { step: '3', title: 'SQL Query', desc: 'Dialect translation' },
            { step: '4', title: 'Database Engine', desc: 'SQLite MIMIC-IV' },
            { step: '5', title: 'Data Quality', desc: '12 Rule verification' },
            { step: '6', title: 'Evidence Trace', desc: 'Source provenance' },
            { step: '7', title: 'Explainable Output', desc: 'Structured insight' },
          ].map((item, idx) => (
            <React.Fragment key={idx}>
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 text-center flex flex-col items-center hover:border-cyan-500/50 transition-all">
                <div className="w-8 h-8 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 text-xs font-bold font-mono flex items-center justify-center mb-2">
                  {item.step}
                </div>
                <h4 className="text-xs font-bold text-slate-200">{item.title}</h4>
                <p className="text-[10px] text-slate-400 mt-1">{item.desc}</p>
              </div>
              {idx < 6 && (
                <div className="hidden md:flex justify-center text-slate-600">
                  <ArrowRight className="w-4 h-4 text-slate-500" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </section>

      {/* Safety & Educational Disclaimer Section */}
      <section id="disclaimer" className="py-12 px-6 max-w-5xl mx-auto w-full my-8">
        <div className="p-6 rounded-2xl bg-amber-950/20 border border-amber-800/40 text-amber-200/90 flex flex-col sm:flex-row items-start space-y-4 sm:space-y-0 sm:space-x-4">
          <ShieldAlert className="w-7 h-7 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-amber-300 text-base">Research & Educational Prototype Disclaimer</h4>
            <p className="text-sm mt-1 text-amber-200/80 leading-relaxed">
              ClinData Explorer is designed strictly for retrospective clinical cohort discovery, data quality inspection, and research exploration using anonymized database schemas (MIMIC-IV demo). It does <strong>NOT</strong> provide medical advice, diagnostic recommendations, patient triage, or clinical decision support.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-800/80 bg-[#060910] py-8 px-6 text-center text-xs text-slate-500 font-mono">
        <p>© 2026 ClinData Explorer — Clinical Data Quality & Provenance System</p>
        <p className="mt-1 text-slate-600">Built for AI for Smarter Patient Care Hackathon Prototype</p>
      </footer>

      {/* Auth Modal */}
      {authModalOpen && (
        <AuthModal 
          mode={authMode} 
          onClose={() => setAuthModalOpen(false)} 
          onSuccess={() => {
            setAuthModalOpen(false);
            onGetStarted();
          }}
        />
      )}
    </div>
  );
}
