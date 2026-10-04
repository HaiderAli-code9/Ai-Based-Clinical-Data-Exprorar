'use client';

import React, { useState, useEffect } from 'react';
import { 
  MessageSquarePlus, 
  BarChart3, 
  History, 
  Settings, 
  Activity, 
  Home, 
  Server, 
  RefreshCw,
  LogOut
} from 'lucide-react';
import { getCurrentUser } from '../lib/api';

export type DashboardTab = 'new-analysis' | 'dataset-insights' | 'history' | 'settings';

interface SidebarProps {
  activeTab: DashboardTab;
  setActiveTab: (tab: DashboardTab) => void;
  onGoHome: () => void;
  backendOnline: boolean;
  onRecheckHealth: () => void;
}

export default function Sidebar({
  activeTab,
  setActiveTab,
  onGoHome,
  backendOnline,
  onRecheckHealth,
}: SidebarProps) {
  const [user, setUser] = useState<{ name: string; email: string } | null>(null);
  const [loading, setLoading] = useState(true);

  const navItems = [
    { id: 'new-analysis' as DashboardTab, label: 'New Analysis', icon: MessageSquarePlus },
    { id: 'dataset-insights' as DashboardTab, label: 'Dataset Insights', icon: BarChart3 },
    { id: 'history' as DashboardTab, label: 'History', icon: History },
    { id: 'settings' as DashboardTab, label: 'Settings', icon: Settings },
  ];

  // Fetch user profile on mount
  useEffect(() => {
    const fetchUser = async () => {
      try {
        const data = await getCurrentUser();
        setUser(data);
      } catch {
        // User not logged in – silently handle
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    fetchUser();
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    setUser(null);
    onGoHome(); // navigate to landing page
  };

  return (
    <aside className="w-64 bg-[#0a0f1d] border-r border-slate-800/80 flex flex-col justify-between shrink-0 h-screen sticky top-0 font-sans">
      {/* Top Header */}
      <div>
        <div className="p-5 border-b border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center space-x-3 cursor-pointer" onClick={onGoHome}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-blue-600 flex items-center justify-center shadow-md shadow-cyan-500/20">
              <Activity className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="font-bold text-sm text-slate-100 tracking-tight">ClinData Explorer</h2>
              <p className="text-[10px] text-slate-400 font-mono">MIMIC-IV Engine</p>
            </div>
          </div>
          <button 
            onClick={onGoHome} 
            title="Return to Cover Page"
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <Home className="w-4 h-4" />
          </button>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1 mt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-xl font-medium text-sm transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-950/80 to-slate-900 border border-cyan-700/50 text-cyan-300 shadow-md shadow-cyan-950/40'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Section: User + API Status */}
      <div className="space-y-3 p-4">
        {/* User Section */}
        {!loading && (
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            {user ? (
              <div className="flex items-center justify-between">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-slate-100 truncate">{user.name}</p>
                  <p className="text-[10px] text-slate-400 truncate">{user.email}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="p-1.5 rounded-lg text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <p className="text-xs text-slate-500 text-center">Not logged in</p>
            )}
          </div>
        )}

        {/* API Connection Status */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">
              API Connection
            </span>
            <button
              onClick={onRecheckHealth}
              title="Recheck API health"
              className="p-1 text-slate-400 hover:text-cyan-400 transition-colors"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <div className={`w-2.5 h-2.5 rounded-full ${backendOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span className="font-mono text-slate-300 text-[11px]">
              {backendOnline ? 'http://localhost:8000 (Connected)' : 'Server Offline'}
            </span>
          </div>

          <div className="mt-3 pt-2 border-t border-slate-800 text-[10px] text-slate-500 flex justify-between">
            <span>Database: SQLite</span>
            <span>10 Tables</span>
          </div>
        </div>
      </div>
    </aside>
  );
}