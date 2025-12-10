import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format large numbers with K/M/B suffix
 * Examples: 14407 → "14.4K", 1500000 → "1.5M"
 */
export function formatNumber(num: number): string {
  if (num >= 1000000000) {
    return (num / 1000000000).toFixed(1) + 'B';
  }
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M';
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toFixed(0);
}

/**
 * Format decimal numbers to max 2 decimal places
 * Examples: 4.317391 → "4.32", 10.5 → "10.5", 10 → "10"
 */
export function formatDecimal(num: number, maxDecimals: number = 2): string {
  const rounded = Number(num.toFixed(maxDecimals));
  return rounded.toString();
}
