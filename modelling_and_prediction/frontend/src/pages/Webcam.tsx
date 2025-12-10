import { useState, useEffect } from 'react';
import { Camera, Activity, Flame, Wind, RefreshCw, AlertTriangle } from 'lucide-react';
import { Header } from '@/components/Header';
import { HistoryPanel } from '@/components/HistoryPanel';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { getHistory } from '@/lib/storage';
import { HistoricalPrediction } from '@/types/prediction';
import { toast } from 'sonner';

interface StreamStats {
  detections: string[];
  fire: boolean;
  smoke: boolean;
  timestamp: number;
}

const Webcam = () => {
  const [stats, setStats] = useState<StreamStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [streamError, setStreamError] = useState(false);
  const [history, setHistory] = useState<HistoricalPrediction[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [videoKey, setVideoKey] = useState(0);

  useEffect(() => {
    setHistory(getHistory());
  }, []);

  useEffect(() => {
    // Fetch stats immediately
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:8001/stats');
        if (response.ok) {
          const data = await response.json();
          console.log('Stats received:', data);
          setStats(data);
          setIsLoading(false);
        } else {
          console.error('Stats fetch failed:', response.status);
        }
      } catch (error) {
        console.error('Stats fetch error:', error);
        setIsLoading(false);
      }
    };
    
    fetchStats();

    // Fetch stats every second for automatic refresh
    const interval = setInterval(fetchStats, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Show alerts for fire/smoke detection
    if (stats?.fire) {
      toast.error('🔥 Fire Detected!', {
        description: 'Immediate action required',
        duration: 3000,
      });
    } else if (stats?.smoke) {
      toast.warning('Smoke Detected!', {
        description: 'Monitoring situation',
        duration: 3000,
      });
    }
  }, [stats?.fire, stats?.smoke]);

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const handleSelectFromHistory = (item: HistoricalPrediction) => {
    setIsHistoryOpen(false);
  };

  return (
    <div className="min-h-screen bg-background">
      <Header 
        onHistoryClick={() => setIsHistoryOpen(true)} 
        historyCount={history.length}
      />

      <main className="container mx-auto px-4 py-8">
        {/* Hero Section */}
        <div className="text-center mb-8 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
            <Camera className="w-4 h-4" />
            Live Webcam Monitoring
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4">
            <span className="fire-gradient-text">Real-Time Fire Detection</span>
          </h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Monitor live video feed with AI-powered fire and smoke detection
          </p>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Video Feed */}
          <div className="lg:col-span-2">
            <Card className="overflow-hidden">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Camera className="w-5 h-5" />
                      Live Video Feed
                    </CardTitle>
                    <CardDescription>Real-time monitoring with AI detection</CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 text-green-500 text-sm font-medium">
                      <Activity className="w-3 h-3 animate-pulse" />
                      <span>Live</span>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <img
                  src="http://localhost:8001/video"
                  alt="Live video stream"
                  className="w-full h-auto"
                />
              </CardContent>
            </Card>
          </div>

          {/* Stats Panel */}
          <div className="space-y-6">
            {/* Detection Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Activity className="w-5 h-5" />
                  Detection Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <>
                    {/* Fire Status */}
                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${stats?.fire ? 'bg-red-500/20' : 'bg-muted'}`}>
                          <Flame className={`w-5 h-5 ${stats?.fire ? 'text-red-500 animate-fire-flicker' : 'text-muted-foreground'}`} />
                        </div>
                        <div>
                          <p className="font-medium">Fire</p>
                          <p className="text-xs text-muted-foreground">High priority alert</p>
                        </div>
                      </div>
                      <Badge variant={stats?.fire ? 'destructive' : 'outline'}>
                        {stats?.fire ? 'DETECTED' : 'Clear'}
                      </Badge>
                    </div>

                    {/* Smoke Status */}
                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${stats?.smoke ? 'bg-yellow-500/20' : 'bg-muted'}`}>
                          <Wind className={`w-5 h-5 ${stats?.smoke ? 'text-yellow-500' : 'text-muted-foreground'}`} />
                        </div>
                        <div>
                          <p className="font-medium">Smoke</p>
                          <p className="text-xs text-muted-foreground">Warning level alert</p>
                        </div>
                      </div>
                      <Badge variant={stats?.smoke ? 'default' : 'outline'} className={stats?.smoke ? 'bg-yellow-500 hover:bg-yellow-600' : ''}>
                        {stats?.smoke ? 'DETECTED' : 'Clear'}
                      </Badge>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Detection Details */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <RefreshCw className="w-5 h-5" />
                  Detection Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {isLoading ? (
                  <div className="flex items-center justify-center py-4">
                    <RefreshCw className="w-5 h-5 animate-spin text-muted-foreground" />
                  </div>
                ) : (
                  <>
                    <div className="space-y-2">
                      <p className="text-sm font-medium text-muted-foreground">Detected Objects</p>
                      {stats?.detections && stats.detections.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                          {stats.detections.map((detection, idx) => (
                            <Badge key={idx} variant="secondary" className="capitalize">
                              {detection}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-muted-foreground">No detections</p>
                      )}
                    </div>

                    <div className="pt-3 border-t">
                      <p className="text-sm font-medium text-muted-foreground mb-1">Last Update</p>
                      <p className="text-sm font-mono">
                        {stats?.timestamp ? formatTimestamp(stats.timestamp) : 'N/A'}
                      </p>
                    </div>

                    <div className="pt-3 border-t">
                      <p className="text-sm font-medium text-muted-foreground mb-1">Update Rate</p>
                      <p className="text-sm">Real-time (1 Hz)</p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>

            {/* Alert History */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <AlertTriangle className="w-5 h-5" />
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-muted-foreground">Video Stream</span>
                    <Badge variant={streamError ? 'destructive' : 'default'} className="bg-green-500">
                      {streamError ? 'Offline' : 'Online'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-muted-foreground">AI Detection</span>
                    <Badge variant={isLoading ? 'outline' : 'default'} className="bg-green-500">
                      {isLoading ? 'Loading' : 'Active'}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between py-2">
                    <span className="text-sm text-muted-foreground">Stats API</span>
                    <Badge variant={streamError ? 'destructive' : 'default'} className="bg-green-500">
                      {streamError ? 'Offline' : 'Online'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
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

export default Webcam;
