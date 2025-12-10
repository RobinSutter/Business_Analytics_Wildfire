export interface PredictionRequest {
  mean_temp: number;
  max_temp: number;
  min_temp: number;
  discovery_temp: number;
  latitude: number;
  longitude: number;
  state: string;
  cause: string;
  month: number;
  day_of_year: number;
  season: string;
  num_cities: number;
  wind_speed?: number;
  wind_direction?: number;
}

export interface PredictionResponse {
  predicted_acres: number;
  predicted_hectares: number;
  risk_score: number;
  risk_category: string;
  risk_color: string;
  fire_size_class: string;
  response_level: string;
  resources: string;
  actions: string[];
  estimated_duration: string;
}

export interface HistoricalPrediction {
  id: string;
  timestamp: string;
  location: {
    lat: number;
    lon: number;
    state: string;
  };
  inputs: PredictionRequest;
  prediction: PredictionResponse;
}

export type RiskCategory = 'Very Low' | 'Low' | 'Moderate' | 'High' | 'Critical';

export interface FireCause {
  value: string;
  label: string;
  icon: string;
}

export const FIRE_CAUSES: FireCause[] = [
  { value: 'Lightning', label: 'Lightning', icon: '⚡' },
  { value: 'Equipment Use', label: 'Equipment Use', icon: '🔧' },
  { value: 'Smoking', label: 'Smoking', icon: '🚬' },
  { value: 'Campfire', label: 'Campfire', icon: '🏕️' },
  { value: 'Debris Burning', label: 'Debris Burning', icon: '🔥' },
  { value: 'Railroad', label: 'Railroad', icon: '🚂' },
  { value: 'Arson', label: 'Arson', icon: '🔥' },
  { value: 'Children', label: 'Children', icon: '👶' },
  { value: 'Miscellaneous', label: 'Miscellaneous', icon: '❓' },
  { value: 'Fireworks', label: 'Fireworks', icon: '🎆' },
  { value: 'Powerline', label: 'Powerline', icon: '⚡' },
  { value: 'Structure', label: 'Structure', icon: '🏠' },
  { value: 'Missing/Undefined', label: 'Unknown', icon: '❓' },
];

export const US_STATES = [
  { value: 'AL', label: 'Alabama' },
  { value: 'AK', label: 'Alaska' },
  { value: 'AZ', label: 'Arizona' },
  { value: 'AR', label: 'Arkansas' },
  { value: 'CA', label: 'California' },
  { value: 'CO', label: 'Colorado' },
  { value: 'CT', label: 'Connecticut' },
  { value: 'DE', label: 'Delaware' },
  { value: 'FL', label: 'Florida' },
  { value: 'GA', label: 'Georgia' },
  { value: 'HI', label: 'Hawaii' },
  { value: 'ID', label: 'Idaho' },
  { value: 'IL', label: 'Illinois' },
  { value: 'IN', label: 'Indiana' },
  { value: 'IA', label: 'Iowa' },
  { value: 'KS', label: 'Kansas' },
  { value: 'KY', label: 'Kentucky' },
  { value: 'LA', label: 'Louisiana' },
  { value: 'ME', label: 'Maine' },
  { value: 'MD', label: 'Maryland' },
  { value: 'MA', label: 'Massachusetts' },
  { value: 'MI', label: 'Michigan' },
  { value: 'MN', label: 'Minnesota' },
  { value: 'MS', label: 'Mississippi' },
  { value: 'MO', label: 'Missouri' },
  { value: 'MT', label: 'Montana' },
  { value: 'NE', label: 'Nebraska' },
  { value: 'NV', label: 'Nevada' },
  { value: 'NH', label: 'New Hampshire' },
  { value: 'NJ', label: 'New Jersey' },
  { value: 'NM', label: 'New Mexico' },
  { value: 'NY', label: 'New York' },
  { value: 'NC', label: 'North Carolina' },
  { value: 'ND', label: 'North Dakota' },
  { value: 'OH', label: 'Ohio' },
  { value: 'OK', label: 'Oklahoma' },
  { value: 'OR', label: 'Oregon' },
  { value: 'PA', label: 'Pennsylvania' },
  { value: 'RI', label: 'Rhode Island' },
  { value: 'SC', label: 'South Carolina' },
  { value: 'SD', label: 'South Dakota' },
  { value: 'TN', label: 'Tennessee' },
  { value: 'TX', label: 'Texas' },
  { value: 'UT', label: 'Utah' },
  { value: 'VT', label: 'Vermont' },
  { value: 'VA', label: 'Virginia' },
  { value: 'WA', label: 'Washington' },
  { value: 'WV', label: 'West Virginia' },
  { value: 'WI', label: 'Wisconsin' },
  { value: 'WY', label: 'Wyoming' },
];

