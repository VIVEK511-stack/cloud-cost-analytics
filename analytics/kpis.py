"""
KPI Calculations Module
Computes all cloud cost business metrics from billing data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any


class KPICalculator:
    """Calculates cloud cost KPIs from billing DataFrame."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Ensure date column is datetime
        date_cols = [c for c in self.df.columns if 'date' in c.lower()]
        if date_cols:
            self.df[date_cols[0]] = pd.to_datetime(self.df[date_cols[0]], errors='coerce')
            self.date_col = date_cols[0]
        else:
            self.date_col = None

        # Find cost column
        cost_cols = [c for c in self.df.columns if 'cost' in c.lower() or 'amount' in c.lower() or 'charge' in c.lower()]
        self.cost_col = cost_cols[0] if cost_cols else None

    def total_spend(self) -> float:
        """Total cloud spend for the entire period."""
        if self.cost_col:
            return round(self.df[self.cost_col].sum(), 2)
        return 0.0

    def average_daily_cost(self) -> float:
        """Average daily cost."""
        if not self.date_col or not self.cost_col:
            return 0.0
        daily = self.df.groupby(self.date_col)[self.cost_col].sum()
        return round(daily.mean(), 2) if len(daily) > 0 else 0.0

    def monthly_spend(self) -> pd.DataFrame:
        """Monthly spend breakdown."""
        if not self.date_col or not self.cost_col:
            return pd.DataFrame()
        self.df['year_month'] = self.df[self.date_col].dt.to_period('M')
        monthly = self.df.groupby('year_month')[self.cost_col].sum().reset_index()
        monthly.columns = ['Month', 'Total Cost']
        return monthly

    def mom_growth(self) -> pd.DataFrame:
        """Month-over-month growth percentage."""
        monthly = self.monthly_spend()
        if monthly.empty:
            return pd.DataFrame()
        monthly['MoM Growth %'] = monthly['Total Cost'].pct_change() * 100
        monthly['MoM Growth %'] = monthly['MoM Growth %'].round(2)
        return monthly

    def cost_by_service(self, top_n: int = 10) -> pd.DataFrame:
        """Cost breakdown by service."""
        service_cols = [c for c in self.df.columns if 'service' in c.lower() or 'product' in c.lower()]
        if not service_cols or not self.cost_col:
            return pd.DataFrame()
        svc = service_cols[0]
        result = self.df.groupby(svc)[self.cost_col].sum().reset_index()
        result.columns = ['Service', 'Total Cost']
        result = result.sort_values('Total Cost', ascending=False).head(top_n)
        result['Total Cost'] = result['Total Cost'].round(2)
        result['% of Total'] = (result['Total Cost'] / self.total_spend() * 100).round(2)
        return result

    def cost_by_region(self, top_n: int = 10) -> pd.DataFrame:
        """Cost breakdown by region."""
        region_cols = [c for c in self.df.columns if 'region' in c.lower() or 'zone' in c.lower()]
        if not region_cols or not self.cost_col:
            return pd.DataFrame()
        reg = region_cols[0]
        result = self.df.groupby(reg)[self.cost_col].sum().reset_index()
        result.columns = ['Region', 'Total Cost']
        result = result.sort_values('Total Cost', ascending=False).head(top_n)
        result['Total Cost'] = result['Total Cost'].round(2)
        return result

    def cost_by_account(self) -> pd.DataFrame:
        """Cost breakdown by account."""
        acct_cols = [c for c in self.df.columns if 'account' in c.lower() or 'subscription' in c.lower()]
        if not acct_cols or not self.cost_col:
            return pd.DataFrame()
        acct = acct_cols[0]
        result = self.df.groupby(acct)[self.cost_col].sum().reset_index()
        result.columns = ['Account', 'Total Cost']
        result = result.sort_values('Total Cost', ascending=False)
        result['Total Cost'] = result['Total Cost'].round(2)
        return result

    def daily_trend(self) -> pd.DataFrame:
        """Daily cost trend for time series analysis."""
        if not self.date_col or not self.cost_col:
            return pd.DataFrame()
        daily = self.df.groupby(self.date_col)[self.cost_col].sum().reset_index()
        daily.columns = ['Date', 'Daily Cost']
        daily = daily.sort_values('Date')
        return daily

    def weekly_trend(self) -> pd.DataFrame:
        """Weekly aggregated cost trend."""
        if not self.date_col or not self.cost_col:
            return pd.DataFrame()
        self.df['week'] = self.df[self.date_col].dt.to_period('W')
        weekly = self.df.groupby('week')[self.cost_col].sum().reset_index()
        weekly.columns = ['Week', 'Weekly Cost']
        return weekly

    def cost_per_unit(self) -> pd.DataFrame:
        """Cost efficiency: cost per usage unit where available."""
        usage_cols = [c for c in self.df.columns if 'usage' in c.lower() or 'quantity' in c.lower() or 'consumption' in c.lower()]
        service_cols = [c for c in self.df.columns if 'service' in c.lower() or 'product' in c.lower()]
        if not usage_cols or not service_cols or not self.cost_col:
            return pd.DataFrame()
        usage = usage_cols[0]
        svc = service_cols[0]
        grouped = self.df.groupby(svc).agg({self.cost_col: 'sum', usage: 'sum'}).reset_index()
        grouped['Cost Per Unit'] = (grouped[self.cost_col] / grouped[usage]).round(4)
        grouped = grouped.sort_values(self.cost_col, ascending=False)
        return grouped

    def summary(self) -> Dict[str, Any]:
        """Generate complete KPI summary."""
        monthly = self.monthly_spend()
        return {
            'total_spend': self.total_spend(),
            'average_daily_cost': self.average_daily_cost(),
            'total_records': len(self.df),
            'date_range': f"{self.df[self.date_col].min()} to {self.df[self.date_col].max()}" if self.date_col else "N/A",
            'monthly_spend': monthly.to_dict('records') if not monthly.empty else [],
            'top_services': self.cost_by_service(5).to_dict('records'),
            'top_regions': self.cost_by_region(5).to_dict('records'),
            'mom_growth': self.mom_growth().to_dict('records') if not self.mom_growth().empty else []
        }
