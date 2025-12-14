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
                    const value = a.animations[0].currentValue;
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

    return (
        <div ref={containerRef} className="w-full p-8 flex justify-between items-center relative overflow-hidden min-h-[300px]">
            {stages.map((stage, index) => (
                <React.Fragment key={stage.id}>
                    {/* Stage Node */}
                    <div className={`stage-${stage.id} z-10 flex flex-col items-center relative group opacity-50`}>
                        <div className="relative w-16 h-16 flex items-center justify-center bg-tech-slate rounded-full border-2 border-transparent group-[.active]:border-[${stage.color}] shadow-[0_0_15px_rgba(0,0,0,0.5)] transition-colors duration-300">
                            <stage.icon className="w-8 h-8 text-white" style={{ color: activeStage >= index ? stage.color : '#6b7280' }} />
                            {/* Ripple/Ring */}
                            <div className="icon-web absolute inset-0 rounded-full border border-current opacity-20 scale-125" style={{ color: stage.color }}></div>
                        </div>
                        <div className="mt-4 text-center">
                            <span className="text-xs tracking-widest text-gray-500 block">STAGE {index + 1}</span>
                            <span className="font-bold text-sm tracking-wide" style={{ color: activeStage >= index ? '#fff' : '#4b5563' }}>{stage.label}</span>
                        </div>

                        {/* Specific Visuals for stages */}
                        {stage.id === 'sales' && (
                            <div className="absolute -top-12 flex gap-1">
                                {[1, 2, 3].map(i => <div key={i} className="filter-particle rejected w-2 h-2 bg-red-500 rounded-full"></div>)}
                                {[1, 2].map(i => <div key={i} className="filter-particle accepted w-2 h-2 bg-green-500 rounded-full"></div>)}
                            </div>
                        )}

                        {stage.id === 'pricing' && (
                            <div className="absolute -bottom-12 font-mono text-tech-cyan">
                                Rs <span className="price-counter">0</span>
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
    );
};

export default PipelineVisualizer;
