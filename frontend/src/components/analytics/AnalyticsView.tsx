import { useEffect, useMemo, useState } from 'react';
import { AreaChart, Area, LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { getFlowSeries } from '../../api/emergency';
import type { FlowSeriesEntry } from '../../types';
import { GovCard } from '../common/gov-card';
import { useTrafficStore } from '@/lib/store';
import { deriveTrafficMetrics } from '@/lib/traffic-metrics';

const CHART_COLORS = ['#1a237e', '#ff9933', '#138808', '#d32f2f', '#000080', '#546e7a'];

function StatCard({ label, value, color, suffix = '', trend, trendLabel }: any) {
  const val = typeof value === 'number' ? Math.round(value) : value;
  const accentMap: Record<string, 'navy' | 'saffron' | 'green' | 'white'> = {
    cyan: 'navy',
    green: 'green',
    red: 'navy',
    amber: 'saffron'
  };
  
  return (
    <GovCard accent={accentMap[color] || 'navy'} className="p-4 shadow-sm">
      <h4 className="text-[10px] text-navy/40 font-black uppercase tracking-widest mb-1">{label}</h4>
      <div className="text-2xl font-black text-navy font-mono">
        {Number(val).toLocaleString('en-IN')}{suffix}
      </div>
      {trend && (
        <div className={`text-[10px] mt-2 font-bold uppercase transition-colors ${trend === 'down' ? 'text-green' : 'text-red-600'}`}>
          {trend === 'down' ? '↓' : '↑'} {trendLabel}
        </div>
      )}
    </GovCard>
  );
}

export function AnalyticsView() {
  const [flowData, setFlowData] = useState<FlowSeriesEntry[]>([]);
  const {
    intersections,
    networkAvgWait,
    totalVehicles,
    emissionsSaved,
    activeEmergencies,
    uptimeSeconds,
    websterRecalculations,
  } = useTrafficStore();

  useEffect(() => {
    const load = async () => {
      try {
        const flow = await getFlowSeries();
        setFlowData(flow.flow_series || []);
      } catch {
        // Ignore
      }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  const derived = useMemo(
    () => deriveTrafficMetrics(intersections, {
      total_vehicles: totalVehicles,
      network_avg_wait: networkAvgWait,
      emissions_saved_pct: emissionsSaved,
      active_emergencies: activeEmergencies,
      uptime_seconds: uptimeSeconds,
      webster_recalculations: websterRecalculations,
    }),
    [intersections, totalVehicles, networkAvgWait, emissionsSaved, activeEmergencies, uptimeSeconds, websterRecalculations]
  );

  const waitComparisonData = useMemo(
    () =>
      intersections
        .map((intersection) => ({
          name: intersection.name.replace(/\s(Signal|Crossing|Junction|Chowk|Gate 3)/g, ''),
          wait: Math.round(intersection.avgWaitTime),
        }))
        .sort((a, b) => a.wait - b.wait),
    [intersections]
  );

  const adaptiveVsFixed = useMemo(
    () =>
      flowData.map((entry) => ({
        hour: entry.hour,
        fixed: 45,
        adaptive: Math.max(8, Math.round(networkAvgWait + (entry.total / Math.max(1, flowData[0]?.total || entry.total)) * 6)),
      })),
    [flowData, networkAvgWait]
  );

  if (!intersections.length) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-2">
          <div className="w-8 h-8 border-4 border-navy/10 border-t-navy rounded-full animate-spin" />
          <div className="text-navy/40 text-[10px] font-black uppercase tracking-widest">Retrieving Official Data...</div>
        </div>
      </div>
    );
  }

  const vehicleDistribution = [
    { name: 'Car', value: 55, color: '#1a237e' },
    { name: 'Motorcycle', value: 20, color: '#ff9933' },
    { name: 'Auto', value: 15, color: '#138808' },
    { name: 'Bus', value: 5, color: '#000080' },
    { name: 'Truck', value: 5, color: '#d32f2f' },
  ];

  return (
    <div className="h-full space-y-6 overflow-y-auto pb-8 animate-in fade-in duration-700">
      {/* Summary KPIs */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Vehicles Today" value={derived.totalVehicles} color="cyan" />
        <StatCard label="Network Avg Wait" value={derived.networkAvgWait} suffix="s" color="green" trend="down" trendLabel={`${Math.round(derived.optimizationEfficiency)}% SAVING`} />
        <StatCard label="Best Sector" value={derived.bestIntersection?.avgWaitTime ?? 0} suffix="s" color="green" />
        <StatCard label="Emergency Ops" value={derived.activeEmergencies} color="red" />
        <StatCard label="CO₂ Saved" value={derived.emissionsSaved} suffix="%" color="green" />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <GovCard title="24h VEHICULAR FLOW TRANSCRIPT" className="p-6">
          <div className="h-[250px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={flowData}>
                <defs>
                  <linearGradient id="nsGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ff9933" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#ff9933" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="ewGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#138808" stopOpacity={0.15}/>
                    <stop offset="95%" stopColor="#138808" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
                <XAxis dataKey="hour" stroke="#1a237e" fontSize={10} fontWeight="bold" />
                <YAxis stroke="#1a237e" fontSize={10} fontWeight="bold" />
                <Tooltip 
                  contentStyle={{ background: '#ffffff', border: '1px solid #d1d9e2', borderRadius: 4, fontSize: 11, fontWeight: 'bold' }} 
                  formatter={(val: number) => [Math.round(val), 'Vehicles']}
                />
                <Area type="monotone" dataKey="ns_flow" stroke="#ff9933" fill="url(#nsGrad)" strokeWidth={3} name="North-South" />
                <Area type="monotone" dataKey="ew_flow" stroke="#138808" fill="url(#ewGrad)" strokeWidth={3} name="East-West" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </GovCard>

        <GovCard title="SECTOR LATENCY AUDIT (SECONDS)" className="p-6">
          <div className="h-[250px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={waitComparisonData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" horizontal={false} />
                <XAxis type="number" stroke="#1a237e" fontSize={10} fontWeight="bold" />
                <YAxis dataKey="name" type="category" stroke="#1a237e" fontSize={9} fontWeight="bold" width={80} />
                <Tooltip 
                  contentStyle={{ background: '#ffffff', border: '1px solid #d1d9e2', borderRadius: 4, fontSize: 11, fontWeight: 'bold' }} 
                  formatter={(val: number) => [`${Math.round(val)}s`, 'Avg Delay']}
                />
                <Bar dataKey="wait" radius={[0, 2, 2, 0]} barSize={20}>
                  {waitComparisonData.map((entry, index) => (
                    <Cell key={index} fill={entry.wait < 20 ? '#138808' : entry.wait < 30 ? '#ff9933' : '#d32f2f'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GovCard>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 gap-6 pb-8 xl:grid-cols-2">
        <GovCard title="ADAPTIVE vs FIXED SIGNAL PERFORMANCE" className="p-6">
          <div className="h-[250px] w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={adaptiveVsFixed}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
                <XAxis dataKey="hour" stroke="#1a237e" fontSize={10} fontWeight="bold" />
                <YAxis stroke="#1a237e" fontSize={10} fontWeight="bold" domain={[0, 60]} />
                <Tooltip 
                  contentStyle={{ background: '#ffffff', border: '1px solid #d1d9e2', borderRadius: 4, fontSize: 11, fontWeight: 'bold' }} 
                />
                <Line type="monotone" dataKey="fixed" stroke="#9e9e9e" strokeDasharray="6 4" name="Manual Timer (45s)" dot={false} strokeWidth={2} />
                <Line type="monotone" dataKey="adaptive" stroke="#1a237e" name="UrbanMind AI Control" dot={true} strokeWidth={4} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </GovCard>

        <GovCard title="MUNICIPAL VEHICLE CLASSIFICATION" className="p-6">
          <div className="mt-4 flex h-[320px] flex-col items-center gap-4 lg:h-[250px] lg:flex-row">
            <div className="h-full w-full lg:max-w-[60%]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={vehicleDistribution} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={50} outerRadius={85} paddingAngle={5}>
                    {vehicleDistribution.map((entry, index) => (
                      <Cell key={index} fill={entry.color} strokeWidth={2} stroke="#fff" />
                    ))}
                  </Pie>
                  <Tooltip 
                     contentStyle={{ background: '#ffffff', border: '1px solid #d1d9e2', borderRadius: 4, fontSize: 11, fontWeight: 'bold' }} 
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="w-full flex-1 space-y-3 lg:pl-4">
              {vehicleDistribution.map(v => (
                <div key={v.name} className="flex flex-col">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="w-2 h-2 rounded-full" style={{ background: v.color }} />
                    <span className="text-[10px] font-black text-navy uppercase tracking-widest">{v.name}</span>
                  </div>
                  <div className="flex items-end justify-between">
                     <span className="text-sm font-black text-navy">{v.value}%</span>
                     <div className="w-24 h-1 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full" style={{ width: `${v.value}%`, background: v.color }} />
                     </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </GovCard>
      </div>
    </div>
  );
}
