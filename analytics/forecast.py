"""
Forecasting Module
Predicts future cloud costs using multiple methods.
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from typing import Dict, Any
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os


class CostForecaster:
    """Forecasts future cloud costs."""

    def __init__(self, df: pd.DataFrame, output_dir: str = 'output/charts'):
        self.df = df.copy()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        date_cols = [c for c in self.df.columns if 'date' in c.lower()]
        self.date_col = date_cols[0] if date_cols else None
        if self.date_col:
            self.df[self.date_col] = pd.to_datetime(self.df[self.date_col], errors='coerce')

        cost_cols = [c for c in self.df.columns if 'cost' in c.lower() or 'amount' in c.lower()]
        self.cost_col = cost_cols[0] if cost_cols else None

        self.daily = None
        if self.date_col and self.cost_col:
            self.daily = self.df.groupby(self.date_col)[self.cost_col].sum().reset_index()
            self.daily = self.daily.sort_values(self.date_col)

    def moving_average_forecast(self, window: int = 7, periods: int = 30) -> pd.DataFrame:
        """Simple moving average forecast."""
        if self.daily is None:
            return pd.DataFrame()
        last_date = self.daily[self.date_col].max()
        dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods)
        ma = self.daily[self.cost_col].rolling(window=window).mean().iloc[-1]
        forecast = pd.DataFrame({
            'Date': dates,
            'Forecast': ma,
            'Method': 'Moving Average'
        })
        return forecast

    def linear_trend_forecast(self, periods: int = 30) -> pd.DataFrame:
        """Linear regression trend forecast."""
        if self.daily is None:
            return pd.DataFrame()
        self.daily['day_num'] = range(len(self.daily))
        X = self.daily['day_num'].values.reshape(-1, 1)
        y = self.daily[self.cost_col].values
        model = LinearRegression()
        model.fit(X, y)

        last_date = self.daily[self.date_col].max()
        dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods)
        future_X = np.arange(len(self.daily), len(self.daily) + periods).reshape(-1, 1)
        predictions = model.predict(future_X)
        predictions = np.maximum(predictions, 0)

        forecast = pd.DataFrame({
            'Date': dates,
            'Forecast': predictions,
            'Method': 'Linear Trend'
        })
        return forecast

    def exponential_smoothing_forecast(self, alpha: float = 0.3, periods: int = 30) -> pd.DataFrame:
        """Simple exponential smoothing forecast."""
        if self.daily is None:
            return pd.DataFrame()
        values = self.daily[self.cost_col].values
        smoothed = [values[0]]
        for v in values[1:]:
            smoothed.append(alpha * v + (1 - alpha) * smoothed[-1])
        last_smooth = smoothed[-1]
        last_date = self.daily[self.date_col].max()
        dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=periods)
        forecast = pd.DataFrame({
            'Date': dates,
            'Forecast': last_smooth,
            'Method': 'Exponential Smoothing'
        })
        return forecast

    def plot_forecast(self, forecast: pd.DataFrame, title: str):
        """Plot historical data with forecast."""
        if forecast.empty or self.daily is None:
            return
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(self.daily[self.date_col], self.daily[self.cost_col],
               color='#2E86AB', label='Historical', alpha=0.7)
        ax.plot(forecast['Date'], forecast['Forecast'],
               color='#C73E1D', linestyle='--', label='Forecast')
        ax.fill_between(forecast['Date'], forecast['Forecast'] * 0.9,
                       forecast['Forecast'] * 1.1, alpha=0.2, color='#C73E1D')
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Cost ($)')
        ax.legend()
        plt.xticks(rotation=45)
        path = os.path.join(self.output_dir, f'forecast_{title.lower().replace(" ", "_")}.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def run_all(self) -> Dict[str, Any]:
        """Run all forecasting methods."""
        print("\nRunning forecasts...")

        ma = self.moving_average_forecast()
        self.plot_forecast(ma, 'Moving Average Forecast')

        lt = self.linear_trend_forecast()
        self.plot_forecast(lt, 'Linear Trend Forecast')

        es = self.exponential_smoothing_forecast()
        self.plot_forecast(es, 'Exponential Smoothing Forecast')

        # Calculate 30-day projections
        next_30d = ma.head(30)['Forecast'].sum() if not ma.empty else 0

        return {
            'forecast_30d_total': round(next_30d, 2),
            'forecast_30d_daily_avg': round(next_30d / 30, 2) if next_30d > 0 else 0,
            'moving_avg_next_7d': round(ma.head(7)['Forecast'].sum(), 2) if not ma.empty else 0,
            'linear_trend_next_7d': round(lt.head(7)['Forecast'].sum(), 2) if not lt.empty else 0
        }
