import { 
  Flame, 
  Target, 
  Layers, 
  Clock
} from 'lucide-react';
import { RiskGauge } from './RiskGauge';
import { MetricCard } from './MetricCard';
import { FireMapViewer } from './FireMapViewer';
import { RecommendationsPanel } from './RecommendationsPanel';
import { PredictionResponse, PredictionRequest, RiskCategory } from '@/types/prediction';
import { acresToKm } from '@/lib/api';
import { formatNumber, formatDecimal } from '@/lib/utils';

interface PredictionResultsProps {
  prediction: PredictionResponse;
  inputs: PredictionRequest;
}

export function PredictionResults({ prediction, inputs }: PredictionResultsProps) {
  // Convert predicted acres to radius in km for the fire map
  const radiusKm = Math.max(1, acresToKm(prediction.predicted_acres));

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Risk Score Section */}
      <div className="glass-card rounded-xl p-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
          {/* Gauge */}
          <div className="flex justify-center">
            <RiskGauge
              score={prediction.risk_score}
              category={prediction.risk_category as RiskCategory}
            />
          </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-2 gap-4">
            <MetricCard
              title="Predicted Size"
              value={`${formatNumber(prediction.predicted_acres)} acres`}
              subtitle={`${formatNumber(prediction.predicted_hectares)} hectares`}
              icon={Flame}
              color="danger"
            />
            
            <MetricCard
              title="Risk Score"
              value={`${formatDecimal(prediction.risk_score)}/100`}
              subtitle={prediction.risk_category}
              icon={Target}
              color={
                prediction.risk_score < 40 ? 'success' :
                prediction.risk_score < 60 ? 'warning' : 'danger'
              }
            />
            
            <MetricCard
              title="Fire Class"
              value={prediction.fire_size_class}
              subtitle="NWCG Classification"
              icon={Layers}
              color="info"
            />
            
            <MetricCard
              title="Est. Duration"
              value={prediction.estimated_duration}
              subtitle="Response timeline"
              icon={Clock}
              color="default"
            />
          </div>
        </div>
      </div>

      {/* Fire Size Classification */}
      <div className="glass-card rounded-xl p-6">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Layers className="w-5 h-5 text-primary" />
          Fire Size Classification Guide
        </h3>
        <div className="grid grid-cols-7 gap-2 text-center text-sm">
          {[
            { class: 'A', range: '< 0.25 ac', active: prediction.fire_size_class === 'A' },
            { class: 'B', range: '0.25-10 ac', active: prediction.fire_size_class === 'B' },
            { class: 'C', range: '10-100 ac', active: prediction.fire_size_class.includes('C') },
            { class: 'D', range: '100-300 ac', active: prediction.fire_size_class.includes('D') },
            { class: 'E', range: '300-1K ac', active: prediction.fire_size_class.includes('E') },
            { class: 'F', range: '1K-5K ac', active: prediction.fire_size_class.includes('F') },
            { class: 'G', range: '> 5K ac', active: prediction.fire_size_class === 'G' },
          ].map((item) => (
            <div
              key={item.class}
              className={`p-3 rounded-lg transition-all ${
                item.active
                  ? 'bg-primary text-primary-foreground scale-105 shadow-lg'
                  : 'bg-muted/50 text-muted-foreground'
              }`}
            >
              <div className="text-xl font-bold">{item.class}</div>
              <div className="text-xs opacity-80">{item.range}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Real Fire Spread Map with County Population Analysis */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Flame className="w-5 h-5 text-primary" />
          Fire Spread & Population Impact Map
        </h3>
        
        <FireMapViewer
          latitude={inputs.latitude}
          longitude={inputs.longitude}
          radiusKm={radiusKm}
          windSpeed={inputs.wind_speed || 10}
          windDirection={inputs.wind_direction || 0}
          riskCategory={prediction.risk_category}
        />
      </div>

      {/* Recommendations */}
      <RecommendationsPanel prediction={prediction} />
    </div>
  );
}
