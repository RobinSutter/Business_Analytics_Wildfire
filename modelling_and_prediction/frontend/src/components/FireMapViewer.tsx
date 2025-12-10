import { useState, useEffect, useCallback } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Loader2, 
  Users, 
  MapPin, 
  Maximize2, 
  Minimize2,
  RefreshCw,
  AlertTriangle,
  X,
  Wind,
  Flame
} from 'lucide-react';
import { cn, formatDecimal, formatNumber } from '@/lib/utils';
import { generateFireMap, FireMapResponse } from '@/lib/api';

interface FireMapViewerProps {
  latitude: number;
  longitude: number;
  radiusKm: number;
  windSpeed: number;
  windDirection: number;
  riskCategory: string;
}

export function FireMapViewer({
  latitude,
  longitude,
  radiusKm,
  windSpeed,
  windDirection,
  riskCategory,
}: FireMapViewerProps) {
  const [mapData, setMapData] = useState<FireMapResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const fetchMap = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await generateFireMap({
        latitude,
        longitude,
        radius_km: radiusKm,
        wind_speed_mph: windSpeed,
        wind_direction_deg: windDirection,
      });
      setMapData(data);
    } catch (err) {
      console.error('Map generation failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate map');
    } finally {
      setLoading(false);
    }
  }, [latitude, longitude, radiusKm, windSpeed, windDirection]);

  // Generate map when props change
  useEffect(() => {
    fetchMap();
  }, [fetchMap]);

  const getRiskColor = () => {
    switch (riskCategory) {
      case 'Very Low': case 'Very Low Risk': return 'bg-green-500';
      case 'Low': case 'Low Risk': return 'bg-blue-500';
      case 'Moderate': case 'Moderate Risk': return 'bg-yellow-500';
      case 'High': case 'High Risk': return 'bg-orange-500';
      case 'Critical': case 'Critical Risk': return 'bg-red-500 animate-pulse';
      default: return 'bg-gray-500';
    }
  };

  // Loading state
  if (loading && !mapData) {
    return (
      <Card className="flex flex-col items-center justify-center h-96 bg-gradient-to-br from-background to-muted/30">
        <div className="relative">
          <Loader2 className="w-12 h-12 animate-spin text-primary" />
          <Flame className="w-6 h-6 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-orange-500 animate-pulse" />
        </div>
        <span className="mt-4 text-lg font-medium">Generating Fire Spread Map...</span>
        <span className="text-sm text-muted-foreground mt-1">
          Analyzing {formatDecimal(radiusKm)}km radius with wind at {formatDecimal(windSpeed)}mph
        </span>
      </Card>
    );
  }

  // Error state
  if (error && !mapData) {
    return (
      <Card className="flex flex-col items-center justify-center h-96 bg-destructive/5 border-destructive/20">
        <AlertTriangle className="w-12 h-12 text-destructive mb-4" />
        <span className="text-lg font-medium text-destructive">Map Generation Failed</span>
        <span className="text-sm text-muted-foreground mt-1 mb-4">{error}</span>
        <Button variant="outline" onClick={fetchMap}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </Card>
    );
  }

  return (
    <div className={cn(
      "relative transition-all duration-500",
      isFullscreen && "fixed inset-0 z-50 bg-background p-4"
    )}>
      {/* Map Container */}
      <div className={cn(
        "relative rounded-xl overflow-hidden border border-border/50 shadow-2xl",
        isFullscreen ? "h-[calc(100vh-180px)]" : "aspect-[16/10]"
      )}>
        {mapData && (
          <iframe
            src={`http://localhost:8000${mapData.map_url}`}
            className="w-full h-full border-0"
            title="Fire Spread Map"
            sandbox="allow-scripts allow-same-origin"
          />
        )}

        {/* Loading overlay for refresh */}
        {loading && mapData && (
          <div className="absolute inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
          </div>
        )}

        {/* Top Left Controls */}
        <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
          {/* Risk Badge */}
          <div className={cn(
            "px-3 py-2 rounded-lg shadow-lg text-white font-bold text-sm flex items-center gap-2",
            getRiskColor()
          )}>
            <AlertTriangle className="w-4 h-4" />
            {riskCategory}
          </div>

          {/* Wind Info */}
          <div className="px-3 py-2 rounded-lg bg-card/90 backdrop-blur-md shadow-lg border border-border/50 text-sm flex items-center gap-2">
            <Wind className="w-4 h-4 text-blue-500" />
            <span>{windSpeed} mph @ {windDirection}°</span>
          </div>
        </div>

        {/* Top Right Controls */}
        <div className="absolute top-4 right-4 z-10 flex gap-2">
          <Button
            variant="secondary"
            size="icon"
            onClick={fetchMap}
            disabled={loading}
            className="bg-card/90 backdrop-blur-md"
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          </Button>
          
          <Button
            variant="secondary"
            size="icon"
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="bg-card/90 backdrop-blur-md"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </Button>

          {isFullscreen && (
            <Button
              variant="destructive"
              size="icon"
              onClick={() => setIsFullscreen(false)}
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>

        {/* Bottom Left: Location Info */}
        <div className="absolute bottom-4 left-4 z-10 px-3 py-2 rounded-lg bg-card/90 backdrop-blur-md shadow-lg border border-border/50">
          <div className="flex items-center gap-2 text-sm">
            <MapPin className="w-4 h-4 text-primary" />
            <span className="font-mono">
              {latitude.toFixed(4)}°N, {Math.abs(longitude).toFixed(4)}°W
            </span>
          </div>
        </div>
      </div>

      {/* Population Impact Panel */}
      {mapData && (
        <Card className={cn(
          "mt-4 p-4",
          isFullscreen && "max-h-[140px] overflow-y-auto"
        )}>
          <h3 className="font-bold flex items-center gap-2 mb-3">
            <Users className="w-5 h-5 text-primary" />
            Population Impact Analysis
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Total Population */}
            <div className="bg-primary/10 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-primary">
                {formatNumber(mapData.total_population)}
              </div>
              <div className="text-sm text-muted-foreground">Affected Population</div>
            </div>

            {/* Radius */}
            <div className="bg-muted/50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold">
                {formatDecimal(mapData.radius_km)} km
              </div>
              <div className="text-sm text-muted-foreground">Fire Radius</div>
            </div>

            {/* Counties */}
            <div className="bg-muted/50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold">
                {mapData.affected_counties.length}
              </div>
              <div className="text-sm text-muted-foreground">Counties Affected</div>
            </div>
          </div>

          {/* Affected Counties List */}
          {mapData.affected_counties.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium mb-2 text-muted-foreground">
                Most Affected Counties
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {mapData.affected_counties.slice(0, 6).map((county, i) => (
                  <div 
                    key={i} 
                    className="flex justify-between items-center text-sm bg-muted/30 rounded px-3 py-2"
                  >
                    <span className="font-medium truncate">
                      {county.county}, {county.state}
                    </span>
                    <span className="text-primary font-bold ml-2">
                      {formatNumber(county.contributing_pop)}
                    </span>
                  </div>
                ))}
              </div>
              
              {mapData.affected_counties.length > 6 && (
                <div className="text-center mt-2 text-sm text-muted-foreground">
                  +{mapData.affected_counties.length - 6} more counties
                </div>
              )}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

