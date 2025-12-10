import { useState, useEffect } from 'react';
import { Flame, AlertTriangle, Info } from 'lucide-react';
import { Header } from '@/components/Header';
import { PredictionForm } from '@/components/PredictionForm';
import { PredictionResults } from '@/components/PredictionResults';
import { HistoryPanel } from '@/components/HistoryPanel';
import { Button } from '@/components/ui/button';
import { predictFireSize, healthCheck } from '@/lib/api';
import { savePrediction, getHistory, generateId } from '@/lib/storage';
import { PredictionRequest, PredictionResponse, HistoricalPrediction } from '@/types/prediction';
import { toast } from 'sonner';

const Index = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [lastInputs, setLastInputs] = useState<PredictionRequest | null>(null);
  const [history, setHistory] = useState<HistoricalPrediction[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [apiStatus, setApiStatus] = useState<'online' | 'offline' | 'checking'>('checking');

  useEffect(() => {
    setHistory(getHistory());
    checkApiStatus();
  }, []);

  const checkApiStatus = async () => {
    try {
      const status = await healthCheck();
      setApiStatus(status.status === 'ok' ? 'online' : 'offline');
    } catch {
      setApiStatus('offline');
    }
  };

  const handleSubmit = async (data: PredictionRequest) => {
    setIsLoading(true);
    setLastInputs(data);

    try {
      const result = await predictFireSize(data);
      setPrediction(result);

      // Save to history
      const historyEntry: HistoricalPrediction = {
        id: generateId(),
        timestamp: new Date().toISOString(),
        location: {
          lat: data.latitude,
          lon: data.longitude,
          state: data.state,
        },
        inputs: data,
        prediction: result,
      };
      savePrediction(historyEntry);
      setHistory(getHistory());

      toast.success('Prediction generated successfully!', {
        description: `Risk Level: ${result.risk_category}`,
      });
    } catch (error) {
      toast.error('Failed to generate prediction', {
        description: 'Please check your inputs and try again.',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectFromHistory = (item: HistoricalPrediction) => {
    setPrediction(item.prediction);
    setLastInputs(item.inputs);
    setIsHistoryOpen(false);
    toast.success('Historical prediction loaded', {
      description: 'You can modify the inputs and re-run the prediction',
    });
  };

  return (
    <div className="min-h-screen bg-background">
      <Header 
        onHistoryClick={() => setIsHistoryOpen(true)} 
        historyCount={history.length}
      />

      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
            <Flame className="w-4 h-4" />
            AI-Powered Fire Risk Analysis
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="fire-gradient-text">Predict Wildfire Size</span>
            <br />
            <span className="text-foreground">Before It Spreads</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Make data-driven decisions with advanced machine learning predictions. 
            Input environmental conditions and get instant fire size estimates and response recommendations.
          </p>
        </div>

        {/* API Status Banner */}
        {apiStatus === 'offline' && (
          <div className="mb-8 p-4 rounded-xl bg-warning/10 border border-warning/30 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-warning" />
            <div className="flex-1">
              <p className="font-medium text-warning">Demo Mode Active</p>
              <p className="text-sm text-muted-foreground">
                Backend API is not connected. Using simulated predictions for demonstration.
              </p>
            </div>
          </div>
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form Section */}
          <div className="space-y-6">
            <div className="flex items-center gap-2 text-xl font-semibold">
              <div className="p-2 rounded-lg bg-primary/10">
                <Info className="w-5 h-5 text-primary" />
              </div>
              <h2>Fire Conditions Input</h2>
            </div>
            <PredictionForm 
              onSubmit={handleSubmit} 
              isLoading={isLoading}
              initialData={lastInputs || undefined}
            />
          </div>

          {/* Results Section */}
          <div className="space-y-6">
            {prediction && lastInputs ? (
              <>
                <div className="flex items-center gap-2 text-xl font-semibold">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Flame className="w-5 h-5 text-primary" />
                  </div>
                  <h2>Prediction Results</h2>
                </div>
                <PredictionResults prediction={prediction} inputs={lastInputs} />
              </>
            ) : (
              <div className="h-full flex items-center justify-center">
                <div className="text-center p-12 glass-card rounded-xl max-w-md">
                  <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-fire-red/20 to-fire-amber/20 flex items-center justify-center">
                    <Flame className="w-10 h-10 text-primary animate-fire-flicker" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Ready to Predict</h3>
                  <p className="text-muted-foreground mb-6">
                    Fill in the fire conditions on the left to generate a prediction. 
                    Results will appear here with risk assessment and response recommendations.
                  </p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {['Risk Score', 'Fire Size', 'Response Plan', 'Fire Map'].map((feature) => (
                      <span 
                        key={feature}
                        className="px-3 py-1 rounded-full bg-muted text-muted-foreground text-sm"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* History Panel */}
      <HistoryPanel
        isOpen={isHistoryOpen}
        onClose={() => setIsHistoryOpen(false)}
        history={history}
        onRefresh={() => setHistory(getHistory())}
        onSelectPrediction={handleSelectFromHistory}
      />
    </div>
  );
};

export default Index;
