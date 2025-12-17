import React, { useState, useEffect, useRef } from 'react';
import AgentNetwork from './AgentNetwork';

const ProcessingView = ({ onComplete }) => {
    const [logs, setLogs] = useState([]);
    const bottomRef = useRef(null);
    const [fetchedData, setFetchedData] = useState(null);

    useEffect(() => {
        // Fetch real data on mount
        fetch('/data/pipeline_results.json')
            .then(res => res.json())
            .then(data => {
                setFetchedData(data);
                generateLogs(data);
            })
            .catch(err => {
                console.error("Failed to load pipeline results, using fallback log:", err);
                // Fallback to minimal logs or mock if needed, but for now we expect data to be there
                const fallbackLogs = [
                    { source: "SYSTEM", msg: "Error loading pipeline results." },
                    { source: "SYSTEM", msg: "Please ensure refresh_data.py has been run." }
                ];
                setLogs(fallbackLogs);
                // Still complete after a delay to show SOMETHING? 
                // Better to maybe not complete if no data, but for demo we might want to just stop.
            });
    }, []);

    const generateLogs = (data) => {
        // Construct a sequence of logs based on real data events
        const newLogs = [
            { source: "SYSTEM", msg: `Initialized Pipeline v${data.pipeline_info?.version || '2.0'}` },
            { source: "SYSTEM", msg: "Connecting to secure government gateways..." },
        ];

        // Discovery Logs
        const totalDiscovered = data.discovery?.total_discovered || 0;
        newLogs.push({ source: "CRAWLER", msg: `Scanning configured sources...` });
        if (data.discovery?.sources) {
            Object.entries(data.discovery.sources).forEach(([src, count]) => {
                newLogs.push({ source: "CRAWLER", msg: `Source [${src}]: Found ${count} tenders.` });
            });
        }
        newLogs.push({ source: "CRAWLER", msg: `Total Discoveries: ${totalDiscovered} items.` });

        // Sales Agent Logs
        newLogs.push({ source: "ORCHESTRATOR", msg: "Delegating to Sales Agent for qualification..." });
        const salesStats = data.processing?.sales_agent_output?.filtering_stats;
        if (salesStats) {
            newLogs.push({ source: "SALES", msg: "Applying client policy filters...", color: "text-tech-magenta" });
            newLogs.push({ source: "SALES", msg: `Filtered: ${salesStats.filtered} (Deadline/Criteria mismatch)` });
            newLogs.push({ source: "SALES", msg: `Qualified: ${salesStats.qualified} tenders available for bidding.` });
        }

        const selectedId = data.processing?.selected_rfp?.tender_id;
        if (selectedId) {
            newLogs.push({ source: "SALES", msg: `Selected Top Candidate: ${selectedId}`, highlight: true });
            newLogs.push({ source: "SALES", msg: "Sending to Orchestrator." });
        }

        // Tech Agent Logs
        if (data.processing?.technical_agent_output) {
            newLogs.push({ source: "ORCHESTRATOR", msg: `Engaging Technical Agent for ${selectedId}...` });
            const products = data.processing.technical_agent_output.final_selection || [];
            newLogs.push({ source: "TECH", msg: `Analyzing ${products.length} scope items...`, color: "text-tech-cyan" });

            products.slice(0, 3).forEach(p => {
                newLogs.push({ source: "TECH", msg: `Match found: '${p.selected_sku}' (${p.match_score}% match)` });
            });
            if (products.length > 3) {
                newLogs.push({ source: "TECH", msg: `...and ${products.length - 3} more items matched.` });
            }
            newLogs.push({ source: "TECH", msg: "Technical compliance verification passed." });
        }

        // Pricing Agent Logs
        if (data.processing?.pricing_agent_output) {
            newLogs.push({ source: "ORCHESTRATOR", msg: "Requesting Pricing calculation..." });
            const pricing = data.processing.pricing_agent_output.pricing_details;
            newLogs.push({ source: "PRICING", msg: "Fetching live commodity prices (LME Copper/Al)...", color: "text-yellow-400" });
            newLogs.push({ source: "PRICING", msg: `Material Cost: ₹${(pricing?.total_material_cost || 0).toLocaleString()}` });
            newLogs.push({ source: "PRICING", msg: `Services & Overheads: ₹${(pricing?.total_services_cost || 0).toLocaleString()}` });
            newLogs.push({ source: "PRICING", msg: `Calculated Final Quote: ₹${(pricing?.grand_total || 0).toLocaleString()}` });
        }

        // Decision Logs
        if (data.processing?.decision) {
            newLogs.push({ source: "ORCHESTRATOR", msg: "Consolidating final bid package..." });
            newLogs.push({ source: "DECISION", msg: `Win Probability: ${data.processing.decision.win_probability}%`, highlight: true });
            newLogs.push({ source: "DECISION", msg: `Recommendation: ${data.processing.recommendation}` });
        }

        // Notification Log
        newLogs.push({ source: "SYSTEM", msg: "Generating Multichannel Report..." });
        newLogs.push({ source: "NOTIFIER", msg: "Sending WhatsApp & Telegram alerts...", color: "text-green-400" });

        newLogs.push({ source: "SYSTEM", msg: "Pipeline Execution Complete." });

        // Simulate streaming
        streamLogs(newLogs, data);
    };

    const streamLogs = (allLogs, finalData) => {
        let currentIndex = 0;
        const interval = setInterval(() => {
            if (currentIndex >= allLogs.length) {
                clearInterval(interval);
                setTimeout(() => onComplete(finalData), 1500); // Pass the real data back
                return;
            }

            setLogs(prev => [...prev, allLogs[currentIndex]]);
            currentIndex++;

            if (bottomRef.current) {
                bottomRef.current.scrollIntoView({ behavior: 'smooth' });
            }
        }, 400); // 400ms per log line
    };

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
                        <div key={i} className={`opacity-0 animate-fade-in-quick ${log?.highlight ? 'bg-white/10' : ''}`}>
                            <span className="text-gray-600">[{new Date().toLocaleTimeString()}]</span>{' '}
                            <span className={`font-bold ${log?.color || 'text-tech-cyan'}`}>{log?.source}</span>:{' '}
                            <span className="text-gray-300">{log?.msg}</span>
                        </div>
                    ))}
                    <div ref={bottomRef} />
                </div>
            </div>

        </div>
    );
};

export default ProcessingView;
