import { useState } from 'react';
import { 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  Truck, 
  Phone, 
  Copy, 
  Download,
  ChevronDown,
  ChevronUp,
  Siren
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { cn, formatNumber } from '@/lib/utils';
import { PredictionResponse, RiskCategory } from '@/types/prediction';
import { toast } from 'sonner';

interface RecommendationsPanelProps {
  prediction: PredictionResponse;
}

export function RecommendationsPanel({ prediction }: RecommendationsPanelProps) {
  const [checkedActions, setCheckedActions] = useState<Set<number>>(new Set());
  const [isExpanded, setIsExpanded] = useState(true);

  const toggleAction = (index: number) => {
    const newSet = new Set(checkedActions);
    if (newSet.has(index)) {
      newSet.delete(index);
    } else {
      newSet.add(index);
    }
    setCheckedActions(newSet);
  };

  const copyToClipboard = () => {
    const text = `
FSP Fire Size Predictor - Response Plan
========================================
Response Level: ${prediction.response_level}
Risk Category: ${prediction.risk_category}
Predicted Size: ${formatNumber(prediction.predicted_acres)} acres

Resources Required:
${prediction.resources}

Action Checklist:
${prediction.actions.map((a, i) => `${i + 1}. ${a}`).join('\n')}

Estimated Duration: ${prediction.estimated_duration}
    `.trim();
    
    navigator.clipboard.writeText(text);
    toast.success('Response plan copied to clipboard');
  };

  const isCritical = prediction.risk_category === 'Critical Risk' || prediction.risk_category === 'High Risk';

  return (
    <div className={cn(
      "glass-card rounded-xl overflow-hidden transition-all duration-300",
      isCritical && "ring-2 ring-primary/50"
    )}>
      {/* Header */}
      <div 
        className={cn(
          "p-4 flex items-center justify-between cursor-pointer transition-colors",
          isCritical ? "bg-primary/10" : "bg-muted/30"
        )}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg",
            isCritical ? "bg-primary/20" : "bg-accent/20"
          )}>
            <Siren className={cn(
              "w-5 h-5",
              isCritical ? "text-primary animate-pulse" : "text-accent"
            )} />
          </div>
          <div>
            <h3 className="font-bold text-lg">{prediction.response_level}</h3>
            <p className="text-sm text-muted-foreground">Response Recommendations</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); copyToClipboard(); }}>
            <Copy className="w-4 h-4 mr-1" />
            Copy
          </Button>
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-muted-foreground" />
          ) : (
            <ChevronDown className="w-5 h-5 text-muted-foreground" />
          )}
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="p-6 space-y-6 animate-fade-in">
          {/* Resources */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <Truck className="w-4 h-4 text-primary" />
              <span>Resource Deployment</span>
            </div>
            <div className="p-4 rounded-lg bg-muted/50 border border-border/50">
              <p className="text-foreground font-medium">{prediction.resources}</p>
            </div>
          </div>

          {/* Action Checklist */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <CheckCircle2 className="w-4 h-4 text-success" />
                <span>Action Checklist</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {checkedActions.size}/{prediction.actions.length} completed
              </span>
            </div>
            
            <div className="space-y-2">
              {prediction.actions.map((action, index) => (
                <div
                  key={index}
                  className={cn(
                    "flex items-start gap-3 p-3 rounded-lg transition-all duration-200",
                    checkedActions.has(index)
                      ? "bg-success/10 border border-success/30"
                      : "bg-muted/30 border border-transparent hover:bg-muted/50"
                  )}
                >
                  <Checkbox
                    id={`action-${index}`}
                    checked={checkedActions.has(index)}
                    onCheckedChange={() => toggleAction(index)}
                    className="mt-0.5"
                  />
                  <label
                    htmlFor={`action-${index}`}
                    className={cn(
                      "text-sm cursor-pointer flex-1 transition-all",
                      checkedActions.has(index) && "line-through text-muted-foreground"
                    )}
                  >
                    {action}
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Duration */}
          <div className="flex items-center gap-4 p-4 rounded-lg bg-muted/30 border border-border/50">
            <Clock className="w-6 h-6 text-accent" />
            <div>
              <p className="text-xs text-muted-foreground">Estimated Duration</p>
              <p className="text-lg font-bold font-mono">{prediction.estimated_duration}</p>
            </div>
          </div>

          {/* Emergency Contacts */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
              <Phone className="w-4 h-4 text-warning" />
              <span>Emergency Contacts</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button variant="outline" size="sm" className="justify-start">
                <Phone className="w-4 h-4 mr-2" />
                911 Dispatch
              </Button>
              <Button variant="outline" size="sm" className="justify-start">
                <Phone className="w-4 h-4 mr-2" />
                Fire HQ
              </Button>
              <Button variant="outline" size="sm" className="justify-start">
                <Phone className="w-4 h-4 mr-2" />
                State EOC
              </Button>
              <Button variant="outline" size="sm" className="justify-start">
                <Phone className="w-4 h-4 mr-2" />
                NWS Weather
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
