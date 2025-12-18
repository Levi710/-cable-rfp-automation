import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import { Activity, Map } from 'lucide-react';

const AnalyticsCharts = () => {
    // 1. Bar Chart Data (Monthly Tender Value)
    const barData = [
        { name: 'Jan', value: 4.2 },
        { name: 'Feb', value: 3.8 },
        { name: 'Mar', value: 5.5 },
        { name: 'Apr', value: 7.2 },
        { name: 'May', value: 6.1 },
        { name: 'Jun', value: 8.4 },
    ];

    // 2. Line Chart Data (Copper Price Trend)
    const lineData = [
        { day: 'Mon', price: 8200 },
        { day: 'Tue', price: 8350 },
        { day: 'Wed', price: 8280 },
        { day: 'Thu', price: 8450 },
        { day: 'Fri', price: 8600 },
    ];

    // 3. Pie Chart Data (Win/Loss)
    const pieData = [
        { name: 'Allocated', value: 65, color: '#4ade80' },
        { name: 'Lost', value: 20, color: '#f87171' },
        { name: 'Pending', value: 15, color: '#facc15' },
    ];

    // 4. Heatmap Data (Regional Demand - Simulated Grid)
    // Darker = Higher Demand
    const heatmapData = [
        { region: 'North', intensity: 'bg-tech-cyan/20' }, { region: 'North', intensity: 'bg-tech-cyan/80' }, { region: 'North', intensity: 'bg-tech-cyan/40' },
        { region: 'West', intensity: 'bg-tech-cyan/60' }, { region: 'West', intensity: 'bg-tech-cyan/90' }, { region: 'West', intensity: 'bg-tech-cyan/30' },
        { region: 'South', intensity: 'bg-tech-cyan/40' }, { region: 'South', intensity: 'bg-tech-cyan/50' }, { region: 'South', intensity: 'bg-tech-cyan/10' },
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-in-up">

            {/* 1. Histogram / Bar Graph */}
            <div className="bg-white/5 border border-white/10 p-6 rounded-xl hover:border-tech-cyan/30 transition-colors">
                <h3 className="text-gray-400 font-mono text-xs mb-4 flex items-center gap-2">
                    <Activity size={14} className="text-tech-cyan" />
                    MONTHLY_TENDER_VALUE (₹ Cr)
                </h3>
                <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={barData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                            <XAxis dataKey="name" stroke="#6b7280" fontSize={10} tickLine={false} />
                            <YAxis stroke="#6b7280" fontSize={10} tickLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }}
                                itemStyle={{ color: '#00f2ea' }}
                            />
                            <Bar dataKey="value" fill="#00f2ea" radius={[4, 4, 0, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* 2. Line Chart (Copper Trends) */}
            <div className="bg-white/5 border border-white/10 p-6 rounded-xl hover:border-tech-magenta/30 transition-colors">
                <h3 className="text-gray-400 font-mono text-xs mb-4 flex items-center gap-2">
                    <Activity size={14} className="text-tech-magenta" />
                    COMMODITY_TREND (LME Cu)
                </h3>
                <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={lineData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                            <XAxis dataKey="day" stroke="#6b7280" fontSize={10} tickLine={false} />
                            <YAxis domain={['auto', 'auto']} stroke="#6b7280" fontSize={10} tickLine={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }}
                                itemStyle={{ color: '#ff0055' }}
                            />
                            <Line type="monotone" dataKey="price" stroke="#ff0055" strokeWidth={2} dot={{ fill: '#ff0055' }} />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* 3. Pie Chart (Win Ratio) */}
            <div className="bg-white/5 border border-white/10 p-6 rounded-xl hover:border-green-400/30 transition-colors flex flex-col">
                <h3 className="text-gray-400 font-mono text-xs mb-4 flex items-center gap-2">
                    <Activity size={14} className="text-green-400" />
                    BID_CONVERSION_RATIO
                </h3>
                <div className="h-48 w-full flex-1 relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie
                                data={pieData}
                                innerRadius={40}
                                outerRadius={60}
                                paddingAngle={5}
                                dataKey="value"
                            >
                                {pieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} stroke="none" />
                                ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#374151', color: '#fff' }} />
                        </PieChart>
                    </ResponsiveContainer>
                    {/* Center Text */}
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                        <div className="text-center">
                            <span className="block text-2xl font-bold text-white">65%</span>
                            <span className="text-[10px] text-gray-400">WIN RATE</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* 4. Heat Map (Regional) */}
            <div className="bg-white/5 border border-white/10 p-6 rounded-xl hover:border-yellow-400/30 transition-colors">
                <h3 className="text-gray-400 font-mono text-xs mb-4 flex items-center gap-2">
                    <Map size={14} className="text-yellow-400" />
                    REGIONAL_DEMAND_HEATMAP
                </h3>
                <div className="h-48 w-full grid grid-cols-3 gap-2">
                    {heatmapData.map((cell, i) => (
                        <div key={i} className={`rounded relative group overflow-hidden ${cell.intensity} border border-transparent hover:border-white/50 transition-all`}>
                            <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                <span className="text-[10px] font-bold text-white bg-black/50 px-1 rounded">{cell.region}</span>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="flex justify-between mt-2 text-[10px] text-gray-500 font-mono">
                    <span>LOW DEMAND</span>
                    <span>HIGH DEMAND</span>
                </div>
            </div>

        </div>
    );
};

export default AnalyticsCharts;
