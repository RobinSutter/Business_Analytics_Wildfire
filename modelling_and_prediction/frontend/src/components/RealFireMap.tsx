import { useEffect, useRef, useState, useCallback } from 'react';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
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
  AlertTriangle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { acresToRadius } from '@/lib/api';
import { cn, formatNumber } from '@/lib/utils';

interface RealFireMapProps {
  latitude: number;
  longitude: number;
  predictedAcres: number;
  windSpeed: number;
  windDirection: number;
  riskCategory: string;
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
}

export function RealFireMap({
  latitude,
  longitude,
  predictedAcres,
  windSpeed,
  windDirection,
  riskCategory,
  isFullscreen = false,
  onToggleFullscreen,
}: RealFireMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapStyle, setMapStyle] = useState<'satellite' | 'terrain' | 'dark'>('satellite');
  const [mapLoaded, setMapLoaded] = useState(false);
  const [animationProgress, setAnimationProgress] = useState(0);

  // Calculate fire spread based on wind
  const getElongationFactor = useCallback(() => {
    if (windSpeed <= 5) return 1.2;
    if (windSpeed <= 15) return 1.8;
    if (windSpeed <= 25) return 2.5;
    return 3.5;
  }, [windSpeed]);

  const radiusMeters = acresToRadius(predictedAcres);
  const elongation = getElongationFactor();

  // Get style URL based on selection
  const getStyleUrl = (style: string) => {
    switch (style) {
      case 'satellite':
        return 'mapbox://styles/mapbox/satellite-streets-v12';
      case 'terrain':
        return 'mapbox://styles/mapbox/outdoors-v12';
      case 'dark':
        return 'mapbox://styles/mapbox/dark-v11';
      default:
        return 'mapbox://styles/mapbox/satellite-streets-v12';
    }
  };

  // Create ellipse coordinates for fire spread
  const createEllipseCoordinates = useCallback((
    centerLng: number,
    centerLat: number,
    majorAxisMeters: number,
    minorAxisMeters: number,
    rotationDegrees: number,
    numPoints: number = 64
  ) => {
    const coordinates: [number, number][] = [];
    const rotationRad = (rotationDegrees * Math.PI) / 180;

    for (let i = 0; i <= numPoints; i++) {
      const angle = (i / numPoints) * 2 * Math.PI;
      
      // Ellipse point before rotation
      const x = majorAxisMeters * Math.cos(angle);
      const y = minorAxisMeters * Math.sin(angle);
      
      // Rotate the point
      const rotatedX = x * Math.cos(rotationRad) - y * Math.sin(rotationRad);
      const rotatedY = x * Math.sin(rotationRad) + y * Math.cos(rotationRad);
      
      // Convert meters to degrees (approximate)
      const latOffset = rotatedY / 111320;
      const lngOffset = rotatedX / (111320 * Math.cos(centerLat * Math.PI / 180));
      
      coordinates.push([centerLng + lngOffset, centerLat + latOffset]);
    }

    return coordinates;
  }, []);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: getStyleUrl(mapStyle),
      center: [longitude, latitude],
      zoom: 10,
      pitch: 45,
      bearing: -17.6,
    });

    // Add navigation controls
    map.current.addControl(
      new mapboxgl.NavigationControl({
        visualizePitch: true,
      }),
      'top-right'
    );

    // Add scale control
    map.current.addControl(
      new mapboxgl.ScaleControl({
        maxWidth: 200,
        unit: 'imperial',
      }),
      'bottom-left'
    );

    map.current.on('load', () => {
      setMapLoaded(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Update map style
  useEffect(() => {
    if (!map.current) return;
    map.current.setStyle(getStyleUrl(mapStyle));
    
    // Re-add layers after style change
    map.current.once('style.load', () => {
      setMapLoaded(true);
      updateFireLayers();
    });
  }, [mapStyle]);

  // Update fire visualization layers
  const updateFireLayers = useCallback(() => {
    if (!map.current || !mapLoaded) return;

    const currentRadius = radiusMeters * (animationProgress / 100);
    const majorAxis = currentRadius * elongation;
    const minorAxis = currentRadius;

    // Wind direction points where fire spreads TO
    const rotationAngle = windDirection;

    // Create ellipse coordinates
    const ellipseCoords = createEllipseCoordinates(
      longitude,
      latitude,
      majorAxis,
      minorAxis,
      rotationAngle
    );

    // Create outer glow ellipse
    const outerGlowCoords = createEllipseCoordinates(
      longitude,
      latitude,
      majorAxis * 1.3,
      minorAxis * 1.3,
      rotationAngle
    );

    // Remove existing layers and sources
    ['fire-spread-glow', 'fire-spread-main', 'fire-spread-core'].forEach(id => {
      if (map.current?.getLayer(id)) map.current.removeLayer(id);
    });
    ['fire-spread-glow-source', 'fire-spread-main-source', 'fire-spread-core-source'].forEach(id => {
      if (map.current?.getSource(id)) map.current.removeSource(id);
    });

    if (currentRadius > 10) {
      // Add outer glow
      map.current.addSource('fire-spread-glow-source', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'Polygon',
            coordinates: [outerGlowCoords],
          },
        },
      });

      map.current.addLayer({
        id: 'fire-spread-glow',
        type: 'fill',
        source: 'fire-spread-glow-source',
        paint: {
          'fill-color': '#F39C12',
          'fill-opacity': 0.2,
        },
      });

      // Add main fire spread
      map.current.addSource('fire-spread-main-source', {
        type: 'geojson',
        data: {
          type: 'Feature',
          properties: {},
          geometry: {
            type: 'Polygon',
            coordinates: [ellipseCoords],
          },
        },
      });

      map.current.addLayer({
        id: 'fire-spread-main',
        type: 'fill',
        source: 'fire-spread-main-source',
        paint: {
          'fill-color': [
            'interpolate',
            ['linear'],
            ['zoom'],
            5, '#E74C3C',
            15, '#E67E22'
          ],
          'fill-opacity': 0.5,
        },
      });

      // Add fire outline
      map.current.addLayer({
        id: 'fire-spread-core',
        type: 'line',
        source: 'fire-spread-main-source',
        paint: {
          'line-color': '#E74C3C',
          'line-width': 3,
          'line-dasharray': [2, 2],
        },
      });
    }

    // Update or add fire origin marker
    const existingMarker = document.getElementById('fire-origin-marker');
    if (existingMarker) existingMarker.remove();

    const markerEl = document.createElement('div');
    markerEl.id = 'fire-origin-marker';
    markerEl.className = 'relative';
    markerEl.innerHTML = `
      <div class="absolute -translate-x-1/2 -translate-y-1/2">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-red-500 to-orange-500 flex items-center justify-center shadow-lg animate-pulse border-2 border-white">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>
          </svg>
        </div>
        <div class="absolute top-full left-1/2 -translate-x-1/2 mt-1 whitespace-nowrap bg-black/80 text-white text-xs px-2 py-1 rounded">
          Fire Origin
        </div>
      </div>
    `;

    new mapboxgl.Marker({ element: markerEl })
      .setLngLat([longitude, latitude])
      .addTo(map.current);

  }, [mapLoaded, latitude, longitude, radiusMeters, elongation, windDirection, animationProgress, createEllipseCoordinates]);

  // Animate fire spread
  useEffect(() => {
    if (!mapLoaded) return;

    let progress = 0;
    const animate = () => {
      progress += 2;
      if (progress > 100) progress = 100;
      setAnimationProgress(progress);
      
      if (progress < 100) {
        requestAnimationFrame(animate);
      }
    };

    animate();
  }, [mapLoaded, predictedAcres]);

  // Update fire layers when animation progresses
  useEffect(() => {
    updateFireLayers();
  }, [updateFireLayers, animationProgress]);

  // Fly to new location
  useEffect(() => {
    if (!map.current || !mapLoaded) return;

    map.current.flyTo({
      center: [longitude, latitude],
      zoom: 10,
      pitch: 45,
      duration: 2000,
    });
  }, [latitude, longitude, mapLoaded]);

  const getWindLabel = (direction: number): string => {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(direction / 45) % 8;
    return directions[index];
  };

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
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
        {/* Style Switcher */}
        <div className="flex gap-1 p-1 bg-card/90 backdrop-blur-md rounded-lg shadow-lg border border-border/50">
          {(['satellite', 'terrain', 'dark'] as const).map((style) => (
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

      {/* Legend Panel */}
      <div className="absolute bottom-4 left-4 z-10 bg-card/90 backdrop-blur-md rounded-xl p-4 shadow-xl border border-border/50 max-w-xs">
        <h4 className="font-semibold text-sm mb-3 flex items-center gap-2">
          <Flame className="w-4 h-4 text-primary" />
          Fire Spread Legend
        </h4>
        
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-gradient-to-br from-fire-red to-fire-orange border-2 border-white shadow" />
            <span>Fire Origin Point</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary/50 border border-primary" />
            <span>Predicted Fire Area ({formatNumber(predictedAcres)} acres)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-warning/30 border border-warning/50" />
            <span>Extended Risk Zone</span>
          </div>
          
          {windSpeed > 0 && (
            <div className="flex items-center gap-2 pt-2 border-t border-border/50">
              <Wind className="w-4 h-4 text-accent" />
              <span>Wind: {windSpeed} mph from {getWindLabel((windDirection + 180) % 360)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Info Panel */}
      <div className="absolute top-4 right-20 z-10 bg-card/90 backdrop-blur-md rounded-xl p-3 shadow-xl border border-border/50">
        <div className="text-xs space-y-1">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Navigation className="w-3 h-3" />
            <span className="font-mono">{latitude.toFixed(4)}°N, {Math.abs(longitude).toFixed(4)}°W</span>
          </div>
          <div className="flex items-center gap-2 font-bold text-foreground">
            <Flame className="w-3 h-3 text-primary" />
            <span>~{Math.round(radiusMeters / 1000 * 2)} km spread radius</span>
          </div>
        </div>
      </div>

      {/* Fullscreen Toggle */}
      <Button
        variant="glass"
        size="icon"
        className="absolute bottom-4 right-4 z-10"
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
          className="absolute top-4 right-4 z-10"
          onClick={onToggleFullscreen}
        >
          <X className="w-5 h-5" />
        </Button>
      )}
    </div>
  );
}
