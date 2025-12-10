import { useState } from 'react';
import { format } from 'date-fns';
import { 
  X, 
  Trash2, 
  MapPin, 
  Flame,
  Clock,
  ChevronRight,
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn, formatNumber, formatDecimal } from '@/lib/utils';
import { HistoricalPrediction, RiskCategory } from '@/types/prediction';
import { deletePrediction, clearHistory } from '@/lib/storage';
import { toast } from 'sonner';

interface HistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  history: HistoricalPrediction[];
  onRefresh: () => void;
  onSelectPrediction: (prediction: HistoricalPrediction) => void;
}

export function HistoryPanel({ 
  isOpen, 
  onClose, 
  history, 
  onRefresh,
  onSelectPrediction 
}: HistoryPanelProps) {
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  const handleDelete = (id: string) => {
    deletePrediction(id);
    onRefresh();
    setDeleteConfirm(null);
    toast.success('Prediction deleted');
  };

  const handleClearAll = () => {
    clearHistory();
    onRefresh();
    toast.success('History cleared');
  };

  const getRiskColor = (category: string) => {
    switch (category) {
      case 'Very Low': return 'bg-success/20 text-success border-success/30';
      case 'Low': return 'bg-accent/20 text-accent border-accent/30';
      case 'Moderate': return 'bg-warning/20 text-warning border-warning/30';
      case 'High': return 'bg-destructive/20 text-destructive border-destructive/30';
      case 'Critical': return 'bg-primary/20 text-primary border-primary/30';
      default: return 'bg-muted/20 text-muted-foreground';
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-full max-w-md bg-card border-l border-border shadow-2xl z-50 animate-slide-in-right">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-bold">Prediction History</h2>
            <span className="px-2 py-0.5 text-xs bg-muted rounded-full">
              {history.length}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleClearAll}
                className="text-destructive hover:text-destructive"
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Clear All
              </Button>
            )}
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="w-5 h-5" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <ScrollArea className="h-[calc(100vh-65px)]">
          {history.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center p-6">
              <div className="w-16 h-16 rounded-full bg-muted/50 flex items-center justify-center mb-4">
                <Clock className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold mb-2">No Predictions Yet</h3>
              <p className="text-sm text-muted-foreground">
                Your prediction history will appear here after you make your first prediction.
              </p>
            </div>
          ) : (
            <div className="p-4 space-y-3">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="glass-card rounded-xl p-4 space-y-3 cursor-pointer hover:scale-[1.02] transition-all duration-200"
                  onClick={() => onSelectPrediction(item)}
                >
                  {/* Header */}
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="w-4 h-4" />
                      {format(new Date(item.timestamp), 'MMM d, yyyy h:mm a')}
                    </div>
                    <div className="flex items-center gap-1">
                      {deleteConfirm === item.id ? (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => { e.stopPropagation(); setDeleteConfirm(null); }}
                          >
                            Cancel
                          </Button>
                          <Button
                            variant="destructive"
                            size="sm"
                            onClick={(e) => { e.stopPropagation(); handleDelete(item.id); }}
                          >
                            Delete
                          </Button>
                        </>
                      ) : (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-destructive"
                          onClick={(e) => { e.stopPropagation(); setDeleteConfirm(item.id); }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Location */}
                  <div className="flex items-center gap-2 text-sm">
                    <MapPin className="w-4 h-4 text-primary" />
                    <span className="font-medium">{item.location.state}</span>
                    <span className="text-muted-foreground font-mono text-xs">
                      {formatDecimal(item.location.lat)}°, {formatDecimal(item.location.lon)}°
                    </span>
                  </div>

                  {/* Results */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <Flame className="w-4 h-4 text-fire-orange" />
                        <span className="font-mono font-bold">
                          {formatNumber(item.prediction.predicted_acres)} ac
                        </span>
                      </div>
                      <div className={cn(
                        "px-2 py-1 rounded-full text-xs font-semibold border",
                        getRiskColor(item.prediction.risk_category)
                      )}>
                        {item.prediction.risk_category}
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </div>
    </>
  );
}
