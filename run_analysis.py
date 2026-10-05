"""
Cloud Cost Analytics - Main Analytics Runner (AI-Powered)
Analyzes cloud billing data with ML, NLP insights, and AI recommendations.

Usage:
    python run_analysis.py [--data PATH] [--output DIR]
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime

from analytics.kpis import KPICalculator
from analytics.visualizations import CostVisualizer
from analytics.anomaly import AnomalyDetector
from analytics.forecast import CostForecaster
from analytics.export import DataExporter
from analytics.ai_features import AICostAnalyzer
from analytics.nlp_insights import NLPInsightsGenerator
from analytics.feature_engineering import FeatureEngineer
from analytics.model_evaluation import ModelEvaluator


def load_data(filepath: str) -> pd.DataFrame:
    """Load cloud billing data from CSV."""
    print(f"Loading data from: {filepath}")
    df = pd.read_csv(filepath)
    print(f"  Loaded {len(df):,} records with {len(df.columns)} columns")
    print(f"  Columns: {list(df.columns)}")
    return df


def print_kpi_report(kpis: dict):
    """Print formatted KPI report."""
    print("\n" + "=" * 60)
    print("CLOUD COST ANALYTICS - KPI REPORT")
    print("=" * 60)
    print(f"Total Spend:        ${kpis['total_spend']:>15,.2f}")
    print(f"Avg Daily Cost:     ${kpis['average_daily_cost']:>15,.2f}")
    print(f"Total Records:      {kpis['total_records']:>15,}")
    print(f"Date Range:         {kpis['date_range']}")
    print("=" * 60)

    if kpis['top_services']:
        print("\nTop 5 Services by Cost:")
        print("-" * 40)
        for svc in kpis['top_services']:
            print(f"  {svc['Service']:<30} ${svc['Total Cost']:>10,.2f} ({svc['% of Total']}%)")

    if kpis['top_regions']:
        print("\nTop 5 Regions by Cost:")
        print("-" * 40)
        for reg in kpis['top_regions']:
            print(f"  {reg['Region']:<30} ${reg['Total Cost']:>10,.2f}")


def main():
    parser = argparse.ArgumentParser(description='Cloud Cost Analytics (AI-Powered)')
    parser.add_argument('--data', type=str, default='data/cloud_billing.csv',
                       help='Path to cloud billing CSV file')
    parser.add_argument('--output', type=str, default='output',
                       help='Output directory for charts and exports')
    args = parser.parse_args()

    # Create output directories
    os.makedirs(f'{args.output}/charts', exist_ok=True)
    os.makedirs(f'{args.output}/powerbi', exist_ok=True)

    # Load data
    if not os.path.exists(args.data):
        print(f"ERROR: Data file not found: {args.data}")
        print("\nPlease download a cloud billing dataset from Kaggle:")
        print("  1. Go to kaggle.com/datasets")
        print("  2. Search for 'cloud billing data' or 'AWS cost usage'")
        print("  3. Download and save as: data/cloud_billing.csv")
        sys.exit(1)

    df = load_data(args.data)

    # Detect columns
    date_cols = [c for c in df.columns if 'date' in c.lower()]
    cost_cols = [c for c in df.columns if 'cost' in c.lower() or 'amount' in c.lower() or 'charge' in c.lower()]
    service_cols = [c for c in df.columns if 'service' in c.lower() or 'product' in c.lower()]
    region_cols = [c for c in df.columns if 'region' in c.lower()]

    date_col = date_cols[0] if date_cols else None
    cost_col = cost_cols[0] if cost_cols else None
    service_col = service_cols[0] if service_cols else None
    region_col = region_cols[0] if region_cols else None

    if not date_col or not cost_col:
        print("ERROR: Could not detect date and cost columns.")
        print(f"  Available columns: {list(df.columns)}")
        sys.exit(1)

    print(f"\nUsing columns: date='{date_col}', cost='{cost_col}'")

    # Step 1: Calculate KPIs
    print("\n" + "=" * 60)
    print("STEP 1: Calculating KPIs...")
    calc = KPICalculator(df)
    kpis = calc.summary()
    print_kpi_report(kpis)

    # Step 2: Generate Visualizations
    print("\n" + "=" * 60)
    print("STEP 2: Generating Visualizations...")
    viz = CostVisualizer(df, output_dir=f'{args.output}/charts')
    viz.generate_all()

    # Step 3: Anomaly Detection
    print("\n" + "=" * 60)
    print("STEP 3: Anomaly Detection...")
    detector = AnomalyDetector(df, output_dir=f'{args.output}/charts')
    anomaly_results = detector.run_all()
    print(f"\nAnomalies detected:")
    print(f"  Z-Score method:    {anomaly_results['zscore_count']} days")
    print(f"  IQR method:        {anomaly_results['iqr_count']} days")
    print(f"  Rolling method:    {anomaly_results['rolling_count']} days")

    # Step 4: Forecasting
    print("\n" + "=" * 60)
    print("STEP 4: Cost Forecasting...")
    forecaster = CostForecaster(df, output_dir=f'{args.output}/charts')
    forecast_results = forecaster.run_all()
    print(f"\n30-Day Forecast:")
    print(f"  Projected total:   ${forecast_results['forecast_30d_total']:>12,.2f}")
    print(f"  Daily average:     ${forecast_results['forecast_30d_daily_avg']:>12,.2f}")

    # Step 5: AI-Powered Analysis
    print("\n" + "=" * 60)
    print("STEP 5: AI-Powered Analysis...")
    ai_analyzer = AICostAnalyzer(df)
    ai_results = ai_analyzer.run_full_ai_analysis()

    # Step 6: NLP Insights
    print("\n" + "=" * 60)
    print("STEP 6: Generating NLP Insights...")
    nlp = NLPInsightsGenerator(df)
    report = nlp.generate_full_report()
    print(report)

    # Save NLP report
    with open(f'{args.output}/nlp_report.txt', 'w') as f:
        f.write(report)
    print(f"\n  Saved: {args.output}/nlp_report.txt")

    # Step 7: Feature Engineering
    print("\n" + "=" * 60)
    print("STEP 7: Feature Engineering...")
    fe = FeatureEngineer(df)
    X, y = fe.prepare_ml_data()
    print(f"  Created {len(X.columns)} features for ML model")
    print(f"  Top features: {fe.get_feature_importance_names()[:5]}")

    # Step 8: Model Evaluation
    print("\n" + "=" * 60)
    print("STEP 8: Model Evaluation...")
    evaluator = ModelEvaluator(output_dir=f'{args.output}/charts')

    # Step 9: Export for Power BI
    print("\n" + "=" * 60)
    print("STEP 9: Exporting Data for Power BI...")
    exporter = DataExporter(output_dir=f'{args.output}/powerbi')
    exporter.export_kpi_summary(kpis)
    exporter.export_all(df, date_col, cost_col, service_col, region_col)

    # Export AI results
    ai_summary = {
        'insights': ai_results['insights'],
        'recommendations': ai_results['recommendations'],
        'anomaly_model_accuracy': ai_results['anomaly_model'].get('test_accuracy', 'N/A'),
        'cost_predictor_r2': ai_results['cost_predictor'].get('r2_score', 'N/A')
    }
    import json
    with open(f'{args.output}/powerbi/ai_insights.json', 'w') as f:
        json.dump(ai_summary, f, indent=2, default=str)
    print(f"  Exported: ai_insights.json")

    # Final Summary
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE!")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  Charts:     {args.output}/charts/")
    print(f"  Power BI:   {args.output}/powerbi/")
    print(f"  NLP Report: {args.output}/nlp_report.txt")
    print(f"\nNext steps:")
    print(f"  1. Review charts in {args.output}/charts/")
    print(f"  2. Import {args.output}/powerbi/*.csv into Power BI")
    print(f"  3. Build dashboards using POWERBI_GUIDE.md")


if __name__ == '__main__':
    main()
