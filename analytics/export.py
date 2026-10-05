"""
Export Module
Exports analysis results to CSV files for Power BI and reporting.
"""

import pandas as pd
import os
from typing import Dict, Any


class DataExporter:
    """Exports analytics results for Power BI and reporting."""

    def __init__(self, output_dir: str = 'output/powerbi'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_kpi_summary(self, kpi_data: Dict[str, Any]):
        """Export KPI summary as JSON and CSV."""
        import json
        with open(os.path.join(self.output_dir, 'kpi_summary.json'), 'w') as f:
            json.dump(kpi_data, f, indent=2, default=str)

    def export_daily_costs(self, df: pd.DataFrame, date_col: str, cost_col: str):
        """Export daily aggregated costs."""
        daily = df.groupby(date_col)[cost_col].sum().reset_index()
        daily.columns = ['Date', 'Daily Cost']
        daily.to_csv(os.path.join(self.output_dir, 'daily_costs.csv'), index=False)
        print(f"  Exported: daily_costs.csv")

    def export_monthly_summary(self, df: pd.DataFrame, date_col: str, cost_col: str):
        """Export monthly summary."""
        df_copy = df.copy()
        df_copy['YearMonth'] = pd.to_datetime(df_copy[date_col]).dt.to_period('M').astype(str)
        monthly = df_copy.groupby('YearMonth')[cost_col].agg(['sum', 'mean', 'count']).reset_index()
        monthly.columns = ['Month', 'Total Cost', 'Avg Daily Cost', 'Record Count']
        monthly.to_csv(os.path.join(self.output_dir, 'monthly_summary.csv'), index=False)
        print(f"  Exported: monthly_summary.csv")

    def export_service_breakdown(self, df: pd.DataFrame, service_col: str, cost_col: str):
        """Export service cost breakdown."""
        svc = df.groupby(service_col)[cost_col].sum().reset_index()
        svc.columns = ['Service', 'Total Cost']
        svc = svc.sort_values('Total Cost', ascending=False)
        svc.to_csv(os.path.join(self.output_dir, 'service_breakdown.csv'), index=False)
        print(f"  Exported: service_breakdown.csv")

    def export_region_breakdown(self, df: pd.DataFrame, region_col: str, cost_col: str):
        """Export region cost breakdown."""
        reg = df.groupby(region_col)[cost_col].sum().reset_index()
        reg.columns = ['Region', 'Total Cost']
        reg = reg.sort_values('Total Cost', ascending=False)
        reg.to_csv(os.path.join(self.output_dir, 'region_breakdown.csv'), index=False)
        print(f"  Exported: region_breakdown.csv")

    def export_anomalies(self, anomalies: pd.DataFrame):
        """Export anomaly records."""
        if not anomalies.empty:
            anomalies.to_csv(os.path.join(self.output_dir, 'anomalies.csv'), index=False)
            print(f"  Exported: anomalies.csv")

    def export_forecasts(self, forecast: pd.DataFrame):
        """Export forecast data."""
        if not forecast.empty:
            forecast.to_csv(os.path.join(self.output_dir, 'forecasts.csv'), index=False)
            print(f"  Exported: forecasts.csv")

    def export_all(self, df: pd.DataFrame, date_col: str, cost_col: str,
                   service_col: str = None, region_col: str = None):
        """Export all standard reports."""
        print("\nExporting data for Power BI...")
        self.export_daily_costs(df, date_col, cost_col)
        self.export_monthly_summary(df, date_col, cost_col)
        if service_col:
            self.export_service_breakdown(df, service_col, cost_col)
        if region_col:
            self.export_region_breakdown(df, region_col, cost_col)
        print(f"\nAll files saved to: {self.output_dir}/")
