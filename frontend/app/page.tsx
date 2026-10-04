'use client';

import React, { useState, useEffect } from 'react';
import LandingPage from '../components/LandingPage';
import Sidebar, { DashboardTab } from '../components/Sidebar';
import NewAnalysisView from '../components/NewAnalysisView';
import DatasetInsightsView from '../components/DatasetInsightsView';
import HistoryView from '../components/HistoryView';
import SettingsView from '../components/SettingsView';
import { checkBackendHealth } from '../lib/api'; // removed ChatResponse import

export default function Home() {
  const [viewState, setViewState] = useState<'cover' | 'dashboard'>('cover');
  const [activeTab, setActiveTab] = useState<DashboardTab>('new-analysis');
  const [backendOnline, setBackendOnline] = useState<boolean>(true);
  const [recheckTrigger, setRecheckTrigger] = useState(0);

  const checkHealth = async () => {
    const res = await checkBackendHealth();
    setBackendOnline(res.status === 'ok');
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, [recheckTrigger]);

  const handleSelectHistoryQuery = (queryText: string) => {
    setActiveTab('new-analysis');
    // You can pass the query to NewAnalysisView via a ref or context if needed
  };

  if (viewState === 'cover') {
    return (
      <LandingPage 
        onGetStarted={() => {
          setViewState('dashboard');
          setActiveTab('new-analysis');
        }} 
      />
    );
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#070b14] text-slate-100 font-sans">
      {/* Dashboard Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onGoHome={() => setViewState('cover')}
        backendOnline={backendOnline}
        onRecheckHealth={() => setRecheckTrigger((v) => v + 1)}
      />

      {/* Main Content Area */}
      <main className="flex-1 h-full overflow-hidden flex flex-col bg-[#070b14]">
        {activeTab === 'new-analysis' && (
          <NewAnalysisView />
        )}
        {activeTab === 'dataset-insights' && (
          <DatasetInsightsView />
        )}
        {activeTab === 'history' && (
          <HistoryView
            onSelectQuery={handleSelectHistoryQuery}
          />
        )}
        {activeTab === 'settings' && (
          <SettingsView />
        )}
      </main>
    </div>
  );
}