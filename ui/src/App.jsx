import React, { useState, useEffect } from 'react';
import GridBackground from './components/GridBackground';
import PipelineVisualizer from './components/PipelineVisualizer';

// Mock Data Import (In real app, fetch from API)
import mockData from './mockData.json';

function App() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate API delay for dramatic effect
    setTimeout(() => {
      setData(mockData);
      setLoading(false);
    }, 1500);
  }, []);

  return (
    <div className="relative min-h-screen font-sans text-white bg-tech-dark overflow-hidden">
      <GridBackground />

      {/* Content Overlay */}
      <div className="relative z-10 container mx-auto p-8">
        <header className="mb-12 border-b border-tech-slate pb-4 flex justify-between items-end">
          <div>
            <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-tech-cyan to-white">
              CABLE RFP AUTOMATION
            </h1>
            <p className="text-tech-cyan/80 font-mono mt-2">&gt; INITIALIZING MAIN AGENT...</p>
          </div>
          <div className="flex gap-4">
            <div className="bg-tech-slate/50 px-4 py-2 rounded border border-tech-cyan/30 backdrop-blur-sm">
              <span className="text-xs text-gray-400 block">SYSTEM STATUS</span>
              <span className={`text-tech-cyan font-bold ${loading ? 'animate-pulse' : ''}`}>
                {loading ? 'INITIALIZING...' : 'ONLINE'}
              </span>
            </div>
          </div>
        </header>

        <main className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <section className="col-span-2 space-y-8">
            {/* Visualizer Container */}
            <div className="bg-tech-dark/80 backdrop-blur-md border border-tech-slate rounded-lg min-h-[400px] flex flex-col relative overflow-hidden group">
              {/* Corner Accents */}
              <div className="absolute top-0 left-0 w-4 h-4 border-l-2 border-t-2 border-tech-cyan"></div>
              <div className="absolute top-0 right-0 w-4 h-4 border-r-2 border-t-2 border-tech-cyan"></div>
              <div className="absolute bottom-0 left-0 w-4 h-4 border-l-2 border-b-2 border-tech-cyan"></div>
              <div className="absolute bottom-0 right-0 w-4 h-4 border-r-2 border-b-2 border-tech-cyan"></div>

              <div className="p-4 border-b border-tech-slate bg-tech-slate/20 flex justify-between">
                <h2 className="font-mono text-sm tracking-widest text-tech-cyan">PIPELINE VISUALIZATION</h2>
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
              </div>

              <div className="flex-1 flex items-center justify-center p-8">
                {loading ? (
                  <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 border-4 border-tech-cyan border-t-transparent rounded-full animate-spin"></div>
                    <span className="font-mono text-sm text-tech-cyan animate-pulse">CONNECTING TO AGENTS...</span>
                  </div>
                ) : (
                  <PipelineVisualizer data={data} />
                )}
              </div>
            </div>

            {/* Tender Details (If loaded) */}
            {!loading && data && (
              <div className="bg-tech-slate/20 border border-tech-slate rounded-lg p-6 backdrop-blur-sm">
                <h3 className="text-xl font-bold mb-4 text-white">Active Tender: <span className="text-tech-cyan">{data.processing.selected_rfp.tender_id}</span></h3>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="block text-gray-500">Title</span>
                    <span className="block text-gray-300">{data.processing.selected_rfp.title}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Organization</span>
                    <span className="block text-gray-300">{data.processing.selected_rfp.organization}</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Win Probability</span>
                    <span className="block text-green-400 font-mono font-bold text-lg">{data.processing.decision.win_probability}%</span>
                  </div>
                  <div>
                    <span className="block text-gray-500">Estimated Value</span>
                    <span className="block text-white font-mono">Rs {data.processing.selected_rfp.estimated_value.toLocaleString()}</span>
                  </div>
                </div>
              </div>
            )}
          </section>

          <aside className="space-y-6">
            {/* Stats */}
            <div className="bg-tech-slate/20 p-6 rounded border-l-4 border-tech-magenta backdrop-blur-sm">
              <h3 className="text-sm text-gray-400 mb-1">TOTAL TENDERS</h3>
              <p className="text-4xl font-bold font-mono text-white">
                {loading ? '...' : data?.discovery.total_discovered}
              </p>
            </div>
            <div className="bg-tech-slate/20 p-6 rounded border-l-4 border-tech-cyan backdrop-blur-sm">
              <h3 className="text-sm text-gray-400 mb-1">QUALIFIED TO BID</h3>
              <p className="text-4xl font-bold font-mono text-white">
                {loading ? '...' : data?.processing.sales_agent_output.filtering_stats.qualified}
              </p>
            </div>

            {/* Agent Status List */}
            <div className="space-y-2 mt-8">
              <h4 className="text-xs font-bold text-gray-500 tracking-widest mb-4">AGENT SWARM HEALTH</h4>
              {['OfficialSourcesCrawler', 'SalesAgent', 'TechnicalAgent', 'PricingAgent', 'MainAgent'].map((agent, i) => (
                <div key={agent} className="flex items-center justify-between p-3 bg-tech-slate/10 rounded border border-white/5">
                  <span className="text-sm font-mono text-gray-300">{agent}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-green-500">IDLE</span>
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: `${i * 200}ms` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </aside>
        </main>
      </div>
    </div>
  );
}

export default App;