import { Activity, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react';
import type { Stats } from '../api';

interface StatsBarProps {
  stats: Stats;
}

export default function StatsBar({ stats }: StatsBarProps) {
  const cards = [
    {
      label: 'Total Incidents',
      value: stats.total_incidents,
      icon: Activity,
      color: 'text-accent-cyan',
      bg: 'from-accent-cyan/10 to-accent-cyan/5',
    },
    {
      label: 'Analyzed',
      value: stats.completed,
      icon: CheckCircle,
      color: 'text-accent-green',
      bg: 'from-accent-green/10 to-accent-green/5',
    },
    {
      label: 'In Progress',
      value: stats.analyzing,
      icon: AlertTriangle,
      color: 'text-accent-amber',
      bg: 'from-accent-amber/10 to-accent-amber/5',
    },
    {
      label: 'Avg Confidence',
      value: stats.avg_confidence > 0 ? `${Math.round(stats.avg_confidence * 100)}%` : '—',
      icon: TrendingUp,
      color: 'text-accent-purple',
      bg: 'from-accent-purple/10 to-accent-purple/5',
    },
  ];

  return (
    <div className="max-w-[1600px] mx-auto px-4 sm:px-6 py-4">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {cards.map((card) => (
          <div
            key={card.label}
            className={`glass-card p-4 bg-gradient-to-br ${card.bg}`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-white/40 font-medium uppercase tracking-wider">
                  {card.label}
                </p>
                <p className={`text-2xl font-bold mt-1 ${card.color}`}>
                  {card.value}
                </p>
              </div>
              <card.icon className={`w-8 h-8 ${card.color} opacity-30`} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
