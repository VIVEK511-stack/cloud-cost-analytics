"""
Forecasting Module (MySQL)
Estimates month-end cloud expenditure using transparent forecasting methods.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from warehouse.connection import WarehouseConnection

logger = logging.getLogger(__name__)


@dataclass
class ForecastResult:
    """Stores a single forecast result."""
    period_start: date
    period_end: date
    forecast_amount: float
    currency: str
    method: str
    confidence_low: float
    confidence_high: float
    actual_to_date: float
    days_elapsed: int
    days_remaining: int


class CostForecaster:
    """
    Forecasts month-end cloud expenditure.

    Supported methods:
    - run_rate: Projects current daily average to end of period
    - historical_average: Uses historical daily averages for same period
    - linear_trend: Linear regression on historical daily costs
    """

    def __init__(self, warehouse: WarehouseConnection,
                 method: str = 'run_rate',
                 projection_days: int = 30):
        self.warehouse = warehouse
        self.method = method
        self.projection_days = projection_days

    def fetch_current_month_costs(self) -> pd.DataFrame:
        """Fetch current month daily costs."""
        query = """
            SELECT
                d.full_date,
                d.day,
                a.account_name,
                t.team_name,
                p.project_name,
                SUM(fc.cost) AS daily_cost
            FROM fact_cloud_cost fc
            JOIN dim_date d ON fc.date_id = d.date_id
            JOIN dim_account a ON fc.account_id = a.account_id
            JOIN dim_team t ON fc.team_id = t.team_id
            JOIN dim_project p ON fc.project_id = p.project_id
            WHERE d.full_date >= DATE_FORMAT(CURDATE(), '%%Y-%%m-01')
              AND d.full_date < CURDATE()
            GROUP BY d.full_date, d.day, a.account_name, t.team_name, p.project_name
            ORDER BY d.full_date
        """
        rows = self.warehouse.fetch_all(query)
        return pd.DataFrame(rows)

    def fetch_historical_costs(self, months_back: int = 6) -> pd.DataFrame:
        """Fetch historical daily costs for trend analysis."""
        query = f"""
            SELECT
                d.full_date,
                d.year,
                d.month,
                d.day,
                a.account_name,
                t.team_name,
                p.project_name,
                SUM(fc.cost) AS daily_cost
            FROM fact_cloud_cost fc
            JOIN dim_date d ON fc.date_id = d.date_id
            JOIN dim_account a ON fc.account_id = a.account_id
            JOIN dim_team t ON fc.team_id = t.team_id
            JOIN dim_project p ON fc.project_id = p.project_id
            WHERE d.full_date >= DATE_SUB(CURDATE(), INTERVAL {months_back} MONTH)
            GROUP BY d.full_date, d.year, d.month, d.day,
                     a.account_name, t.team_name, p.project_name
            ORDER BY d.full_date
        """
        rows = self.warehouse.fetch_all(query)
        return pd.DataFrame(rows)

    def forecast_run_rate(self, current_df: pd.DataFrame,
                          historical_df: pd.DataFrame = None) -> List[ForecastResult]:
        """Run-rate projection: current daily average * days in month."""
        forecasts = []

        if current_df.empty:
            return forecasts

        today = date.today()
        days_in_month = self._days_in_month(today.year, today.month)
        days_elapsed = today.day
        days_remaining = days_in_month - days_elapsed

        grouped = current_df.groupby(['account_name', 'team_name', 'project_name'])

        for (account, team, project), group in grouped:
            actual_to_date = group['daily_cost'].sum()
            daily_avg = actual_to_date / days_elapsed if days_elapsed > 0 else 0

            forecast_amount = actual_to_date + (daily_avg * days_remaining)

            if historical_df is not None and not historical_df.empty:
                hist_group = historical_df[
                    (historical_df['account_name'] == account) &
                    (historical_df['team_name'] == team) &
                    (historical_df['project_name'] == project)
                ]
                if not hist_group.empty:
                    daily_std = hist_group['daily_cost'].std()
                    margin = daily_std * np.sqrt(days_remaining) * 1.96
                    confidence_low = max(0, forecast_amount - margin)
                    confidence_high = forecast_amount + margin
                else:
                    confidence_low = forecast_amount * 0.8
                    confidence_high = forecast_amount * 1.2
            else:
                confidence_low = forecast_amount * 0.8
                confidence_high = forecast_amount * 1.2

            forecasts.append(ForecastResult(
                period_start=date(today.year, today.month, 1),
                period_end=date(today.year, today.month, days_in_month),
                forecast_amount=round(forecast_amount, 2),
                currency='USD',
                method='run_rate',
                confidence_low=round(confidence_low, 2),
                confidence_high=round(confidence_high, 2),
                actual_to_date=round(actual_to_date, 2),
                days_elapsed=days_elapsed,
                days_remaining=days_remaining
            ))

        return forecasts

    def forecast_historical_average(self, current_df: pd.DataFrame,
                                     historical_df: pd.DataFrame) -> List[ForecastResult]:
        """Historical average: uses average daily cost from previous months."""
        forecasts = []

        if current_df.empty or historical_df.empty:
            return forecasts

        today = date.today()
        days_in_month = self._days_in_month(today.year, today.month)
        days_elapsed = today.day
        days_remaining = days_in_month - days_elapsed

        grouped = current_df.groupby(['account_name', 'team_name', 'project_name'])

        for (account, team, project), group in grouped:
            actual_to_date = group['daily_cost'].sum()

            hist_group = historical_df[
                (historical_df['account_name'] == account) &
                (historical_df['team_name'] == team) &
                (historical_df['project_name'] == project) &
                (historical_df['day'] <= days_elapsed)
            ]

            if hist_group.empty:
                daily_avg = actual_to_date / days_elapsed if days_elapsed > 0 else 0
            else:
                hist_daily_avg = hist_group.groupby('full_date')['daily_cost'].sum().mean()
                current_daily_avg = actual_to_date / days_elapsed if days_elapsed > 0 else 0
                daily_avg = 0.7 * current_daily_avg + 0.3 * hist_daily_avg

            forecast_amount = actual_to_date + (daily_avg * days_remaining)

            if not hist_group.empty:
                hist_std = hist_group.groupby('full_date')['daily_cost'].sum().std()
                margin = hist_std * np.sqrt(days_remaining) * 1.96
                confidence_low = max(0, forecast_amount - margin)
                confidence_high = forecast_amount + margin
            else:
                confidence_low = forecast_amount * 0.8
                confidence_high = forecast_amount * 1.2

            forecasts.append(ForecastResult(
                period_start=date(today.year, today.month, 1),
                period_end=date(today.year, today.month, days_in_month),
                forecast_amount=round(forecast_amount, 2),
                currency='USD',
                method='historical_average',
                confidence_low=round(confidence_low, 2),
                confidence_high=round(confidence_high, 2),
                actual_to_date=round(actual_to_date, 2),
                days_elapsed=days_elapsed,
                days_remaining=days_remaining
            ))

        return forecasts

    def forecast_linear_trend(self, current_df: pd.DataFrame,
                              historical_df: pd.DataFrame) -> List[ForecastResult]:
        """Linear trend: fits a linear regression on historical daily costs."""
        forecasts = []

        if current_df.empty or historical_df.empty:
            return forecasts

        today = date.today()
        days_in_month = self._days_in_month(today.year, today.month)
        days_elapsed = today.day
        days_remaining = days_in_month - days_elapsed

        grouped = current_df.groupby(['account_name', 'team_name', 'project_name'])

        for (account, team, project), group in grouped:
            actual_to_date = group['daily_cost'].sum()

            hist_group = historical_df[
                (historical_df['account_name'] == account) &
                (historical_df['team_name'] == team) &
                (historical_df['project_name'] == project)
            ]

            if len(hist_group) < 7:
                daily_avg = actual_to_date / days_elapsed if days_elapsed > 0 else 0
                forecast_amount = actual_to_date + (daily_avg * days_remaining)
                confidence_low = forecast_amount * 0.8
                confidence_high = forecast_amount * 1.2
            else:
                daily_totals = hist_group.groupby('full_date')['daily_cost'].sum().reset_index()
                daily_totals['day_num'] = range(len(daily_totals))

                x = daily_totals['day_num'].values
                y = daily_totals['daily_cost'].values

                n = len(x)
                slope = (n * np.sum(x * y) - np.sum(x) * np.sum(y)) / (n * np.sum(x**2) - np.sum(x)**2)
                intercept = (np.sum(y) - slope * np.sum(x)) / n

                future_x = np.arange(n, n + days_remaining)
                projected_daily = slope * future_x + intercept
                projected_daily = np.maximum(projected_daily, 0)

                forecast_amount = actual_to_date + projected_daily.sum()

                residuals = y - (slope * x + intercept)
                mse = np.mean(residuals**2)
                margin = np.sqrt(mse * days_remaining) * 1.96
                confidence_low = max(0, forecast_amount - margin)
                confidence_high = forecast_amount + margin

            forecasts.append(ForecastResult(
                period_start=date(today.year, today.month, 1),
                period_end=date(today.year, today.month, days_in_month),
                forecast_amount=round(forecast_amount, 2),
                currency='USD',
                method='linear_trend',
                confidence_low=round(confidence_low, 2),
                confidence_high=round(confidence_high, 2),
                actual_to_date=round(actual_to_date, 2),
                days_elapsed=days_elapsed,
                days_remaining=days_remaining
            ))

        return forecasts

    def _days_in_month(self, year: int, month: int) -> int:
        """Get number of days in a month."""
        if month == 12:
            return 31
        return (date(year, month + 1, 1) - date(year, month, 1)).days

    def run_forecast(self) -> List[ForecastResult]:
        """Run forecasting using the configured method."""
        logger.info(f"Running forecast: method={self.method}")

        current_df = self.fetch_current_month_costs()
        historical_df = self.fetch_historical_costs()

        if current_df.empty:
            logger.warning("No current month data available for forecasting")
            return []

        if self.method == 'run_rate':
            forecasts = self.forecast_run_rate(current_df, historical_df)
        elif self.method == 'historical_average':
            forecasts = self.forecast_historical_average(current_df, historical_df)
        elif self.method == 'linear_trend':
            forecasts = self.forecast_linear_trend(current_df, historical_df)
        else:
            logger.error(f"Unknown forecast method: {self.method}")
            return []

        logger.info(f"Generated {len(forecasts)} forecasts using {self.method}")
        return forecasts

    def save_forecasts(self, forecasts: List[ForecastResult]) -> int:
        """Save forecast results to the warehouse."""
        if not forecasts:
            return 0

        rows = []
        for f in forecasts:
            rows.append((
                datetime.now(), None, None, None,
                f.period_start, f.period_end,
                f.forecast_amount, f.currency, f.method,
                f.confidence_low, f.confidence_high,
                None, None
            ))

        query = """
            INSERT INTO fact_forecasts
            (forecast_date, account_id, team_id, project_id,
             period_start, period_end, forecast_amount, currency,
             method, confidence_low, confidence_high,
             actual_amount, accuracy_pct)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        count = self.warehouse.execute_many(query, rows)
        logger.info(f"Saved {count} forecasts to warehouse")
        return count

    def get_forecast_summary(self, forecasts: List[ForecastResult]) -> Dict[str, Any]:
        """Generate a summary of forecasts."""
        if not forecasts:
            return {'total_forecasts': 0}

        total_forecast = sum(f.forecast_amount for f in forecasts)
        total_actual = sum(f.actual_to_date for f in forecasts)

        return {
            'total_forecasts': len(forecasts),
            'method': self.method,
            'total_forecast_amount': round(total_forecast, 2),
            'total_actual_to_date': round(total_actual, 2),
            'total_projected_remaining': round(total_forecast - total_actual, 2),
            'avg_confidence_range': round(
                np.mean([f.confidence_high - f.confidence_low for f in forecasts]), 2
            ) if forecasts else 0,
            'forecast_timestamp': datetime.now().isoformat()
        }
