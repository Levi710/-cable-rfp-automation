import React, { useEffect, useRef } from 'react';
import anime from 'animejs';
import { Brain, Database, ShieldCheck, Calculator } from 'lucide-react';

const AgentNetwork = ({ isActive }) => {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!isActive) return;

        // Animate particles traveling from Hub to Satellites
        const tl = anime.timeline({
            easing: 'linear',
            loop: true
        });

        // Hub Pulse
        anime({
            targets: '.hub-node',
            scale: [1, 1.1, 1],
            boxShadow: [
                '0 0 20px rgba(0, 242, 234, 0.2)',
                '0 0 50px rgba(0, 242, 234, 0.6)',
                '0 0 20px rgba(0, 242, 234, 0.2)'
            ],
            duration: 2000,
            loop: true,
            easing: 'easeInOutSine'
        });

        // Packets: Hub -> Sales
        anime({
            targets: '.packet-sales',
            translateX: [0, -150], // Adjust based on layout
            translateY: [0, -80],
            opacity: [0, 1, 0],
            duration: 1500,
            loop: true,
            easing: 'easeOutQuad',
            delay: 500
        });

        // Packets: Hub -> Tech
        anime({
            targets: '.packet-tech',
            translateX: [0, 150],
            translateY: [0, -80],
            opacity: [0, 1, 0],
            duration: 1500,
            loop: true,
            easing: 'easeOutQuad',
            delay: 1000
        });

        // Packets: Hub -> Pricing
        anime({
            targets: '.packet-pricing',
            translateX: [0, 0],
            translateY: [0, 150],
            opacity: [0, 1, 0],
            duration: 1500,
            loop: true,
            easing: 'easeOutQuad',
            delay: 1500
        });

    }, [isActive]);

    return (
        <div ref={containerRef} className="relative w-full h-[500px] flex items-center justify-center">

            {/* Connection Lines (SVG) */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none stroke-current text-white/10" style={{ zIndex: 0 }}>
                {/* Center to Top-Left (Sales) */}
                <line x1="50%" y1="50%" x2="calc(50% - 150px)" y2="calc(50% - 80px)" strokeWidth="2" strokeDasharray="5,5" />
                {/* Center to Top-Right (Tech) */}
                <line x1="50%" y1="50%" x2="calc(50% + 150px)" y2="calc(50% - 80px)" strokeWidth="2" strokeDasharray="5,5" />
                {/* Center to Bottom (Pricing) */}
                <line x1="50%" y1="50%" x2="50%" y2="calc(50% + 150px)" strokeWidth="2" strokeDasharray="5,5" />
            </svg>

            {/* Central Hub */}
            <div className="hub-node absolute z-20 w-24 h-24 bg-black border-2 border-tech-cyan rounded-full flex items-center justify-center">
                <Brain className="text-tech-cyan w-10 h-10" />
                <div className="absolute -bottom-8 text-tech-cyan font-mono text-xs tracking-widest">ORCHESTRATOR</div>
            </div>

            {/* Satellite: SALES */}
            <div className="absolute z-10 w-16 h-16 bg-black border border-tech-magenta rounded-full flex items-center justify-center" style={{ transform: 'translate(-150px, -80px)' }}>
                <ShieldCheck className="text-tech-magenta w-6 h-6" />
                <div className="absolute -top-6 text-tech-magenta font-mono text-[10px] tracking-widest">SALES</div>
            </div>

            {/* Satellite: TECH */}
            <div className="absolute z-10 w-16 h-16 bg-black border border-tech-cyan rounded-full flex items-center justify-center" style={{ transform: 'translate(150px, -80px)' }}>
                <Database className="text-tech-cyan w-6 h-6" />
                <div className="absolute -top-6 text-tech-cyan font-mono text-[10px] tracking-widest">TECH</div>
            </div>

            {/* Satellite: PRICING */}
            <div className="absolute z-10 w-16 h-16 bg-black border border-yellow-400 rounded-full flex items-center justify-center" style={{ transform: 'translate(0px, 150px)' }}>
                <Calculator className="text-yellow-400 w-6 h-6" />
                <div className="absolute -bottom-6 text-yellow-400 font-mono text-[10px] tracking-widest">PRICING</div>
            </div>

            {/* Data Packets */}
            <div className="packet-sales absolute w-3 h-3 bg-tech-magenta rounded-full shadow-[0_0_10px_currentColor] z-10"></div>
            <div className="packet-tech absolute w-3 h-3 bg-tech-cyan rounded-full shadow-[0_0_10px_currentColor] z-10"></div>
            <div className="packet-pricing absolute w-3 h-3 bg-yellow-400 rounded-full shadow-[0_0_10px_currentColor] z-10"></div>

        </div>
    );
};

export default AgentNetwork;
