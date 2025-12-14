import React, { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import { ShieldCheck, Search, Database, Calculator, FileText } from 'lucide-react';

const PipelineVisualizer = ({ data }) => {
    const containerRef = useRef(null);
    const [activeStage, setActiveStage] = useState(0);

    const stages = [
        { id: 'discovery', label: 'DISCOVERY', icon: Search, color: '#00f2ea' },
        { id: 'sales', label: 'SALES AGENT', icon: ShieldCheck, color: '#ff0055' }, // Magenta
        { id: 'tech', label: 'TECH AGENT', icon: Database, color: '#00f2ea' },
        { id: 'pricing', label: 'PRICING', icon: Calculator, color: '#facc15' }, // Yellow
        { id: 'decision', label: 'DECISION', icon: FileText, color: '#4ade80' } // Green
    ];

    useEffect(() => {
        if (!data) return;

        // Master Timeline
        const tl = anime.timeline({
            easing: 'easeOutExpo',
            loop: false // Run once for now
        });

        // 1. Discovery Pulse
        tl.add({
            targets: '.stage-discovery .icon-ring',
            scale: [1, 1.5, 1],
            opacity: [0.5, 0, 0.5],
            duration: 1000,
            complete: () => setActiveStage(0) // Discovery Active
        })

            // 2. Data Flow to Sales
            .add({
                targets: '.connector-0',
                width: ['0%', '100%'],
                backgroundColor: ['#1f2937', '#00f2ea'],
                duration: 800,
                easing: 'linear'
            })
            .add({
                targets: '.stage-sales',
                opacity: [0.3, 1],
                translateY: [20, 0],
                duration: 500,
                begin: () => setActiveStage(1)
            })

            // 3. Sales Filtering Animation (Particles being rejected)
            .add({
                targets: '.filter-particle.rejected',
                translateX: [0, 50],
                opacity: [1, 0],
                delay: anime.stagger(100),
                duration: 500,
                color: '#ff0000'
            }, '-=300')

            // 4. Flow to Tech
            .add({
                targets: '.connector-1',
                width: ['0%', '100%'],
                backgroundColor: ['#1f2937', '#ff0055'],
                duration: 800,
                easing: 'linear'
            })
            .add({
                targets: '.stage-tech',
                opacity: [0.3, 1],
                translateY: [20, 0],
                duration: 500,
                begin: () => setActiveStage(2)
            })

            // 5. Flow to Pricing
            .add({
                targets: '.connector-2',
                width: ['0%', '100%'],
                backgroundColor: ['#1f2937', '#00f2ea'],
                duration: 800,
                easing: 'linear'
            })
            .add({
                targets: '.stage-pricing',
                opacity: [0.3, 1],
                translateY: [20, 0],
                duration: 500,
                begin: () => setActiveStage(3)
            })
            .add({
                targets: '.price-counter',
                innerHTML: [0, 48500000],
                round: 1,
                easing: 'linear',
                duration: 1500,
                update: function (a) {
                    // const value = a.animations[0].currentValue;
                    // Manually format if needed, simplistic for now
                }
            })

            // 6. Flow to Decision
            .add({
                targets: '.connector-3',
                width: ['0%', '100%'],
                backgroundColor: ['#1f2937', '#facc15'],
                duration: 800,
                easing: 'linear'
            })
            .add({
                targets: '.stage-decision',
                opacity: [0.3, 1],
                scale: [0.8, 1],
                duration: 800,
                begin: () => setActiveStage(4)
            })


    }, [data]);

    const [detailsOpen, setDetailsOpen] = useState(false);
    const detailsRef = useRef(null);

    const handleStageClick = (index) => {
        if (activeStage === index && detailsOpen) {
            setDetailsOpen(false);
        } else {
            setActiveStage(index);
            setDetailsOpen(true);
        }
    };

    // CSS-based transition is more reliable than JS height:auto
    const detailsClasses = detailsOpen
        ? "max-h-[1000px] opacity-100 border-white/10"
        : "max-h-0 opacity-0 border-transparent";


    const renderDetails = () => {
        if (!data) return null;
        const stageId = stages[activeStage]?.id;

        switch (stageId) {
            case 'discovery':
                return (
                    <div className="grid grid-cols-1 gap-4">
                        <h3 className="text-tech-cyan font-mono text-lg mb-2 border-b border-white/10 pb-2">DISCOVERED OPPORTUNITIES</h3>
                        {data.discovery?.tenders?.map((tender, i) => (
                            <div key={i} className="bg-white/5 p-3 rounded flex justify-between items-center hover:bg-white/10 transition-colors cursor-pointer border-l-2 border-transparent hover:border-tech-cyan">
                                <div>
                                    <div className="text-sm font-bold text-white">{tender.title}</div>
                                    <div className="text-xs text-gray-400">{tender.organization} | <span className="text-tech-cyan">ID: {tender.tender_id}</span></div>
                                </div>
                                <div className="text-right">
                                    <div className="text-sm font-mono text-gray-300">₹{(tender.estimated_value / 10000000).toFixed(2)} Cr</div>
                                    <div className="text-xs text-gray-500">{new Date(tender.deadline).toLocaleDateString()}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                );
            case 'sales':
                return (
                    <div className="grid grid-cols-2 gap-6">
                        <div>
                            <h3 className="text-tech-magenta font-mono text-lg mb-2 border-b border-white/10 pb-2">QUALIFICATION METRICS</h3>
                            <div className="space-y-3">
                                <div className="flex justify-between bg-white/5 p-2 rounded">
                                    <span className="text-gray-400 text-sm">Keyword Match</span>
                                    <span className="text-white font-mono">HIGH (XLPE, 3.3kV)</span>
                                </div>
                                <div className="flex justify-between bg-white/5 p-2 rounded">
                                    <span className="text-gray-400 text-sm">Est. Value</span>
                                    <span className="text-white font-mono">₹5.0 Cr</span>
                                </div>
                                <div className="flex justify-between bg-white/5 p-2 rounded">
                                    <span className="text-gray-400 text-sm">Customer Tier</span>
                                    <span className="text-white font-mono">TIER-1 (NTPC)</span>
                                </div>
                            </div>
                        </div>
                        <div>
                            <h3 className="text-tech-magenta font-mono text-lg mb-2 border-b border-white/10 pb-2">FILTERING STATS</h3>
                            <div className="grid grid-cols-3 gap-2 text-center">
                                <div className="bg-white/5 p-2 rounded">
                                    <div className="text-2xl font-bold text-gray-300">{data.processing?.sales_agent_output?.filtering_stats?.total_processed || 0}</div>
                                    <div className="text-xs text-gray-500 uppercase">Scanned</div>
                                </div>
                                <div className="bg-white/5 p-2 rounded">
                                    <div className="text-2xl font-bold text-red-400">{data.processing?.sales_agent_output?.filtering_stats?.filtered || 0}</div>
                                    <div className="text-xs text-gray-500 uppercase">Rejected</div>
                                </div>
                                <div className="bg-white/5 p-2 rounded bg-tech-magenta/10 border border-tech-magenta/30">
                                    <div className="text-2xl font-bold text-tech-magenta">{data.processing?.sales_agent_output?.filtering_stats?.qualified || 0}</div>
                                    <div className="text-xs text-tech-magenta uppercase">Qualified</div>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            case 'tech':
                return (
                    <div>
                        <h3 className="text-tech-cyan font-mono text-lg mb-2 border-b border-white/10 pb-2">PRODUCT SELECTION</h3>
                        <div className="space-y-4">
                            {data.processing?.technical_agent_output?.final_selection?.map((item, i) => (
                                <div key={i} className="bg-white/5 p-4 rounded-lg border border-white/5 hover:border-tech-cyan/50 transition-colors">
                                    <div className="flex justify-between mb-2">
                                        <div className="text-sm text-gray-400 font-mono">REQ: {item.requirement}</div>
                                        <div className="text-xs px-2 py-0.5 rounded bg-green-500/20 text-green-400 border border-green-500/30">MATCH: {item.match_score}%</div>
                                    </div>
                                    <div className="text-lg font-bold text-white">{item.selected_sku}</div>
                                    <div className="text-sm text-gray-400 mt-1">{item.description}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                );
            case 'pricing':
                const pricing = data.processing?.pricing_agent_output?.pricing_details;
                return (
                    <div className="grid grid-cols-3 gap-6">
                        <div className="col-span-2">
                            <h3 className="text-yellow-400 font-mono text-lg mb-2 border-b border-white/10 pb-2">COST BREAKDOWN</h3>
                            <div className="space-y-2">
                                <div className="flex justify-between p-2 hover:bg-white/5 rounded">
                                    <span className="text-gray-400">Material Cost</span>
                                    <span className="font-mono text-white">₹{pricing?.total_material_cost?.toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between p-2 hover:bg-white/5 rounded">
                                    <span className="text-gray-400">Services & Labor</span>
                                    <span className="font-mono text-white">₹{pricing?.total_services_cost?.toLocaleString()}</span>
                                </div>
                                <div className="flex justify-between p-2 hover:bg-white/5 rounded">
                                    <span className="text-gray-400">Taxes (GST)</span>
                                    <span className="font-mono text-white">₹{pricing?.taxes?.toLocaleString()}</span>
                                </div>
                            </div>
                        </div>
                        <div className="bg-yellow-400/10 p-4 rounded-lg border border-yellow-400/30 flex flex-col justify-center text-center">
                            <div className="text-sm text-yellow-400 mb-1">TOTAL ESTIMATE</div>
                            <div className="text-3xl font-bold text-white font-mono">₹{pricing?.grand_total?.toLocaleString()}</div>
                            <div className="text-xs text-gray-400 mt-2">Margin: ₹{pricing?.margin?.toLocaleString()}</div>
                        </div>
                    </div>
                );
            case 'decision':
                return (
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-green-400 font-mono text-lg mb-2">FINAL RECOMMENDATION</h3>
                            <div className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-green-400 to-emerald-600">
                                {data.processing?.recommendation}
                            </div>
                            <p className="text-gray-400 mt-2 max-w-md">Based on high technical compliance (98%) and healthy margin projections, this tender is classified as a WINNABLE opportunity.</p>
                        </div>
                        <div className="text-center">
                            <div className="w-32 h-32 rounded-full border-8 border-green-500/20 flex items-center justify-center relative">
                                <div className="absolute inset-0 rounded-full border-4 border-green-500 border-t-transparent animate-spin duration-[3000ms]"></div>
                                <div>
                                    <div className="text-3xl font-bold text-white">{data.processing?.decision?.win_probability}%</div>
                                    <div className="text-[10px] text-gray-500">WIN PROB</div>
                                </div>
                            </div>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="flex flex-col w-full">
            <div ref={containerRef} className="w-full p-8 flex justify-between items-center relative overflow-visible min-h-[250px] z-20">
                {stages.map((stage, index) => (
                    <React.Fragment key={stage.id}>
                        {/* Stage Node */}
                        <div
                            className={`stage-${stage.id} z-10 flex flex-col items-center relative group cursor-pointer transition-all duration-300 ${activeStage === index ? 'scale-110 opacity-100' : 'opacity-50 hover:opacity-100'}`}
                            onClick={() => handleStageClick(index)}
                        >
                            <div className="relative w-16 h-16 flex items-center justify-center bg-tech-slate rounded-full border-2 border-transparent group-[.active]:border-[${stage.color}] shadow-[0_0_15px_rgba(0,0,0,0.5)] transition-colors duration-300">
                                <stage.icon className="w-8 h-8 text-white" style={{ color: activeStage >= index ? stage.color : '#6b7280' }} />
                                {/* Ripple/Ring */}
                                <div className="icon-web absolute inset-0 rounded-full border border-current opacity-20 scale-125" style={{ color: stage.color }}></div>
                            </div>
                            <div className="mt-4 text-center">
                                <span className="text-xs tracking-widest text-gray-500 block">STAGE {index + 1}</span>
                                <span className={`font-bold text-sm tracking-wide transition-colors ${activeStage === index ? 'text-white' : 'text-gray-500'}`}>{stage.label}</span>
                            </div>

                            {/* Active Indicator Arrow */}
                            {activeStage === index && detailsOpen && (
                                <div className="absolute -bottom-10 text-white animate-bounce">
                                    ▼
                                </div>
                            )}

                            {/* Specific Visuals for stages - KEEPING THESE FOR AMBIANCE */}
                            {stage.id === 'sales' && (
                                <div className="absolute -top-12 flex gap-1 opacity-50 pointer-events-none">
                                    {[1, 2, 3].map(i => <div key={i} className="filter-particle rejected w-2 h-2 bg-red-500 rounded-full"></div>)}
                                    {[1, 2].map(i => <div key={i} className="filter-particle accepted w-2 h-2 bg-green-500 rounded-full"></div>)}
                                </div>
                            )}
                            {stage.id === 'pricing' && (
                                <div className="absolute -bottom-12 font-mono text-tech-cyan text-xs opacity-50 pointer-events-none">
                                    <span className="price-counter">0</span>
                                </div>
                            )}

                        </div>

                        {/* Connector Line (except last) */}
                        {index < stages.length - 1 && (
                            <div className="flex-1 h-1 bg-tech-slate mx-4 relative overflow-hidden rounded">
                                <div className={`connector-${index} h-full w-0 absolute left-0 top-0`}></div>
                            </div>
                        )}
                    </React.Fragment>
                ))}
            </div>

            {/* Details Panel - CSS Transition */}
            <div className={`w-full bg-white/5 border-y overflow-hidden transition-all duration-500 ease-in-out relative z-10 ${detailsClasses}`}>
                <div className="p-8 max-w-5xl mx-auto">
                    {renderDetails()}
                </div>
            </div>
        </div>
    );
};

export default PipelineVisualizer;
