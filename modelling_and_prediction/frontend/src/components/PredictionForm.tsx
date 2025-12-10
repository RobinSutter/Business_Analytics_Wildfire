import { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { 
  CalendarIcon, 
  MapPin, 
  Thermometer, 
  Wind, 
  Compass, 
  Building2,
  Flame,
  Navigation,
  Loader2
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Calendar } from '@/components/ui/calendar';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { PredictionRequest, FIRE_CAUSES, US_STATES, SEASONS, STATE_COORDINATES } from '@/types/prediction';
import { getSeasonFromMonth, getDayOfYear } from '@/lib/api';

interface PredictionFormProps {
  onSubmit: (data: PredictionRequest) => void;
  isLoading: boolean;
  initialData?: PredictionRequest;
}

export function PredictionForm({ onSubmit, isLoading, initialData }: PredictionFormProps) {
  const [date, setDate] = useState<Date>(initialData ? new Date(2024, (initialData.month - 1), 1) : new Date());
  const [state, setState] = useState(initialData?.state || 'CA');
  const [latitude, setLatitude] = useState(initialData?.latitude || 36.7783);
  const [longitude, setLongitude] = useState(initialData?.longitude || -119.4179);
  const [meanTemp, setMeanTemp] = useState(initialData?.mean_temp || 25);
  const [maxTemp, setMaxTemp] = useState(initialData?.max_temp || 35);
  const [minTemp, setMinTemp] = useState(initialData?.min_temp || 15);
  const [discoveryTemp, setDiscoveryTemp] = useState(initialData?.discovery_temp || 30);
  const [cause, setCause] = useState(initialData?.cause || 'Lightning');
  const [season, setSeason] = useState(initialData?.season || 'Summer');
  const [numCities, setNumCities] = useState(initialData?.num_cities || 5);
  const [windSpeed, setWindSpeed] = useState(initialData?.wind_speed || 10);
  const [windDirection, setWindDirection] = useState(initialData?.wind_direction || 180);
  const [useCelsius, setUseCelsius] = useState(true);
  const [isLocating, setIsLocating] = useState(false);

  // Auto-update season when date changes
  useEffect(() => {
    const month = date.getMonth() + 1;
    setSeason(getSeasonFromMonth(month));
  }, [date]);

  // Update coordinates when state changes
  useEffect(() => {
    const coords = STATE_COORDINATES[state];
    if (coords) {
      setLatitude(coords.lat);
      setLongitude(coords.lon);
    }
  }, [state]);

  const handleGetLocation = () => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }

    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(Math.round(position.coords.latitude * 10000) / 10000);
        setLongitude(Math.round(position.coords.longitude * 10000) / 10000);
        setIsLocating(false);
      },
      (error) => {
        console.error('Error getting location:', error);
        setIsLocating(false);
        alert('Unable to get your location. Please enter coordinates manually.');
      }
    );
  };

  const toC = (f: number) => Math.round((f - 32) * 5/9);
  const toF = (c: number) => Math.round(c * 9/5 + 32);

  const displayTemp = (c: number) => useCelsius ? c : toF(c);
  const tempUnit = useCelsius ? '°C' : '°F';

  const getWindDirectionLabel = (deg: number) => {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
    const index = Math.round(deg / 45) % 8;
    return directions[index];
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const data: PredictionRequest = {
      mean_temp: meanTemp,
      max_temp: maxTemp,
      min_temp: minTemp,
      discovery_temp: discoveryTemp,
      latitude,
      longitude,
      state,
      cause,
      month: date.getMonth() + 1,
      day_of_year: getDayOfYear(date),
      season,
      num_cities: numCities,
      wind_speed: windSpeed,
      wind_direction: windDirection,
    };

    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Date & Time Section */}
      <div className="glass-card rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <CalendarIcon className="w-5 h-5 text-primary" />
          <h3>Discovery Date & Time</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Date</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className={cn(
                    "w-full justify-start text-left font-normal",
                    !date && "text-muted-foreground"
                  )}
                >
                  <CalendarIcon className="mr-2 h-4 w-4" />
                  {date ? format(date, "PPP") : <span>Pick a date</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-auto p-0 pointer-events-auto" align="start">
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={(d) => d && setDate(d)}
                  initialFocus
                  className="pointer-events-auto"
                />
              </PopoverContent>
            </Popover>
          </div>

          <div className="space-y-2">
            <Label>Season</Label>
            <Select value={season} onValueChange={setSeason}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SEASONS.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </div>

      {/* Location Section */}
      <div className="glass-card rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <MapPin className="w-5 h-5 text-primary" />
            <h3>Location</h3>
          </div>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={handleGetLocation}
            disabled={isLocating}
          >
            {isLocating ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Navigation className="w-4 h-4 mr-2" />
            )}
            Use Current Location
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="space-y-2">
            <Label>State</Label>
            <Select value={state} onValueChange={setState}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="max-h-60">
                {US_STATES.map((s) => (
                  <SelectItem key={s.value} value={s.value}>
                    {s.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label>Latitude</Label>
            <Input
              type="number"
              step="0.0001"
              value={latitude}
              onChange={(e) => setLatitude(parseFloat(e.target.value))}
              className="font-mono"
            />
          </div>

          <div className="space-y-2">
            <Label>Longitude</Label>
            <Input
              type="number"
              step="0.0001"
              value={longitude}
              onChange={(e) => setLongitude(parseFloat(e.target.value))}
              className="font-mono"
            />
          </div>
        </div>
      </div>

      {/* Temperature Section */}
      <div className="glass-card rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <Thermometer className="w-5 h-5 text-primary" />
            <h3>Temperature Conditions</h3>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setUseCelsius(!useCelsius)}
          >
            {useCelsius ? '°C' : '°F'}
          </Button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Mean Temperature</Label>
                <span className="text-sm font-mono text-muted-foreground">
                  {displayTemp(meanTemp)}{tempUnit}
                </span>
              </div>
              <Slider
                value={[meanTemp]}
                onValueChange={([v]) => setMeanTemp(v)}
                min={-20}
                max={50}
                step={1}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Max Temperature</Label>
                <span className="text-sm font-mono text-muted-foreground">
                  {displayTemp(maxTemp)}{tempUnit}
                </span>
              </div>
              <Slider
                value={[maxTemp]}
                onValueChange={([v]) => setMaxTemp(v)}
                min={-10}
                max={60}
                step={1}
                className="w-full"
              />
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Min Temperature</Label>
                <span className="text-sm font-mono text-muted-foreground">
                  {displayTemp(minTemp)}{tempUnit}
                </span>
              </div>
              <Slider
                value={[minTemp]}
                onValueChange={([v]) => setMinTemp(v)}
                min={-30}
                max={40}
                step={1}
                className="w-full"
              />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Discovery Temperature</Label>
                <span className="text-sm font-mono text-muted-foreground">
                  {displayTemp(discoveryTemp)}{tempUnit}
                </span>
              </div>
              <Slider
                value={[discoveryTemp]}
                onValueChange={([v]) => setDiscoveryTemp(v)}
                min={-20}
                max={55}
                step={1}
                className="w-full"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Wind Section */}
      <div className="glass-card rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Wind className="w-5 h-5 text-primary" />
          <h3>Wind Conditions</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Wind Speed</Label>
              <span className="text-sm font-mono text-muted-foreground">
                {windSpeed} mph
              </span>
            </div>
            <Slider
              value={[windSpeed]}
              onValueChange={([v]) => setWindSpeed(v)}
              min={0}
              max={60}
              step={1}
              className="w-full"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label>Wind Direction</Label>
              <span className="text-sm font-mono text-muted-foreground flex items-center gap-1">
                <Compass className="w-3 h-3" />
                {windDirection}° ({getWindDirectionLabel(windDirection)})
              </span>
            </div>
            <Slider
              value={[windDirection]}
              onValueChange={([v]) => setWindDirection(v)}
              min={0}
              max={359}
              step={1}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* Environmental Context */}
      <div className="glass-card rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-lg font-semibold text-foreground">
          <Flame className="w-5 h-5 text-primary" />
          <h3>Fire Context</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Fire Cause</Label>
            <Select value={cause} onValueChange={setCause}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {FIRE_CAUSES.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    <span className="flex items-center gap-2">
                      <span>{c.icon}</span>
                      <span>{c.label}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <Label className="flex items-center gap-2">
                <Building2 className="w-4 h-4" />
                Nearby Cities/Towns
              </Label>
              <span className="text-sm font-mono text-muted-foreground">
                {numCities}
              </span>
            </div>
            <Slider
              value={[numCities]}
              onValueChange={([v]) => setNumCities(v)}
              min={0}
              max={50}
              step={1}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* Submit Button */}
      <Button
        type="submit"
        variant="fire"
        size="xl"
        className="w-full"
        disabled={isLoading}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyzing Fire Risk...
          </>
        ) : (
          <>
            <Flame className="w-5 h-5" />
            Predict Fire Size
          </>
        )}
      </Button>
    </form>
  );
}
