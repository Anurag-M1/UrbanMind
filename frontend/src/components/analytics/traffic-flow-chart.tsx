'use client';

import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { GovCard } from '@/components/common/gov-card';

const data = [
  { time: '00:00', northSouth: 120, eastWest: 95, efficiency: 85 },
  { time: '04:00', northSouth: 85, eastWest: 70, efficiency: 92 },
  { time: '08:00', northSouth: 240, eastWest: 210, efficiency: 75 },
  { time: '12:00', northSouth: 280, eastWest: 250, efficiency: 68 },
  { time: '16:00', northSouth: 250, eastWest: 240, efficiency: 72 },
  { time: '20:00', northSouth: 200, eastWest: 180, efficiency: 80 },
  { time: '24:00', northSouth: 130, eastWest: 110, efficiency: 88 },
];

export function TrafficFlowChart() {
  return (
    <GovCard title="SECTOR THROUGHPUT ANALYSIS">
      <div className="pt-4">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
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
            />
            <Legend verticalAlign="bottom" height={36} />
            <Line type="monotone" dataKey="northSouth" stroke="#ff9933" strokeWidth={3} dot={{ r: 4, fill: '#ff9933' }} name="NS Corridor" />
            <Line type="monotone" dataKey="eastWest" stroke="#138808" strokeWidth={3} dot={{ r: 4, fill: '#138808' }} name="EW Corridor" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </GovCard>
  );
}
