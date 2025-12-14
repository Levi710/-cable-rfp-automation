import React, { useState } from 'react';
import PipelineVisualizer from './PipelineVisualizer';
import { Activity, Database, Server, CheckCircle, Clock, AlertCircle } from 'lucide-react';

const Dashboard = ({ data }) => {
    return (
        <div className="relative z-10 container mx-auto px-4 py-8 animate-fade-in">
            <header className="mb-12 flex justify-between items-center border-b border-white/10 pb-6">
                <div>
                    <h1 className="text-4xl font-mono font-bold tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-tech-cyan to-tech-magenta">
                        CABLE.RFP_AUTO
                    </h1>
                    <p className="text-tech-slate-light mt-2 flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                        SYSTEM ONLINE
                    </p>
                </div>
                <div className="flex gap-6 text-sm font-mono text-gray-400">
                    <div className="flex items-center gap-2">
                        <Clock size={16} />
                        <span>UPTIME: 24h 12m</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <Server size={16} />
                        <span>v2.4.0-stable</span>
                    </div>
                </div>
            </header>

            <main className="space-y-12">
                {/* KPI Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="bg-white/5 backdrop-blur-sm border border-white/10 p-6 rounded-lg hover:border-tech-cyan/50 transition-colors group">
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-tech-cyan/10 rounded-lg group-hover:bg-tech-cyan/20 transition-colors">
                                <Database className="text-tech-cyan" size={24} />
                            </div>
                            <span className="text-xs font-mono text-gray-500">TOTAL PROCESSED</span>
                        </div>
                        <div className="text-3xl font-bold font-mono">1,284</div>
                        <div className="text-sm text-gray-400 mt-1">RFPs analyzed</div>
                    </div>

                    <div className="bg-white/5 backdrop-blur-sm border border-white/10 p-6 rounded-lg hover:border-tech-magenta/50 transition-colors group">
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-tech-magenta/10 rounded-lg group-hover:bg-tech-magenta/20 transition-colors">
                                <Activity className="text-tech-magenta" size={24} />
                            </div>
                            <span className="text-xs font-mono text-gray-500">SUCCESS RATE</span>
                        </div>
                        <div className="text-3xl font-bold font-mono">94.2%</div>
                        <div className="text-sm text-gray-400 mt-1">parsing accuracy</div>
                    </div>

                    <div className="bg-white/5 backdrop-blur-sm border border-white/10 p-6 rounded-lg hover:border-green-500/50 transition-colors group">
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-green-500/10 rounded-lg group-hover:bg-green-500/20 transition-colors">
                                <CheckCircle className="text-green-500" size={24} />
                            </div>
                            <span className="text-xs font-mono text-gray-500">ACTIVE AGENTS</span>
                        </div>
                        <div className="text-3xl font-bold font-mono">5/5</div>
                        <div className="text-sm text-gray-400 mt-1">operational</div>
                    </div>

                    <div className="bg-white/5 backdrop-blur-sm border border-white/10 p-6 rounded-lg hover:border-yellow-500/50 transition-colors group">
                        <div className="flex justify-between items-start mb-4">
                            <div className="p-2 bg-yellow-500/10 rounded-lg group-hover:bg-yellow-500/20 transition-colors">
                                <AlertCircle className="text-yellow-500" size={24} />
                            </div>
                            <span className="text-xs font-mono text-gray-500">PENDING REVIEW</span>
                        </div>
                        <div className="text-3xl font-bold font-mono">12</div>
                        <div className="text-sm text-gray-400 mt-1">requiring attention</div>
                    </div>
                </div>

                {/* Main Visualizer */}
                <div className="bg-black/20 backdrop-blur-md rounded-xl border border-white/10 overflow-hidden shadow-2xl shadow-tech-cyan/5">
                    <div className="p-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
                        <h2 className="font-mono text-lg flex items-center gap-2">
                            <Activity className="text-tech-cyan" size={20} />
                            LIVE_PIPELINE_VIEW
                        </h2>
                        <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-1 rounded">ID: {data?.tender_id || 'UNKNOWN'}</span>
                    </div>

                    {data && <PipelineVisualizer data={data} />}

                    <div className="p-4 border-t border-white/10 bg-white/5 grid grid-cols-2 gap-4 text-xs font-mono text-gray-400">
                        <div>
                            <span className="text-gray-600 block mb-1">INPUT SOURCE</span>
                            {data?.tender_details?.title}
                        </div>
                        <div className="text-right">
                            <span className="text-gray-600 block mb-1">LAST UPDATE</span>
                            {new Date().toISOString()}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

export default Dashboard;
