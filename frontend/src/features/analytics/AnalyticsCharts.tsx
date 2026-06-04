import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const mockData = [
  { name: 'Lun', revenus: 4000, occupation: 85 },
  { name: 'Mar', revenus: 3000, occupation: 90 },
  { name: 'Mer', revenus: 2000, occupation: 70 },
  { name: 'Jeu', revenus: 2780, occupation: 95 },
  { name: 'Ven', revenus: 1890, occupation: 80 },
  { name: 'Sam', revenus: 2390, occupation: 100 },
];

export const AnalyticsCharts = () => {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-3xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 mt-8">
      <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-6">Tendances de la Semaine</h2>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={mockData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorRevenus" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value} MAD`} />
            <Tooltip 
              contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)' }}
            />
            <Area type="monotone" dataKey="revenus" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorRevenus)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
