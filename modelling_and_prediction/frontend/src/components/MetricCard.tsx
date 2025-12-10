import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  trend?: 'up' | 'down' | 'neutral';
}

export function MetricCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon,
  color = 'default',
  trend
}: MetricCardProps) {
  const colorClasses = {
    default: 'text-foreground',
    success: 'text-success',
    warning: 'text-warning',
    danger: 'text-primary',
    info: 'text-accent',
  };

  const bgClasses = {
    default: 'bg-muted/50',
    success: 'bg-success/10',
    warning: 'bg-warning/10',
    danger: 'bg-primary/10',
    info: 'bg-accent/10',
  };

  return (
    <div className="metric-card group">
      <div className="flex items-start justify-between mb-3">
        <div className={cn(
          "p-2.5 rounded-lg transition-all duration-300 group-hover:scale-110",
          bgClasses[color]
        )}>
          <Icon className={cn("w-5 h-5", colorClasses[color])} />
        </div>
        {trend && (
          <span className={cn(
            "text-xs font-medium px-2 py-1 rounded-full",
            trend === 'up' && "bg-primary/10 text-primary",
            trend === 'down' && "bg-success/10 text-success",
            trend === 'neutral' && "bg-muted text-muted-foreground"
          )}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}
          </span>
        )}
      </div>
      
      <p className="text-sm text-muted-foreground mb-1">{title}</p>
      
      <p className={cn(
        "text-2xl font-bold font-mono tracking-tight",
        colorClasses[color]
      )}>
        {value}
      </p>
      
      {subtitle && (
        <p className="text-xs text-muted-foreground mt-1">{subtitle}</p>
      )}
    </div>
  );
}
