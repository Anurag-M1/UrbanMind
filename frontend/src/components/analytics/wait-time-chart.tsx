'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { GovCard } from '@/components/common/gov-card';

const data = [
  { time: '00:00', current: 15, baseline: 12, variance: 3 },
  { time: '04:00', current: 12, baseline: 10, variance: 2 },
  { time: '08:00', current: 65, baseline: 45, variance: 20 },
  { time: '12:00', current: 85, baseline: 60, variance: 25 },
  { time: '16:00', current: 72, baseline: 55, variance: 17 },
  { time: '20:00', current: 45, baseline: 40, variance: 5 },
  { time: '24:00', current: 20, baseline: 15, variance: 5 },
];

export function WaitTimeChart() {
  return (
    <GovCard title="AVERAGE SECTOR LATENCY (SECONDS)">
      <div className="pt-4">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" vertical={false} />
            <XAxis dataKey="time" stroke="#1a237e" fontSize={10} fontWeight="bold" tickLine={false} axisLine={false} />
            <YAxis stroke="#1a237e" fontSize={10} fontWeight="bold" tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #d1d9e2',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 'bold'
              }}
              cursor={{ fill: '#f8f9fa' }}
            />
            <Legend verticalAlign="bottom" height={36} />
            <Bar dataKey="current" fill="#1a237e" radius={[4, 4, 0, 0]} name="Observed Wait" />
            <Bar dataKey="baseline" fill="#d1d9e2" radius={[4, 4, 0, 0]} name="Historical Baseline" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </GovCard>
  );
}
