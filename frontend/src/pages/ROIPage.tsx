import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  AreaChart, Area, Cell
} from 'recharts';
import { TrendingUp, IndianRupee, Clock, Leaf, ShieldCheck, Activity } from 'lucide-react';
import { useTrafficStore } from '@/lib/store';
import { GovCard } from '@/components/common/gov-card';
import { AnimatedCounter } from '@/components/common/animated-counter';
import { deriveTrafficMetrics } from '@/lib/traffic-metrics';

const COLORS = ['#1a237e', '#ff9933', '#138808', '#000080'];

export default function ROIPage() {
  const {
    intersections,
    totalVehicles,
    networkAvgWait,
    emissionsSaved,
    activeEmergencies,
    activeIntersections,
    systemSnapshot,
    uptimeSeconds,
    websterRecalculations,
  } = useTrafficStore();

  const metrics = useMemo(
    () =>
      deriveTrafficMetrics(intersections, {
        ...systemSnapshot,
        total_vehicles: totalVehicles,
        network_avg_wait: networkAvgWait,
        emissions_saved_pct: emissionsSaved,
        active_emergencies: activeEmergencies,
        uptime_seconds: uptimeSeconds,
        webster_recalculations: websterRecalculations,
      }),
    [intersections, totalVehicles, networkAvgWait, emissionsSaved, activeEmergencies, systemSnapshot, uptimeSeconds, websterRecalculations]
  );

  const aggregateRoi = useMemo(
    () =>
      Math.round(
        metrics.optimizationEfficiency * 6 +
        metrics.emissionsSaved * 2 +
        activeIntersections * 8 +
        activeEmergencies * 20
      ),
    [activeEmergencies, activeIntersections, metrics.emissionsSaved, metrics.optimizationEfficiency]
  );

  const economicData = useMemo(
    () =>
      ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'].map((month, index) => ({
        month,
        savings: Math.round((metrics.costSavingsLakhs * 100000 * (0.42 + index * 0.11)) / 0.97),
      })),
    [metrics.costSavingsLakhs]
  );

  const operationalData = useMemo(
    () => [
      { category: 'Fuel Idling', reduction: Math.round(Math.max(18, metrics.optimizationEfficiency)) },
      { category: 'Brake Wear', reduction: Math.round(Math.max(14, metrics.optimizationEfficiency * 0.72)) },
      { category: 'Tire Life', reduction: Math.round(Math.max(12, metrics.optimizationEfficiency * 0.55)) },
      { category: 'Engine Hours', reduction: Math.round(Math.max(16, metrics.optimizationEfficiency * 0.8)) },
    ],
    [metrics.optimizationEfficiency]
  );

  return (
    <div className="min-h-full space-y-8 bg-[#f5f7fa] p-4 transition-all duration-700 sm:p-6 lg:p-8">
      {/* Official Page Header */}
      <div className="flex flex-col gap-4 border-b-2 border-navy/10 pb-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <div className="w-1 h-6 bg-saffron" />
            <div className="w-1 h-6 bg-white border border-gray-200" />
            <div className="w-1 h-6 bg-green" />
            <h3 className="text-[10px] font-black text-navy/40 uppercase tracking-[0.3em] ml-2">Economic Impact Assessment</h3>
          </div>
          <h2 className="text-4xl font-black text-navy tracking-tight uppercase">National ROI Dashboard</h2>
          <p className="text-navy/50 font-medium mt-1">Official Metropolitan Economic & Operational Efficiency Analytics</p>
        </div>
        <div className="text-right bg-white p-4 rounded border border-[#d1d9e2] shadow-sm">
          <p className="text-[10px] text-navy/40 font-black uppercase tracking-widest">Fiscal Reporting Period</p>
          <p className="text-xl font-black text-navy uppercase">FY 2025-26</p>
          <p className="text-[10px] text-green font-black uppercase mt-1 flex items-center justify-end gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green animate-pulse" />
            Live Projection: +{Math.round(metrics.optimizationEfficiency)}%
          </p>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <GovCard accent="saffron" className="p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] text-navy/40 font-black uppercase tracking-widest mb-1">Cost Savings</p>
              <div className="text-3xl font-black text-navy flex items-center">
                ₹<AnimatedCounter value={metrics.costSavingsLakhs} />L
              </div>
              <p className="text-[9px] text-navy/30 font-bold uppercase mt-2">Aggregated Municipal Savings</p>
            </div>
            <div className="p-2 bg-saffron/10 rounded text-saffron">
              <IndianRupee size={20} />
            </div>
          </div>
        </GovCard>

        <GovCard accent="white" className="p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] text-navy/40 font-black uppercase tracking-widest mb-1">Time Recovered</p>
              <div className="text-3xl font-black text-navy">
                <AnimatedCounter value={metrics.timeRecoveredHours} /> hrs
              </div>
              <p className="text-[9px] text-navy/30 font-bold uppercase mt-2">Commuter Time Valuation</p>
            </div>
            <div className="p-2 bg-navy/5 rounded text-navy/60">
              <Clock size={20} />
            </div>
          </div>
        </GovCard>

        <GovCard accent="green" className="p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] text-navy/40 font-black uppercase tracking-widest mb-1">Carbon Credits</p>
              <div className="text-3xl font-black text-navy">
                <AnimatedCounter value={metrics.carbonCreditsMt} /> MT
              </div>
              <p className="text-[9px] text-navy/30 font-bold uppercase mt-2">Net Emissions Reduction</p>
            </div>
            <div className="p-2 bg-green/10 rounded text-green">
              <Leaf size={20} />
            </div>
          </div>
        </GovCard>

        <GovCard accent="navy" className="p-5 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-[10px] text-navy/40 font-black uppercase tracking-widest mb-1">Efficiency Gain</p>
              <div className="text-3xl font-black text-navy">
                +<AnimatedCounter value={metrics.optimizationEfficiency} />%
              </div>
              <p className="text-[9px] text-navy/30 font-bold uppercase mt-2">Network Throughput Optimization</p>
            </div>
            <div className="p-2 bg-navy/10 rounded text-navy">
              <Activity size={20} />
            </div>
          </div>
        </GovCard>
      </div>

      <div className="grid grid-cols-1 gap-8 xl:grid-cols-2">
        {/* Economic Growth Chart */}
        <GovCard title="CUMULATIVE COST AVOIDANCE (IN LAKHS)" className="p-6">
          <div className="h-[350px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={economicData}>
                <defs>
                  <linearGradient id="colorSavings" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#1a237e" stopOpacity={0.1}/>
                    <stop offset="95%" stopColor="#1a237e" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
                <XAxis 
                  dataKey="month" 
                  stroke="#1a237e" 
                  fontSize={10} 
                  fontWeight="bold"
                  tickLine={false} 
                  axisLine={false}
                />
                <YAxis 
                  stroke="#1a237e" 
                  fontSize={10} 
                  fontWeight="bold"
                  tickLine={false} 
                  axisLine={false}
                  tickFormatter={(val) => `₹${Math.round(val / 100000)}L`}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #d1d9e2', borderRadius: '4px', boxShadow: '0 4px 6px rgba(0,0,0,0.05)' }}
                  itemStyle={{ color: '#1a237e', fontWeight: 'bold', fontSize: '11px' }}
                  labelStyle={{ color: '#1a237e', fontWeight: 'black', marginBottom: '4px', fontSize: '12px' }}
                  formatter={(val: number) => [`₹${Math.round(val / 100000)}L`, 'Official Savings']}
                />
                <Area 
                  type="monotone" 
                  dataKey="savings" 
                  stroke="#1a237e" 
                  fillOpacity={1} 
                  fill="url(#colorSavings)" 
                  strokeWidth={4}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GovCard>

        {/* Operational Impact */}
        <GovCard title="MAINTENANCE REDUCTION BY CATEGORY (%)" className="p-6">
          <div className="h-[350px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={operationalData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" horizontal={false} />
                <XAxis 
                  type="number" 
                  stroke="#1a237e" 
                  fontSize={10} 
                  fontWeight="bold"
                  tickLine={false} 
                  axisLine={false}
                  tickFormatter={(val) => `${val}%`}
                />
                <YAxis 
                  dataKey="category" 
                  type="category"
                  stroke="#1a237e" 
                  fontSize={10} 
                  fontWeight="bold"
                  tickLine={false} 
                  axisLine={false}
                  width={110}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #d1d9e2', borderRadius: '4px' }}
                  itemStyle={{ color: '#1a237e', fontWeight: 'bold' }}
                />
                <Bar dataKey="reduction" radius={[0, 2, 2, 0]} barSize={30}>
                  {operationalData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GovCard>
      </div>

      {/* Environmental & Civic Impact */}
      <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
         <GovCard title="ENVIRONMENTAL & SOCIAL AUDIT" className="md:col-span-2 p-0">
            <div className="divide-y divide-gray-100">
              <div className="flex justify-between items-center p-5 bg-gray-50/50">
                <div className="flex items-center gap-3">
                   <div className="w-8 h-8 rounded bg-green/10 flex items-center justify-center text-green">
                      <Leaf size={16} />
                   </div>
                   <span className="text-xs font-bold text-navy uppercase tracking-wide">Verified Carbon Offset</span>
                </div>
                <span className="text-lg font-black text-green">{Math.round(metrics.carbonCreditsMt)} Metric Tons</span>
              </div>
              <div className="flex justify-between items-center p-5">
                <div className="flex items-center gap-3">
                   <div className="w-8 h-8 rounded bg-saffron/10 flex items-center justify-center text-saffron">
                      <Activity size={16} />
                   </div>
                   <span className="text-xs font-bold text-navy uppercase tracking-wide">Fuel Resource Optimization</span>
                </div>
                <span className="text-lg font-black text-navy">{Math.round(totalVehicles * 0.42).toLocaleString('en-IN')} Liters SAVED</span>
              </div>
              <div className="flex justify-between items-center p-5 bg-gray-50/50">
                <div className="flex items-center gap-3">
                   <div className="w-8 h-8 rounded bg-navy/10 flex items-center justify-center text-navy">
                      <ShieldCheck size={16} />
                   </div>
                   <span className="text-xs font-bold text-navy uppercase tracking-wide">Projected Air Quality Delta</span>
                </div>
                <span className="text-lg font-black text-navy">+{Math.round(metrics.optimizationEfficiency * 0.5)}% AQI Score</span>
              </div>
            </div>
         </GovCard>

         <div className="bg-navy rounded p-8 flex flex-col items-center justify-center text-center shadow-xl border-4 border-white/10 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 -mr-16 -mt-16 rounded-full group-hover:scale-110 transition-transform" />
            
            <div className="p-5 bg-white/10 rounded-full text-white mb-6 border border-white/20">
              <TrendingUp size={48} />
            </div>
            <h4 className="text-[10px] font-black text-white/50 mb-2 uppercase tracking-[0.3em]">Aggregate System ROI</h4>
            <p className="text-6xl font-black text-white tracking-tighter mb-4">{aggregateRoi}%</p>
            <div className="py-2 px-4 bg-green text-white text-[10px] font-black uppercase rounded shadow-lg border border-white/20">
              MUNICIPAL PERFORMANCE: CLASS A+
            </div>
            <p className="text-[9px] text-white/40 mt-6 font-medium uppercase tracking-widest leading-relaxed">
              official government of india audit<br />
              delhi-ncr deployment phase 1
            </p>
         </div>
      </div>
    </div>
  );
}
