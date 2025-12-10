#!/usr/bin/env python3
"""
Analyze wildfire data with temperature information.

Generates comprehensive visualizations and statistics exploring the relationship
between temperature and wildfire characteristics (size, frequency, causes, etc.)

Usage:
  uv run python src/analyze_fire_temperature.py
  uv run python src/analyze_fire_temperature.py --input data/processed/fires_with_temperature.csv
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


def load_and_clean_data(csv_path: str) -> pd.DataFrame:
    """Load fire-temperature data and perform basic cleaning."""
    print(f"Loading data from {csv_path}...")
    df = pd.read_csv(csv_path, parse_dates=['discovery_date', 'cont_date'])
    
    print(f"  Loaded {len(df):,} records")
    
    # Filter to records with valid temperature data
    df_clean = df[df['discovery_temp'].notna()].copy()
    print(f"  {len(df_clean):,} records have temperature data ({len(df_clean)/len(df)*100:.1f}%)")
    
    # Add derived columns
    df_clean['discovery_year'] = df_clean['discovery_date'].dt.year
    df_clean['discovery_month'] = df_clean['discovery_date'].dt.month
    df_clean['discovery_day_of_year'] = df_clean['discovery_date'].dt.dayofyear
    
    # Calculate fire duration in days
    df_clean['duration_days'] = (
        df_clean['cont_date'] - df_clean['discovery_date']
    ).dt.total_seconds() / 86400
    df_clean['duration_days'] = df_clean['duration_days'].clip(lower=0)
    
    # Season mapping
    season_map = {1: 'Winter', 2: 'Winter', 3: 'Spring', 4: 'Spring', 5: 'Spring',
                  6: 'Summer', 7: 'Summer', 8: 'Summer', 9: 'Fall', 10: 'Fall',
                  11: 'Fall', 12: 'Winter'}
    df_clean['season'] = df_clean['discovery_month'].map(season_map)
    
    return df_clean


def create_output_dir(output_dir: str) -> Path:
    """Create output directory for plots."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def plot_temporal_trends(df: pd.DataFrame, output_dir: Path):
    """Generate temporal analysis plots."""
    print("\nGenerating temporal analysis plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Fires per year
    yearly = df.groupby('discovery_year').size()
    axes[0, 0].plot(yearly.index, yearly.values, marker='o', linewidth=2)
    axes[0, 0].set_xlabel('Year', fontsize=12)
    axes[0, 0].set_ylabel('Number of Fires', fontsize=12)
    axes[0, 0].set_title('Wildfire Frequency Over Time (1992-2013)', fontsize=14, fontweight='bold')
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Mean temperature over years
    yearly_temp = df.groupby('discovery_year')['discovery_temp'].mean()
    ax2 = axes[0, 1]
    ax2.plot(yearly_temp.index, yearly_temp.values, marker='o', color='orangered', linewidth=2)
    ax2.set_xlabel('Year', fontsize=12)
    ax2.set_ylabel('Mean Temperature (°C)', fontsize=12)
    ax2.set_title('Average Discovery Temperature Over Time', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # 3. Monthly distribution (all years combined)
    monthly_counts = df.groupby('discovery_month').size()
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    axes[1, 0].bar(range(1, 13), monthly_counts.values, color='steelblue')
    axes[1, 0].set_xlabel('Month', fontsize=12)
    axes[1, 0].set_ylabel('Total Fires', fontsize=12)
    axes[1, 0].set_title('Seasonal Distribution of Wildfires', fontsize=14, fontweight='bold')
    axes[1, 0].set_xticks(range(1, 13))
    axes[1, 0].set_xticklabels(month_names, rotation=45)
    axes[1, 0].grid(True, axis='y', alpha=0.3)
    
    # 4. Day of year density
    axes[1, 1].hist(df['discovery_day_of_year'], bins=52, color='forestgreen', alpha=0.7, edgecolor='black')
    axes[1, 1].set_xlabel('Day of Year', fontsize=12)
    axes[1, 1].set_ylabel('Number of Fires', fontsize=12)
    axes[1, 1].set_title('Fire Distribution Throughout the Year', fontsize=14, fontweight='bold')
    axes[1, 1].grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'temporal_trends.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved temporal_trends.png")


def plot_temperature_relationships(df: pd.DataFrame, output_dir: Path):
    """Plot relationships between temperature and fire characteristics."""
    print("\nGenerating temperature relationship plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Temperature distribution by season
    season_order = ['Winter', 'Spring', 'Summer', 'Fall']
    sns.boxplot(data=df, x='season', y='discovery_temp', order=season_order, ax=axes[0, 0])
    axes[0, 0].set_xlabel('Season', fontsize=12)
    axes[0, 0].set_ylabel('Temperature (°C)', fontsize=12)
    axes[0, 0].set_title('Temperature Distribution by Season', fontsize=14, fontweight='bold')
    axes[0, 0].grid(True, axis='y', alpha=0.3)
    
    # 2. Fire size vs temperature (binned)
    temp_bins = pd.cut(df['discovery_temp'], bins=10)
    size_by_temp = df.groupby(temp_bins)['FIRE_SIZE'].mean()
    bin_centers = [interval.mid for interval in size_by_temp.index]
    axes[0, 1].plot(bin_centers, size_by_temp.values, marker='o', linewidth=2, markersize=8, color='red')
    axes[0, 1].set_xlabel('Temperature (°C)', fontsize=12)
    axes[0, 1].set_ylabel('Average Fire Size (acres)', fontsize=12)
    axes[0, 1].set_title('Fire Size vs. Discovery Temperature', fontsize=14, fontweight='bold')
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Temperature range vs fire duration
    valid_duration = df[df['duration_days'] > 0]
    if len(valid_duration) > 100:
        axes[1, 0].scatter(valid_duration['temp_range'], valid_duration['duration_days'], 
                          alpha=0.3, s=10, color='purple')
        axes[1, 0].set_xlabel('Temperature Range During Fire (°C)', fontsize=12)
        axes[1, 0].set_ylabel('Fire Duration (days)', fontsize=12)
        axes[1, 0].set_title('Fire Duration vs. Temperature Variation', fontsize=14, fontweight='bold')
        axes[1, 0].set_ylim([0, min(valid_duration['duration_days'].quantile(0.95), 100)])
        axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Fire size class distribution by temperature quartile
    df['temp_quartile'] = pd.qcut(df['discovery_temp'], q=4, labels=['Q1 (Cold)', 'Q2', 'Q3', 'Q4 (Hot)'])
    size_class_temp = pd.crosstab(df['temp_quartile'], df['FIRE_SIZE_CLASS'], normalize='index') * 100
    size_class_temp.plot(kind='bar', stacked=True, ax=axes[1, 1], colormap='YlOrRd')
    axes[1, 1].set_xlabel('Temperature Quartile', fontsize=12)
    axes[1, 1].set_ylabel('Percentage', fontsize=12)
    axes[1, 1].set_title('Fire Size Class Distribution by Temperature', fontsize=14, fontweight='bold')
    axes[1, 1].legend(title='Size Class', bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[1, 1].set_xticklabels(axes[1, 1].get_xticklabels(), rotation=45)
    axes[1, 1].grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'temperature_relationships.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved temperature_relationships.png")


def plot_fire_causes(df: pd.DataFrame, output_dir: Path):
    """Analyze and visualize fire causes."""
    print("\nGenerating fire cause analysis plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Top causes overall
    cause_counts = df['STAT_CAUSE_DESCR'].value_counts().head(10)
    axes[0, 0].barh(range(len(cause_counts)), cause_counts.values, color='coral')
    axes[0, 0].set_yticks(range(len(cause_counts)))
    axes[0, 0].set_yticklabels(cause_counts.index, fontsize=10)
    axes[0, 0].set_xlabel('Number of Fires', fontsize=12)
    axes[0, 0].set_title('Top 10 Fire Causes', fontsize=14, fontweight='bold')
    axes[0, 0].invert_yaxis()
    axes[0, 0].grid(True, axis='x', alpha=0.3)
    
    # 2. Average temperature by cause (top causes)
    top_causes = cause_counts.head(8).index
    cause_temp = df[df['STAT_CAUSE_DESCR'].isin(top_causes)].groupby('STAT_CAUSE_DESCR')['discovery_temp'].mean().sort_values()
    axes[0, 1].barh(range(len(cause_temp)), cause_temp.values, color='skyblue')
    axes[0, 1].set_yticks(range(len(cause_temp)))
    axes[0, 1].set_yticklabels(cause_temp.index, fontsize=10)
    axes[0, 1].set_xlabel('Average Temperature (°C)', fontsize=12)
    axes[0, 1].set_title('Average Discovery Temperature by Cause', fontsize=14, fontweight='bold')
    axes[0, 1].invert_yaxis()
    axes[0, 1].grid(True, axis='x', alpha=0.3)
    
    # 3. Seasonal variation by cause (top 4 causes)
    top_4_causes = cause_counts.head(4).index
    season_order = ['Winter', 'Spring', 'Summer', 'Fall']
    season_cause = df[df['STAT_CAUSE_DESCR'].isin(top_4_causes)].groupby(['season', 'STAT_CAUSE_DESCR']).size().unstack(fill_value=0)
    season_cause = season_cause.reindex(season_order)
    season_cause.plot(kind='bar', ax=axes[1, 0], width=0.8)
    axes[1, 0].set_xlabel('Season', fontsize=12)
    axes[1, 0].set_ylabel('Number of Fires', fontsize=12)
    axes[1, 0].set_title('Top Fire Causes by Season', fontsize=14, fontweight='bold')
    axes[1, 0].legend(title='Cause', bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=45)
    axes[1, 0].grid(True, axis='y', alpha=0.3)
    
    # 4. Fire size by cause (top causes)
    cause_size = df[df['STAT_CAUSE_DESCR'].isin(top_causes)].groupby('STAT_CAUSE_DESCR')['FIRE_SIZE'].mean().sort_values(ascending=False)
    axes[1, 1].barh(range(len(cause_size)), cause_size.values, color='orange')
    axes[1, 1].set_yticks(range(len(cause_size)))
    axes[1, 1].set_yticklabels(cause_size.index, fontsize=10)
    axes[1, 1].set_xlabel('Average Fire Size (acres)', fontsize=12)
    axes[1, 1].set_title('Average Fire Size by Cause', fontsize=14, fontweight='bold')
    axes[1, 1].invert_yaxis()
    axes[1, 1].grid(True, axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'fire_causes.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved fire_causes.png")


def plot_geographic_analysis(df: pd.DataFrame, output_dir: Path):
    """Generate geographic analysis plots."""
    print("\nGenerating geographic analysis plots...")
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Top states by fire count
    state_counts = df['STATE'].value_counts().head(15)
    axes[0, 0].barh(range(len(state_counts)), state_counts.values, color='seagreen')
    axes[0, 0].set_yticks(range(len(state_counts)))
    axes[0, 0].set_yticklabels(state_counts.index, fontsize=10)
    axes[0, 0].set_xlabel('Number of Fires', fontsize=12)
    axes[0, 0].set_title('Top 15 States by Fire Count', fontsize=14, fontweight='bold')
    axes[0, 0].invert_yaxis()
    axes[0, 0].grid(True, axis='x', alpha=0.3)
    
    # 2. Average temperature by state (top states)
    top_states = state_counts.head(15).index
    state_temp = df[df['STATE'].isin(top_states)].groupby('STATE')['discovery_temp'].mean().sort_values()
    axes[0, 1].barh(range(len(state_temp)), state_temp.values, color='indianred')
    axes[0, 1].set_yticks(range(len(state_temp)))
    axes[0, 1].set_yticklabels(state_temp.index, fontsize=10)
    axes[0, 1].set_xlabel('Average Temperature (°C)', fontsize=12)
    axes[0, 1].set_title('Average Fire Temperature by State', fontsize=14, fontweight='bold')
    axes[0, 1].invert_yaxis()
    axes[0, 1].grid(True, axis='x', alpha=0.3)
    
    # 3. Latitude vs Temperature
    axes[1, 0].scatter(df['LATITUDE'], df['discovery_temp'], alpha=0.1, s=5, color='blue')
    axes[1, 0].set_xlabel('Latitude', fontsize=12)
    axes[1, 0].set_ylabel('Discovery Temperature (°C)', fontsize=12)
    axes[1, 0].set_title('Fire Temperature by Latitude', fontsize=14, fontweight='bold')
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Geographic scatter (simple map)
    scatter = axes[1, 1].scatter(df['LONGITUDE'], df['LATITUDE'], 
                                 c=df['discovery_temp'], cmap='RdYlBu_r',
                                 s=1, alpha=0.3)
    axes[1, 1].set_xlabel('Longitude', fontsize=12)
    axes[1, 1].set_ylabel('Latitude', fontsize=12)
    axes[1, 1].set_title('Geographic Distribution of Fires (colored by temperature)', 
                         fontsize=14, fontweight='bold')
    cbar = plt.colorbar(scatter, ax=axes[1, 1])
    cbar.set_label('Temperature (°C)', fontsize=10)
    axes[1, 1].set_xlim([-130, -65])
    axes[1, 1].set_ylim([25, 50])
    
    plt.tight_layout()
    plt.savefig(output_dir / 'geographic_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved geographic_analysis.png")


def generate_statistics(df: pd.DataFrame, output_dir: Path):
    """Generate summary statistics and correlations."""
    print("\nGenerating statistical summary...")
    
    stats = []
    
    # Overall statistics
    stats.append("=" * 80)
    stats.append("WILDFIRE-TEMPERATURE ANALYSIS SUMMARY")
    stats.append("=" * 80)
    stats.append(f"\nDataset Overview:")
    stats.append(f"  Total fires analyzed: {len(df):,}")
    stats.append(f"  Time period: {df['discovery_year'].min()}-{df['discovery_year'].max()}")
    stats.append(f"  States covered: {df['STATE'].nunique()}")
    stats.append(f"  Unique fire causes: {df['STAT_CAUSE_DESCR'].nunique()}")
    
    stats.append(f"\nTemperature Statistics:")
    stats.append(f"  Mean discovery temperature: {df['discovery_temp'].mean():.2f}°C")
    stats.append(f"  Std deviation: {df['discovery_temp'].std():.2f}°C")
    stats.append(f"  Temperature range: {df['discovery_temp'].min():.2f}°C to {df['discovery_temp'].max():.2f}°C")
    stats.append(f"  Median: {df['discovery_temp'].median():.2f}°C")
    
    stats.append(f"\nFire Size Statistics:")
    stats.append(f"  Mean fire size: {df['FIRE_SIZE'].mean():.2f} acres")
    stats.append(f"  Median fire size: {df['FIRE_SIZE'].median():.2f} acres")
    stats.append(f"  Largest fire: {df['FIRE_SIZE'].max():.2f} acres")
    stats.append(f"  Total acres burned: {df['FIRE_SIZE'].sum():,.0f}")
    
    # Correlation analysis
    stats.append(f"\nCorrelation Analysis:")
    corr_vars = ['discovery_temp', 'mean_temp', 'temp_range', 'FIRE_SIZE', 'duration_days']
    corr_matrix = df[corr_vars].corr()
    stats.append(f"\nTemperature vs Fire Size correlation: {corr_matrix.loc['discovery_temp', 'FIRE_SIZE']:.3f}")
    stats.append(f"Temperature range vs Duration correlation: {corr_matrix.loc['temp_range', 'duration_days']:.3f}")
    stats.append(f"Mean temp vs Fire Size correlation: {corr_matrix.loc['mean_temp', 'FIRE_SIZE']:.3f}")
    
    # Seasonal breakdown
    stats.append(f"\nSeasonal Breakdown:")
    season_stats = df.groupby('season').agg({
        'OBJECTID': 'count',
        'discovery_temp': 'mean',
        'FIRE_SIZE': 'mean'
    }).round(2)
    season_stats.columns = ['Count', 'Avg Temp (°C)', 'Avg Size (acres)']
    stats.append(season_stats.to_string())
    
    # Top causes
    stats.append(f"\nTop 5 Fire Causes:")
    top_causes = df['STAT_CAUSE_DESCR'].value_counts().head(5)
    for cause, count in top_causes.items():
        pct = (count / len(df)) * 100
        stats.append(f"  {cause}: {count:,} ({pct:.1f}%)")
    
    # Save to file
    stats_text = "\n".join(stats)
    with open(output_dir / 'statistics_summary.txt', 'w') as f:
        f.write(stats_text)
    
    print(stats_text)
    print(f"\n  ✓ Saved statistics_summary.txt")
    
    # Generate correlation heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title('Correlation Matrix: Temperature and Fire Characteristics', 
                 fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("  ✓ Saved correlation_heatmap.png")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analyze wildfire data with temperature information"
    )
    parser.add_argument(
        "--input",
        default="data/processed/fires_with_temperature.csv",
        help="Path to fire-temperature CSV",
    )
    parser.add_argument(
        "--output",
        default="reports",
        help="Output directory for plots and statistics",
    )
    
    args = parser.parse_args(argv)
    
    # Load and clean data
    df = load_and_clean_data(args.input)
    
    # Create output directory
    output_dir = create_output_dir(args.output)
    print(f"\nOutput directory: {output_dir}")
    
    # Generate all visualizations and statistics
    plot_temporal_trends(df, output_dir)
    plot_temperature_relationships(df, output_dir)
    plot_fire_causes(df, output_dir)
    plot_geographic_analysis(df, output_dir)
    generate_statistics(df, output_dir)
    
    print(f"\n{'='*80}")
    print("✓ Analysis complete! All plots and statistics saved to:", output_dir)
    print(f"{'='*80}\n")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
