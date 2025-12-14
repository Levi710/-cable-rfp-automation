import React, { useCallback } from 'react';
import { Upload, FileText, ArrowRight } from 'lucide-react';

const LandingPage = ({ onStart }) => {
    // Visual-only drag and drop for showcase
    const handleDrop = (e) => {
        e.preventDefault();
        onStart();
    };

    return (
        <div className="relative min-h-screen flex flex-col items-center justify-center p-4">
            <div className="text-center mb-12 animate-fade-in-up">
                <h1 className="text-6xl font-black font-mono tracking-tighter mb-4">
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-tech-cyan to-white">AUTOMATE</span> YOUR
                    <br />
                    CABLE <span className="text-tech-magenta">RFPs</span>
                </h1>
                <p className="text-xl text-gray-400 max-w-2xl mx-auto">
                    Deploy AI agents to parse, analyze, and bid on tender documents in seconds.
                </p>
            </div>

            <div
                className="w-full max-w-xl aspect-video border-2 border-dashed border-white/20 rounded-2xl bg-white/5 backdrop-blur-sm flex flex-col items-center justify-center cursor-pointer hover:border-tech-cyan hover:bg-tech-cyan/5 transition-all group"
                onClick={onStart}
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
            >
                <div className="w-20 h-20 bg-white/10 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Upload className="text-tech-cyan w-10 h-10" />
                </div>
                <h3 className="text-2xl font-mono font-bold text-white mb-2">UPLOAD TENDER DOC</h3>
                <p className="text-gray-500 font-mono text-sm">Drag & Drop PDF, XLSX, or DOCX</p>
            </div>

            <div className="mt-12 flex gap-4 text-gray-500 font-mono text-xs">
                <div className="flex items-center gap-2">
                    <FileText size={14} />
                    <span>SUPPORTED: PDF 2.0</span>
                </div>
                <div className="flex items-center gap-2">
                    <FileText size={14} />
                    <span>EXCEL 2021+</span>
                </div>
            </div>

            <button
                onClick={onStart}
                className="mt-12 bg-tech-cyan hover:bg-cyan-400 text-black font-bold py-3 px-8 rounded-full flex items-center gap-2 transition-transform hover:scale-105"
            >
                Start Simulation <ArrowRight size={18} />
            </button>
        </div>
    );
};

export default LandingPage;
