import React, { useEffect, useRef } from 'react';
import anime from 'animejs';
import { Brain, Database, ShieldCheck, Calculator, FileText, Search, FileOutput, Layers } from 'lucide-react';

const AgentNetwork = ({ isActive }) => {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!isActive) return;

        const tl = anime.timeline({
            easing: 'linear',
            loop: true
        });

        // 1. Packet: Main -> Sales
        tl.add({
            targets: '.packet-main-sales',
            translateY: [0, 80],
            opacity: [0, 1, 0],
            duration: 1000,
            easing: 'easeOutQuad'
        })
            // 2. Packet: Sales -> Identify
            .add({
                targets: '.packet-sales-identify',
                translateX: [0, 120],
                opacity: [0, 1, 0],
                duration: 800,
                easing: 'easeOutQuad'
            })
            // 3. Packet: Identify -> Summarize (Visual logic flow)
            .add({
                targets: '.packet-identify-summarize',
                translateX: [0, -60],
                translateY: [0, 80],
                opacity: [0, 1, 0],
                duration: 800,
                easing: 'easeOutQuad'
            })
            // 4. Split: Summarize -> Tech & Pricing
            .add({
                targets: ['.packet-sum-tech', '.packet-sum-pricing'],
                translateX: (el) => el.classList.contains('packet-sum-tech') ? [0, -100] : [0, 100],
                translateY: [0, 60],
                opacity: [0, 1, 0],
                duration: 1000,
                easing: 'easeOutQuad'
            })
            // 5. Tech->Match & Pricing->Estimate
            .add({
                targets: ['.packet-tech-match', '.packet-pricing-est'],
                translateY: [0, 60],
                opacity: [0, 1, 0],
                duration: 800,
                easing: 'easeOutQuad'
            })
            // 6. Converge: Match & Estimate -> Prepare Response
            .add({
                targets: ['.packet-match-response', '.packet-est-response'],
                translateX: (el) => el.classList.contains('packet-match-response') ? [0, 100] : [0, -100],
                translateY: [0, 60],
                opacity: [0, 1, 0],
                duration: 1000,
                easing: 'easeOutQuad'
            });

        // Pulse effect for nodes
        anime({
            targets: '.node-pulse',
            scale: [1, 1.05, 1],
            boxShadow: [
                '0 0 0px rgba(0, 242, 234, 0)',
                '0 0 20px rgba(0, 242, 234, 0.4)',
                '0 0 0px rgba(0, 242, 234, 0)'
            ],
            duration: 2000,
            loop: true,
            delay: anime.stagger(300)
        });

    }, [isActive]);

    return (
        <div ref={containerRef} className="relative w-full h-[600px] flex justify-center pt-8 bg-black/20 rounded-xl border border-white/5 overflow-hidden">

            {/* SVG Connections with more distinct hierarchy */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-gray-700" style={{ zIndex: 0 }}>
                {/* Main -> Sales */}
                <line x1="50%" y1="50" x2="50%" y2="130" strokeWidth="2" />
                {/* Sales -> Identify */}
                <line x1="50%" y1="130" x2="70%" y2="130" strokeWidth="2" />
                {/* Identify -> Summarize (Curved or direct?) Let's go Sales -> Summarize directly for visual simplicity in tree, 
                    but diagram had side step. Let's do Sales -> Summarize and Sales -> Identify as separate or sequential.
                    Diagram: Sales -> Identify -> (arrow down to Pricing?? No, probably back to flow).
                    Let's stick to the core flow: Sales -> Summarize */}
                <line x1="50%" y1="130" x2="50%" y2="210" strokeWidth="2" />

                {/* Summarize -> Tech (Left) & Pricing (Right) */}
                <path d="M 50% 250 L 50% 270 L 30% 270 L 30% 300" fill="none" strokeWidth="2" strokeDasharray="5,5" />
                <path d="M 50% 250 L 50% 270 L 70% 270 L 70% 300" fill="none" strokeWidth="2" strokeDasharray="5,5" />

                {/* Tech -> Match SKUs */}
                <line x1="30%" y1="340" x2="30%" y2="400" strokeWidth="2" />

                {/* Pricing -> Estimate Costs */}
                <line x1="70%" y1="340" x2="70%" y2="400" strokeWidth="2" />

                {/* Converge to Response */}
                <path d="M 30% 440 L 30% 460 L 50% 460 L 50% 490" fill="none" strokeWidth="2" />
                <path d="M 70% 440 L 70% 460 L 50% 460 L 50% 490" fill="none" strokeWidth="2" />
            </svg>

            {/* NODES */}

            {/* 1. Main Agent */}
            <div className="absolute top-4 left-1/2 -translate-x-1/2 flex flex-col items-center z-20">
                <div className="node-pulse w-12 h-12 bg-gray-900 border-2 border-blue-500 rounded-full flex items-center justify-center">
                    <Brain className="w-6 h-6 text-blue-500" />
                </div>
                <span className="text-[10px] text-blue-400 mt-1 font-mono bg-black/50 px-1 rounded">MAIN AGENT</span>
                <div className="packet-main-sales absolute top-12 w-2 h-2 bg-blue-500 rounded-full"></div>
            </div>

            {/* 2. Sales Agent */}
            <div className="absolute top-[130px] left-1/2 -translate-x-1/2 flex flex-col items-center z-20">
                <div className="node-pulse w-12 h-12 bg-gray-900 border-2 border-magenta-500 rounded-full flex items-center justify-center border-tech-magenta">
                    <ShieldCheck className="w-6 h-6 text-tech-magenta" />
                </div>
                <span className="text-[10px] text-tech-magenta mt-1 font-mono bg-black/50 px-1 rounded">SALES AGENT</span>
                {/* Packet to Identify (Side) */}
                <div className="packet-sales-identify absolute left-12 top-6 w-2 h-2 bg-tech-magenta rounded-full"></div>
            </div>

            {/* 2b. Identify RFPs (Side Node) */}
            <div className="absolute top-[130px] left-[70%] -translate-x-1/2 flex flex-col items-center z-10">
                <div className="w-10 h-10 bg-gray-900 border border-gray-600 rounded flex items-center justify-center">
                    <Search className="w-5 h-5 text-gray-400" />
                </div>
                <span className="text-[10px] text-gray-500 mt-1 font-mono">IDENTIFY RFP</span>
                {/* Packet returning or implicit */}
            </div>

            {/* 3. Summarize */}
            <div className="absolute top-[210px] left-1/2 -translate-x-1/2 flex flex-col items-center z-20">
                <div className="node-pulse w-12 h-12 bg-gray-900 border-2 border-purple-500 rounded-full flex items-center justify-center">
                    <FileText className="w-6 h-6 text-purple-500" />
                </div>
                <span className="text-[10px] text-purple-400 mt-1 font-mono bg-black/50 px-1 rounded">SUMMARIZE</span>
                <div className="packet-sum-tech absolute top-12 w-2 h-2 bg-tech-cyan rounded-full"></div>
                <div className="packet-sum-pricing absolute top-12 w-2 h-2 bg-yellow-400 rounded-full"></div>
            </div>

            {/* 4a. Technical Agent */}
            <div className="absolute top-[300px] left-[30%] -translate-x-1/2 flex flex-col items-center z-20">
                <div className="node-pulse w-12 h-12 bg-gray-900 border-2 border-tech-cyan rounded-full flex items-center justify-center">
                    <Database className="w-6 h-6 text-tech-cyan" />
                </div>
                <span className="text-[10px] text-tech-cyan mt-1 font-mono bg-black/50 px-1 rounded">TECHNICAL</span>
                <div className="packet-tech-match absolute top-12 w-2 h-2 bg-tech-cyan rounded-full"></div>
            </div>

            {/* 4b. Pricing Agent */}
            <div className="absolute top-[300px] left-[70%] -translate-x-1/2 flex flex-col items-center z-20">
                <div className="node-pulse w-12 h-12 bg-gray-900 border-2 border-yellow-400 rounded-full flex items-center justify-center">
                    <Calculator className="w-6 h-6 text-yellow-400" />
                </div>
                <span className="text-[10px] text-yellow-400 mt-1 font-mono bg-black/50 px-1 rounded">PRICING</span>
                <div className="packet-pricing-est absolute top-12 w-2 h-2 bg-yellow-400 rounded-full"></div>
            </div>

            {/* 5a. Match SKUs */}
            <div className="absolute top-[400px] left-[30%] -translate-x-1/2 flex flex-col items-center z-10">
                <div className="w-32 h-8 bg-gray-900 border border-tech-cyan/50 rounded flex items-center justify-center">
                    <span className="text-xs text-tech-cyan font-mono">MATCH SKUs</span>
                </div>
                <div className="packet-match-response absolute top-8 w-2 h-2 bg-tech-cyan rounded-full"></div>
            </div>

            {/* 5b. Estimate Costs */}
            <div className="absolute top-[400px] left-[70%] -translate-x-1/2 flex flex-col items-center z-10">
                <div className="w-32 h-8 bg-gray-900 border border-yellow-400/50 rounded flex items-center justify-center">
                    <span className="text-xs text-yellow-400 font-mono">ESTIMATE COSTS</span>
                </div>
                <div className="packet-est-response absolute top-8 w-2 h-2 bg-yellow-400 rounded-full"></div>
            </div>

            {/* 6. Prepare Response */}
            <div className="absolute top-[490px] left-1/2 -translate-x-1/2 flex flex-col items-center z-20">
                <div className="node-pulse w-14 h-14 bg-gray-900 border-2 border-green-500 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(34,197,94,0.3)]">
                    <FileOutput className="w-7 h-7 text-green-500" />
                </div>
                <span className="text-xs text-green-400 mt-2 font-mono font-bold bg-black/50 px-2 rounded">PREPARE RESPONSE</span>
            </div>

        </div>
    );
};

export default AgentNetwork;
