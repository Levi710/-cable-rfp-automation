import React, { useState, useEffect, useRef } from 'react';
import AgentNetwork from './AgentNetwork';

const LOG_MESSAGES = [
    { source: "SYSTEM", msg: "Initialized Pipeline v2.4" },
    { source: "ORCHESTRATOR", msg: "Received file: 'NTPC_Tender_2024.pdf'", highlight: true },
    { source: "ORCHESTRATOR", msg: "Parsing PDF structure..." },
    { source: "ORCHESTRATOR", msg: "Identified 15 potential line items." },
    { source: "ORCHESTRATOR", msg: "Delegating to Sales Agent for filtering..." },
    { source: "SALES", msg: "Analysing keywords: '3.3kV', 'XLPE'...", color: "text-tech-magenta" },
    { source: "SALES", msg: "Filtered 3 items. Qualified 12 tenders." },
    { source: "SALES", msg: "Sending Qualified list to Orchestrator." },
    { source: "ORCHESTRATOR", msg: "Received Qualified Tenders." },
    { source: "ORCHESTRATOR", msg: "Requesting Technical Analysis for Tender #101" },
    { source: "TECH", msg: "Querying Product Database...", color: "text-tech-cyan" },
    { source: "TECH", msg: "Match found: 'CAB-XLPE-33-3C-300-AL' (98% match)" },
    { source: "TECH", msg: "Verifying spec compliance... OK." },
    { source: "ORCHESTRATOR", msg: "Technical Check Passed." },
    { source: "ORCHESTRATOR", msg: "Requesting Pricing..." },
    { source: "PRICING", msg: "Calculating Material Cost (Copper/Aluminum)...", color: "text-yellow-400" },
    { source: "PRICING", msg: "Applied Margin: 12%." },
    { source: "PRICING", msg: "Final Bid Value: ₹4,85,00,000" },
    { source: "ORCHESTRATOR", msg: "Bid Package Ready." },
    { source: "SYSTEM", msg: "Pipeline Execution Complete." }
];

const ProcessingView = ({ onComplete }) => {
    const [logs, setLogs] = useState([]);
    const bottomRef = useRef(null);

    useEffect(() => {
        let currentIndex = 0;

        const interval = setInterval(() => {
            if (currentIndex >= LOG_MESSAGES.length) {
                clearInterval(interval);
                setTimeout(onComplete, 1000); // Wait 1s after logs finish
                return;
            }

            setLogs(prev => [...prev, LOG_MESSAGES[currentIndex]]);
            currentIndex++;

            // Auto scroll
            if (bottomRef.current) {
                bottomRef.current.scrollIntoView({ behavior: 'smooth' });
            }

        }, 300); // New log every 300ms

        return () => clearInterval(interval);
    }, [onComplete]);

    return (
        <div className="min-h-screen flex flex-col md:flex-row p-8 gap-8 items-center">

            {/* Left: Visualization */}
            <div className="w-full md:w-1/2 ">
                <div className="text-center mb-4">
                    <h2 className="text-2xl font-mono font-bold animate-pulse text-tech-cyan">PROCESSING RFP...</h2>
                    <p className="text-xs text-gray-500 font-mono">AGENTS NEGOTIATING</p>
                </div>
                <AgentNetwork isActive={true} />
            </div>

            {/* Right: Terminal Log */}
            <div className="w-full md:w-1/2 bg-black/50 border border-white/20 rounded-lg p-4 h-[500px] overflow-y-auto font-mono text-sm shadow-inner relative">
                <div className="absolute top-0 left-0 right-0 bg-white/5 p-2 text-xs text-gray-400 flex justify-between border-b border-white/10">
                    <span>TERMINAL_OUTPUT</span>
                    <span>./cable_auto.log</span>
                </div>
                <div className="mt-8 space-y-2">
                    {logs.map((log, i) => (
                        <div key={i} className={`opacity-0 animate-fade-in-quick ${log.highlight ? 'bg-white/10' : ''}`}>
                            <span className="text-gray-600">[{new Date().toLocaleTimeString()}]</span>{' '}
                            <span className={`font-bold ${log.color || 'text-tech-cyan'}`}>{log.source}</span>:{' '}
                            <span className="text-gray-300">{log.msg}</span>
                        </div>
                    ))}
                    <div ref={bottomRef} />
                </div>
            </div>

        </div>
    );
};

export default ProcessingView;
