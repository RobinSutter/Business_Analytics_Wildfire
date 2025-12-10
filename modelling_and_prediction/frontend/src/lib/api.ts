import { PredictionRequest, PredictionResponse, RiskCategory } from '@/types/prediction';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Fire Map Types
export interface FireMapRequest {
  latitude: number;
  longitude: number;
  radius_km: number;
  wind_speed_mph: number;
  wind_direction_deg: number;
}

export interface AffectedCounty {
  county: string;
  state: string;
  population: number;
  affected_share: number;
  contributing_pop: number;
}

export interface FireMapResponse {
  map_url: string;
  total_population: number;
  affected_counties: AffectedCounty[];
  radius_km: number;
  center_lat: number;
  center_lon: number;
}

export async function predictFireSize(data: PredictionRequest): Promise<PredictionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.statusText}`);
    }
    
    return response.json();
  } catch (error) {
    // If API is unavailable, generate mock prediction for demo
    console.warn('API unavailable, using mock prediction:', error);
    return generateMockPrediction(data);
  }
}

export async function healthCheck(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.json();
  } catch {
    return { status: 'offline' };
  }
}

// Mock prediction for demo purposes when API is unavailable
function generateMockPrediction(data: PredictionRequest): PredictionResponse {
  // Calculate a risk score based on inputs
  let riskScore = 50;
  
  // Temperature factors
  const tempRange = data.max_temp - data.min_temp;
  riskScore += Math.min(tempRange * 0.5, 15);
  riskScore += Math.max(0, (data.max_temp - 30) * 2);
  
  // Wind factor
  if (data.wind_speed) {
    riskScore += Math.min(data.wind_speed * 0.8, 20);
  }
  
  // Season factor
  if (data.season === 'Summer') riskScore += 10;
  if (data.season === 'Fall') riskScore += 5;
  
  // Cause factor
  if (data.cause === 'Arson') riskScore += 15;
  if (data.cause === 'Lightning') riskScore += 10;
  
  // Clamp score
  riskScore = Math.max(0, Math.min(100, riskScore));
  
  // Calculate predicted acres based on risk score
  let predictedAcres: number;
  if (riskScore < 20) predictedAcres = Math.random() * 10;
  else if (riskScore < 40) predictedAcres = 10 + Math.random() * 90;
  else if (riskScore < 60) predictedAcres = 100 + Math.random() * 900;
  else if (riskScore < 80) predictedAcres = 1000 + Math.random() * 9000;
  else predictedAcres = 10000 + Math.random() * 40000;
  
  const { category, color, sizeClass, responseLevel, resources, actions, duration } = getRiskDetails(riskScore);
  
  return {
    predicted_acres: Math.round(predictedAcres * 10) / 10,
    predicted_hectares: Math.round(predictedAcres * 0.404686 * 10) / 10,
    risk_score: Math.round(riskScore),
    risk_category: category,
    risk_color: color,
    fire_size_class: sizeClass,
    response_level: responseLevel,
    resources: resources,
    actions: actions,
    estimated_duration: duration,
  };
}

function getRiskDetails(score: number): {
  category: RiskCategory;
  color: string;
  sizeClass: string;
  responseLevel: string;
  resources: string;
  actions: string[];
  duration: string;
} {
  if (score < 20) {
    return {
      category: 'Very Low',
      color: '#2ECC71',
      sizeClass: 'A',
      responseLevel: 'MINIMAL RESPONSE',
      resources: '1 engine, 2-4 personnel',
      actions: [
        'Monitor fire progression',
        'Establish initial attack perimeter',
        'Document fire origin and cause',
        'Coordinate with local dispatch',
      ],
      duration: '1-4 hours',
    };
  } else if (score < 40) {
    return {
      category: 'Low',
      color: '#3498DB',
      sizeClass: 'B',
      responseLevel: 'STANDARD RESPONSE',
      resources: '2-3 engines, 6-10 personnel',
      actions: [
        'Deploy ground crews immediately',
        'Establish containment lines',
        'Request weather updates',
        'Notify nearby property owners',
        'Set up incident command post',
      ],
      duration: '4-12 hours',
    };
  } else if (score < 60) {
    return {
      category: 'Moderate',
      color: '#F39C12',
      sizeClass: 'C-D',
      responseLevel: 'ELEVATED RESPONSE',
      resources: '4-6 engines, 15-30 personnel, 1 helicopter',
      actions: [
        'Request mutual aid from neighboring districts',
        'Deploy aerial reconnaissance',
        'Establish multiple containment lines',
        'Begin evacuation advisories for at-risk areas',
        'Set up staging area for additional resources',
        'Activate public information officer',
      ],
      duration: '12-48 hours',
    };
  } else if (score < 80) {
    return {
      category: 'High',
      color: '#E67E22',
      sizeClass: 'E-F',
      responseLevel: 'MAJOR RESPONSE',
      resources: '10+ engines, 50-100 personnel, 2-4 aircraft',
      actions: [
        'Issue mandatory evacuation orders',
        'Request state emergency resources',
        'Deploy multiple air tankers',
        'Establish unified command structure',
        'Coordinate with law enforcement for evacuations',
        'Set up emergency shelters',
        'Activate emergency broadcast system',
        'Request National Guard assistance if needed',
      ],
      duration: '2-7 days',
    };
  } else {
    return {
      category: 'Critical',
      color: '#E74C3C',
      sizeClass: 'G',
      responseLevel: 'EMERGENCY RESPONSE - CRITICAL',
      resources: '20+ engines, 200+ personnel, 6+ aircraft, National resources',
      actions: [
        'IMMEDIATE: Issue emergency evacuation orders',
        'Request federal disaster assistance',
        'Deploy all available air resources',
        'Establish Type 1 Incident Management Team',
        'Coordinate multi-agency unified command',
        'Activate all mutual aid agreements',
        'Request military support',
        'Establish multiple evacuation routes',
        'Deploy mass casualty incident protocols',
        'Coordinate with FEMA',
      ],
      duration: '1-4+ weeks',
    };
  }
}

export function getRiskCategoryColor(category: RiskCategory): string {
  switch (category) {
    case 'Very Low': return 'hsl(145, 63%, 49%)';
    case 'Low': return 'hsl(204, 70%, 53%)';
    case 'Moderate': return 'hsl(37, 90%, 51%)';
    case 'High': return 'hsl(28, 80%, 52%)';
    case 'Critical': return 'hsl(6, 78%, 57%)';
    default: return 'hsl(210, 15%, 45%)';
  }
}

export function getSeasonFromMonth(month: number): string {
  if (month >= 3 && month <= 5) return 'Spring';
  if (month >= 6 && month <= 8) return 'Summer';
  if (month >= 9 && month <= 11) return 'Fall';
  return 'Winter';
}

export function getDayOfYear(date: Date): number {
  const start = new Date(date.getFullYear(), 0, 0);
  const diff = date.getTime() - start.getTime();
  const oneDay = 1000 * 60 * 60 * 24;
  return Math.floor(diff / oneDay);
}

export function acresToRadius(acres: number): number {
  // Area = πr², so r = sqrt(Area / π)
  // Convert acres to square feet first (1 acre = 43,560 sq ft)
  const sqFeet = acres * 43560;
  const radiusFeet = Math.sqrt(sqFeet / Math.PI);
  // Convert feet to meters
  return radiusFeet * 0.3048;
}

export function acresToKm(acres: number): number {
  // 1 acre = 0.00404686 km²
  // Area = πr² → r = sqrt(Area / π)
  const areaKm2 = acres * 0.00404686;
  return Math.sqrt(areaKm2 / Math.PI);
}

/**
 * Generate fire spread map with wind animation
 * Calls the backend Python script to generate a Folium map
 */
export async function generateFireMap(request: FireMapRequest): Promise<FireMapResponse> {
  const response = await fetch(`${API_BASE_URL}/api/generate-fire-map`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `Request failed: ${response.statusText}`);
  }

  return response.json();
}
