import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '../../services/api';

const DAY_LABELS = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];

const fallbackData = DAY_LABELS.map(name => ({ name, activite: 5 }));

export const AnalyticsCharts = () => {
  const [chartData, setChartData] = useState(fallbackData);

  useEffect(() => {
    api.get('/admin/dashboard/stats')
      .then((res: any) => {
        const weekly: number[] = res.data?.weekly_activity ?? [];
        if (weekly.length === 7) {
          const today = new Date().getDay(); // 0=Sun
          // backend returns last 7 days newest-last (index 6 = today)
          const rotated = weekly.map((val, i) => {
            const dayIdx = (today - 6 + i + 7) % 7; // Mon=1 → 0 offset
            return { name: DAY_LABELS[(dayIdx + 6) % 7], activite: val };
          });
          setChartData(rotated);
        }
      })
      .catch(() => {}); // keep fallback silently
  }, []);

  return (
    <div className="bg-white dark:bg-slate-800 rounded-3xl p-6 shadow-sm border border-slate-200 dark:border-slate-700 mt-8">
      <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-6">Tendances de la Semaine</h2>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorActivite" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
            <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
            <Tooltip
              contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              formatter={(value: number) => [`${value}%`, 'Activité']}
            />
            <Area type="monotone" dataKey="activite" stroke="#3b82f6" strokeWidth={3} fillOpacity={1} fill="url(#colorActivite)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
