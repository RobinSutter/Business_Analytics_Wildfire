import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';
import { RiskCategory } from '@/types/prediction';

interface RiskGaugeProps {
  score: number;
  category: RiskCategory;
  animate?: boolean;
}

export function RiskGauge({ score, category, animate = true }: RiskGaugeProps) {
  const [displayScore, setDisplayScore] = useState(animate ? 0 : score);

  useEffect(() => {
    if (!animate) {
      setDisplayScore(score);
      return;
    }

    // Animate the score
    const duration = 1500;
    const steps = 60;
    const increment = score / steps;
    let current = 0;
    
    const timer = setInterval(() => {
      current += increment;
      if (current >= score) {
        setDisplayScore(score);
        clearInterval(timer);
      } else {
        setDisplayScore(Math.round(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [score, animate]);

  const getColor = () => {
    if (score < 20) return { stroke: 'hsl(145, 63%, 49%)', glow: 'rgba(46, 204, 113, 0.5)' };
    if (score < 40) return { stroke: 'hsl(204, 70%, 53%)', glow: 'rgba(52, 152, 219, 0.5)' };
    if (score < 60) return { stroke: 'hsl(37, 90%, 51%)', glow: 'rgba(243, 156, 18, 0.5)' };
    if (score < 80) return { stroke: 'hsl(28, 80%, 52%)', glow: 'rgba(230, 126, 34, 0.5)' };
    return { stroke: 'hsl(6, 78%, 57%)', glow: 'rgba(231, 76, 60, 0.5)' };
  };

  const color = getColor();
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference - (displayScore / 100) * circumference;

  const isCritical = score >= 80;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative">
        {/* Glow effect */}
        <div
          className={cn(
            "absolute inset-0 rounded-full blur-xl opacity-50 transition-all duration-500",
            isCritical && "animate-pulse-glow"
          )}
          style={{ backgroundColor: color.glow }}
        />
        
        <svg
          className="w-48 h-48 transform -rotate-90"
          viewBox="0 0 100 100"
        >
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-muted/30"
          />
          
          {/* Progress circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            stroke={color.stroke}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            className="transition-all duration-300 drop-shadow-lg"
            style={{
              filter: `drop-shadow(0 0 10px ${color.glow})`,
            }}
          />

          {/* Tick marks */}
          {[0, 20, 40, 60, 80, 100].map((tick) => {
            const angle = (tick / 100) * 360 - 90;
            const rad = (angle * Math.PI) / 180;
            const x1 = 50 + 38 * Math.cos(rad);
            const y1 = 50 + 38 * Math.sin(rad);
            const x2 = 50 + 42 * Math.cos(rad);
            const y2 = 50 + 42 * Math.sin(rad);
            return (
              <line
                key={tick}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke="currentColor"
                strokeWidth="1"
                className="text-muted-foreground/50"
              />
            );
          })}
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className={cn(
              "text-5xl font-bold font-mono transition-all duration-300",
              isCritical && "animate-fire-flicker"
            )}
            style={{ color: color.stroke }}
          >
            {displayScore}
          </span>
          <span className="text-sm text-muted-foreground font-medium">/ 100</span>
        </div>
      </div>

      {/* Category badge */}
      <div
        className={cn(
          "px-4 py-2 rounded-full text-sm font-bold uppercase tracking-wider transition-all duration-300",
          isCritical && "animate-pulse-glow"
        )}
        style={{
          backgroundColor: `${color.stroke}20`,
          color: color.stroke,
          border: `2px solid ${color.stroke}40`,
        }}
      >
        {category}
      </div>
    </div>
  );
}