export const SEASONS = [
  { value: 'Spring', label: 'Spring', months: [3, 4, 5] },
  { value: 'Summer', label: 'Summer', months: [6, 7, 8] },
  { value: 'Fall', label: 'Fall', months: [9, 10, 11] },
  { value: 'Winter', label: 'Winter', months: [12, 1, 2] },
];

// State center coordinates (approximate capital cities)
export const STATE_COORDINATES: Record<string, { lat: number; lon: number }> = {
  'AL': { lat: 32.3792, lon: -86.3077 },
  'AK': { lat: 61.2181, lon: -149.9003 },
  'AZ': { lat: 33.4484, lon: -112.0740 },
  'AR': { lat: 34.7465, lon: -92.2896 },
  'CA': { lat: 36.7783, lon: -119.4179 },
  'CO': { lat: 39.5501, lon: -105.7821 },
  'CT': { lat: 41.6032, lon: -73.0877 },
  'DE': { lat: 38.9108, lon: -75.5277 },
  'FL': { lat: 27.9947, lon: -81.7603 },
  'GA': { lat: 32.1656, lon: -82.9001 },
  'HI': { lat: 19.8968, lon: -155.5828 },
  'ID': { lat: 44.0682, lon: -114.7420 },
  'IL': { lat: 40.6331, lon: -89.3985 },
  'IN': { lat: 40.2672, lon: -86.1349 },
  'IA': { lat: 41.8780, lon: -93.0977 },
  'KS': { lat: 39.0119, lon: -98.4842 },
  'KY': { lat: 37.8393, lon: -84.2700 },
  'LA': { lat: 30.9843, lon: -91.9623 },
  'ME': { lat: 45.3695, lon: -69.2428 },
  'MD': { lat: 39.0458, lon: -76.6413 },
  'MA': { lat: 42.4072, lon: -71.3824 },
  'MI': { lat: 44.3148, lon: -85.6024 },
  'MN': { lat: 46.7296, lon: -94.6859 },
  'MS': { lat: 32.3547, lon: -89.3985 },
  'MO': { lat: 37.9643, lon: -91.8318 },
  'MT': { lat: 46.8797, lon: -110.3626 },
  'NE': { lat: 41.4925, lon: -99.9018 },
  'NV': { lat: 38.8026, lon: -116.4194 },
  'NH': { lat: 43.1939, lon: -71.5724 },
  'NJ': { lat: 40.0583, lon: -74.4057 },
  'NM': { lat: 34.5199, lon: -105.8701 },
  'NY': { lat: 43.2994, lon: -74.2179 },
  'NC': { lat: 35.7596, lon: -79.0193 },
  'ND': { lat: 47.5515, lon: -101.0020 },
  'OH': { lat: 40.4173, lon: -82.9071 },
  'OK': { lat: 35.0078, lon: -97.0929 },
  'OR': { lat: 43.8041, lon: -120.5542 },
  'PA': { lat: 41.2033, lon: -77.1945 },
  'RI': { lat: 41.5801, lon: -71.4774 },
  'SC': { lat: 33.8361, lon: -81.1637 },
  'SD': { lat: 43.9695, lon: -99.9018 },
  'TN': { lat: 35.5175, lon: -86.5804 },
  'TX': { lat: 31.9686, lon: -99.9018 },
  'UT': { lat: 39.3210, lon: -111.0937 },
  'VT': { lat: 44.5588, lon: -72.5778 },
  'VA': { lat: 37.4316, lon: -78.6569 },
  'WA': { lat: 47.7511, lon: -120.7401 },
  'WV': { lat: 38.5976, lon: -80.4549 },
  'WI': { lat: 43.7844, lon: -88.7879 },
  'WY': { lat: 43.0760, lon: -107.2903 },
};
