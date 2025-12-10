import { HistoricalPrediction } from '@/types/prediction';

const STORAGE_KEY = 'fsp_predictions_history';

export function savePrediction(prediction: HistoricalPrediction): void {
  const history = getHistory();
  history.unshift(prediction);
  // Keep only last 50 predictions
  const trimmed = history.slice(0, 50);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
}

export function getHistory(): HistoricalPrediction[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

export function deletePrediction(id: string): void {
  const history = getHistory().filter(p => p.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
}

export function clearHistory(): void {
  localStorage.removeItem(STORAGE_KEY);
}

export function generateId(): string {
  return `pred_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
