import { useEffect, useRef, useState, useCallback } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Map, 
  Layers, 
  Wind, 
  ZoomIn, 
  ZoomOut, 
  Maximize2,
  Minimize2,
  X,
  Navigation,
  Flame,
  AlertTriangle,
  Users
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { acresToRadius } from '@/lib/api';
import { cn, formatNumber, formatDecimal } from '@/lib/utils';

interface PopulationFireMapProps {
  latitude: number;
  longitude: number;
  predictedAcres: number;
  windSpeed: number;
  windDirection: number;
  riskCategory: string;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

export function PopulationFireMap({
  latitude,
  longitude,
  predictedAcres,
  windSpeed,
  windDirection,
  riskCategory,
  isFullscreen = false,
  onToggleFullscreen,
}: PopulationFireMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const [mapStyle, setMapStyle] = useState<'satellite' | 'terrain' | 'light'>('light');
  const [mapLoaded, setMapLoaded] = useState(false);
  const [estimatedPopulation, setEstimatedPopulation] = useState(0);

  const radiusMeters = acresToRadius(predictedAcres);
  const radiusKm = radiusMeters / 1000;

  // Tile layer URLs
  const getTileUrl = (style: string) => {
    switch (style) {
      case 'satellite':
        return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
      case 'terrain':
        return 'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png';
      case 'light':
        return 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
      default:
        return 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
    }
  };

  // Estimate population impact (simplified - in real app, fetch from backend)
  const estimatePopulation = useCallback((radiusKm: number) => {
    // Rough population density estimates (people per sq km)
    // In real implementation, this would come from backend with actual county data
    const avgDensity = 100; // Default rural
    const area = Math.PI * radiusKm * radiusKm;
    const estimated = Math.round(area * avgDensity);
    setEstimatedPopulation(estimated);
  }, []);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = L.map(mapContainer.current, {
      center: [latitude, longitude],
      zoom: 10,
      zoomControl: false, // We'll add custom controls
    });

    // Add tile layer
    L.tileLayer(getTileUrl(mapStyle), {
      attribution: mapStyle === 'satellite' 
        ? '&copy; Esri' 
        : mapStyle === 'terrain'
        ? '&copy; OpenTopoMap'
        : '&copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 18,
    }).addTo(map.current);

    // Add zoom controls in top right
    L.control.zoom({ position: 'topright' }).addTo(map.current);

    // Add scale control
    L.control.scale({ imperial: true, metric: true }).addTo(map.current);

    setMapLoaded(true);

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Update tile layer when style changes
  useEffect(() => {
    if (!map.current) return;
    
    map.current.eachLayer((layer) => {
      if (layer instanceof L.TileLayer) {
        map.current?.removeLayer(layer);
      }
    });

    L.tileLayer(getTileUrl(mapStyle), {
      attribution: mapStyle === 'satellite' 
        ? '&copy; Esri' 
        : mapStyle === 'terrain'
        ? '&copy; OpenTopoMap'
        : '&copy; <a href="https://carto.com/attributions">CARTO</a>',
      maxZoom: 18,
    }).addTo(map.current);
  }, [mapStyle]);

  // Update fire visualization
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    // Clear existing layers except tile layer
    map.current.eachLayer((layer) => {
      if (!(layer instanceof L.TileLayer)) {
        map.current?.removeLayer(layer);
      }
    });

    // Add fire impact circle
    const fireCircle = L.circle([latitude, longitude], {
      radius: radiusMeters,
      color: '#E74C3C',
      fillColor: '#E74C3C',
      fillOpacity: 0.3,
      weight: 3,
      dashArray: '10, 5',
    }).addTo(map.current);

    fireCircle.bindPopup(`
      <div class="font-sans">
        <h3 class="font-bold text-sm mb-1">Fire Impact Zone</h3>
        <p class="text-xs">Radius: ${formatDecimal(radiusKm)} km</p>
        <p class="text-xs">Area: ${formatDecimal(Math.PI * radiusKm * radiusKm)} km²</p>
        <p class="text-xs">Est. Population: ${formatNumber(estimatedPopulation)}</p>
      </div>
    `);

    // Add warning zone (1.5x radius)
    L.circle([latitude, longitude], {
      radius: radiusMeters * 1.5,
      color: '#F39C12',
      fillColor: '#F39C12',
      fillOpacity: 0.1,
      weight: 2,
      dashArray: '5, 10',
    }).addTo(map.current);

    // Add wind direction indicator
    if (windSpeed > 0) {
      const windEndLat = latitude + (radiusKm / 111) * Math.cos((windDirection * Math.PI) / 180);
      const windEndLng = longitude + (radiusKm / (111 * Math.cos((latitude * Math.PI) / 180))) * Math.sin((windDirection * Math.PI) / 180);

      L.polyline(
        [[latitude, longitude], [windEndLat, windEndLng]],
        {
          color: '#3498DB',
          weight: 3,
          dashArray: '10, 5',
        }
      ).addTo(map.current).bindPopup(`
        <div class="font-sans">
          <h3 class="font-bold text-sm mb-1">Wind Direction</h3>
          <p class="text-xs">Speed: ${windSpeed} mph</p>
          <p class="text-xs">Direction: ${windDirection}°</p>
        </div>
      `);
    }

    // Add fire origin marker
    const fireIcon = L.divIcon({
      className: 'custom-fire-icon',
      html: `
        <div class="relative">
          <div class="w-10 h-10 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg animate-pulse border-2 border-white">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>
            </svg>
          </div>
        </div>
      `,
      iconSize: [40, 40],
      iconAnchor: [20, 20],
    });

    L.marker([latitude, longitude], { icon: fireIcon })
      .addTo(map.current)
      .bindPopup(`
        <div class="font-sans">
          <h3 class="font-bold text-sm mb-1">Fire Origin</h3>
          <p class="text-xs">${formatDecimal(latitude, 4)}°N, ${formatDecimal(Math.abs(longitude), 4)}°W</p>
          <p class="text-xs font-bold text-red-600">${formatNumber(predictedAcres)} acres</p>
        </div>
      `);

    // Fit map to show entire fire zone
    map.current.fitBounds(fireCircle.getBounds(), { padding: [50, 50] });

    // Estimate population
    estimatePopulation(radiusKm);
  }, [mapLoaded, latitude, longitude, radiusMeters, radiusKm, windSpeed, windDirection, predictedAcres, estimatePopulation, estimatedPopulation]);

  // Fly to new location
  useEffect(() => {
    if (!map.current || !mapLoaded) return;
    map.current.flyTo([latitude, longitude], 10, { duration: 2 });
  }, [latitude, longitude, mapLoaded]);

  const getRiskColor = () => {
    switch (riskCategory) {
      case 'Very Low': return 'bg-success';
      case 'Low': return 'bg-accent';
      case 'Moderate': return 'bg-warning';
      case 'High': return 'bg-destructive';
      case 'Critical': return 'bg-primary animate-pulse';
      default: return 'bg-muted';
    }
  };

  return (
    <div className={cn(
      "relative rounded-xl overflow-hidden border border-border/50 shadow-2xl transition-all duration-500",
      isFullscreen 
        ? "fixed inset-0 z-50 rounded-none" 
        : "aspect-[16/10]"
    )}>
      {/* Map Container */}
      <div ref={mapContainer} className="absolute inset-0" />

      {/* Top Controls */}
      <div className="absolute top-4 left-4 z-[1000] flex flex-col gap-2">
        {/* Style Switcher */}
        <div className="flex gap-1 p-1 bg-card/90 backdrop-blur-md rounded-lg shadow-lg border border-border/50">
          {(['light', 'terrain', 'satellite'] as const).map((style) => (
            <Button
              key={style}
              variant={mapStyle === style ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setMapStyle(style)}
              className="capitalize text-xs"
            >
              {style}
            </Button>
          ))}
        </div>

        {/* Risk Badge */}
        <div className={cn(
          "px-3 py-2 rounded-lg shadow-lg text-white font-bold text-sm flex items-center gap-2",
          getRiskColor()
        )}>
          <AlertTriangle className="w-4 h-4" />
          {riskCategory}
        </div>
      </div>

      {/* Population Impact Panel */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-card/90 backdrop-blur-md rounded-xl p-4 shadow-xl border border-border/50 max-w-xs">
        <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
          <Users className="w-4 h-4 text-primary" />
          Population Impact
        </h4>
        
        <div className="space-y-2 text-xs">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Affected Radius:</span>
            <span className="font-bold">{formatDecimal(radiusKm)} km</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Impact Area:</span>
            <span className="font-bold">{formatDecimal(Math.PI * radiusKm * radiusKm)} km²</span>
          </div>
          <div className="flex justify-between border-t border-border/50 pt-2">
            <span className="text-muted-foreground">Est. Population:</span>
            <span className="font-bold text-primary">{formatNumber(estimatedPopulation)}</span>
          </div>
          
          {windSpeed > 0 && (
            <div className="flex items-center gap-2 pt-2 border-t border-border/50">
              <Wind className="w-4 h-4 text-accent" />
              <span>Wind: {formatDecimal(windSpeed)} mph @ {windDirection}°</span>
            </div>
          )}
        </div>
      </div>

      {/* Info Panel */}
      <div className="absolute top-4 right-20 z-[1000] bg-card/90 backdrop-blur-md rounded-xl p-3 shadow-xl border border-border/50">
        <div className="text-xs space-y-1">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Navigation className="w-3 h-3" />
            <span className="font-mono">{formatDecimal(latitude, 4)}°N, {formatDecimal(Math.abs(longitude), 4)}°W</span>
          </div>
          <div className="flex items-center gap-2 font-bold text-foreground">
            <Flame className="w-3 h-3 text-primary" />
            <span>{formatNumber(predictedAcres)} acres</span>
          </div>
        </div>
      </div>

      {/* Fullscreen Toggle */}
      <Button
        variant="glass"
        size="icon"
        className="absolute bottom-4 right-4 z-[1000]"
        onClick={onToggleFullscreen}
      >
        {isFullscreen ? (
          <Minimize2 className="w-5 h-5" />
        ) : (
          <Maximize2 className="w-5 h-5" />
        )}
      </Button>

      {/* Close button in fullscreen */}
      {isFullscreen && (
        <Button
          variant="destructive"
          size="icon"
          className="absolute top-4 right-4 z-[1000]"
          onClick={onToggleFullscreen}
        >
          <X className="w-5 h-5" />
        </Button>
      )}
    </div>
  );
}
