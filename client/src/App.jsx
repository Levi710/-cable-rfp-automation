import React, { useState } from 'react';
import GridBackground from './components/GridBackground';
import LandingPage from './components/LandingPage';
import ProcessingView from './components/ProcessingView';
import Dashboard from './components/Dashboard';
import mockData from './mockData.json';

function App() {
  const [view, setView] = useState('landing'); // 'landing', 'processing', 'dashboard'
  const [data, setData] = useState(null);

  const startProcessing = () => {
    setView('processing');
  };

  const finishProcessing = (resultData) => {
    setData(resultData || mockData);
    setView('dashboard');
  };

  return (
    <div className="relative min-h-screen bg-tech-dark text-white overflow-x-hidden font-sans selection:bg-tech-cyan selection:text-tech-dark">
      {/* Global Background */}
      <GridBackground />

      {/* Pages */}
      <div className="relative z-10">
        {view === 'landing' && <LandingPage onStart={startProcessing} />}
        {view === 'processing' && <ProcessingView onComplete={finishProcessing} />}
        {view === 'dashboard' && <Dashboard data={data} />}
      </div>

    </div>
  );
}

export default App;