'use client';

import React from 'react';
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from 'recharts';
import { GovCard } from '@/components/common/gov-card';

const data = [
  { name: 'Cars', value: 65 },
  { name: 'Trucks', value: 15 },
  { name: 'Buses', value: 12 },
  { name: 'Motorcycles', value: 8 },
];

const COLORS = ['#1a237e', '#ff9933', '#138808', '#546e7a'];

export function VehicleTypeChart() {
  return (
    <GovCard title="VEHICLE CLASSIFICATION AUDIT">
      <div className="pt-4">
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, value }) => `${name} ${value}%`}
              outerRadius={100}
              dataKey="value"
              stroke="#fff"
              strokeWidth={2}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#ffffff',
                border: '1px solid #d1d9e2',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 'bold'
              }}
              itemStyle={{ color: '#1a237e' }}
            />
            <Legend verticalAlign="bottom" height={36}/>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </GovCard>
  );
}
