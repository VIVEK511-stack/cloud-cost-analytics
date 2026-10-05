"""
Anomaly Detection Module
Identifies unusual spending patterns using statistical methods.
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import List, Dict, Any
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import os


class AnomalyDetector:
    """Detects anomalous cloud spending."""

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

    def detect_zscore(self, threshold: float = 2.5) -> pd.DataFrame:
        """Z-score based anomaly detection on daily costs."""
        if not self.date_col or not self.cost_col:
            return pd.DataFrame()
        daily = self.df.groupby(self.date_col)[self.cost_col].sum().reset_index()
        daily['zscore'] = np.abs(stats.zscore(daily[self.cost_col]))
        daily['is_anomaly'] = daily['zscore'] > threshold
        daily['threshold'] = daily[self.cost_col].mean() + threshold * daily[self.cost_col].std()
        return daily[daily['is_anomaly']]

    def detect_iqr(self) -> pd.DataFrame:
        """IQR based anomaly detection."""
        if not self.date_col or not self.cost_col:
            return pd.DataFrame()
        daily = self.df.groupby(self.date_col)[self.cost_col].sum().reset_index()
        q1 = daily[self.cost_col].quantile(0.25)
        q3 = daily[self.cost_col].quantile(0.75)
        iqr = q3 - q1
        upper = q3 + 1.5 * iqr
        lower = q1 - 1.5 * iqr
        anomalies = daily[(daily[self.cost_col] > upper) | (daily[self.cost_col] < lower)]
        return anomalies

    def detect_rolling(self, window: int = 7, threshold_mult: float = 2.0) -> pd.DataFrame:
        """Rolling mean deviation anomaly detection."""
        if not self.date_col or not self.cost_col:
            return pd.DataFrame()
        daily = self.df.groupby(self.date_col)[self.cost_col].sum().reset_index()
        daily['rolling_mean'] = daily[self.cost_col].rolling(window=window, min_periods=1).mean()
        daily['rolling_std'] = daily[self.cost_col].rolling(window=window, min_periods=1).std()
        daily['upper_bound'] = daily['rolling_mean'] + threshold_mult * daily['rolling_std']
        daily['is_anomaly'] = daily[self.cost_col] > daily['upper_bound']
        return daily[daily['is_anomaly']]

    def plot_anomalies(self, anomalies: pd.DataFrame, method_name: str):
        """Plot anomalies on daily cost chart."""
        if anomalies.empty or not self.date_col or not self.cost_col:
            return
        daily = self.df.groupby(self.date_col)[self.cost_col].sum().reset_index()
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(daily[self.date_col], daily[self.cost_col], color='#2E86AB', alpha=0.7, label='Daily Cost')
        ax.scatter(anomalies[self.date_col], anomalies[self.cost_col],
                  color='red', s=100, zorder=5, label='Anomaly')
        ax.set_title(f'Anomaly Detection ({method_name})', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Cost ($)')
        ax.legend()
        plt.xticks(rotation=45)
        path = os.path.join(self.output_dir, f'anomalies_{method_name.lower()}.png')
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def run_all(self) -> Dict[str, Any]:
        """Run all anomaly detection methods."""
        print("\nRunning anomaly detection...")

        zscore_anomalies = self.detect_zscore()
        self.plot_anomalies(zscore_anomalies, 'ZScore')

        iqr_anomalies = self.detect_iqr()
        self.plot_anomalies(iqr_anomalies, 'IQR')

        rolling_anomalies = self.detect_rolling()
        self.plot_anomalies(rolling_anomalies, 'Rolling')

        return {
            'zscore_count': len(zscore_anomalies),
            'iqr_count': len(iqr_anomalies),
            'rolling_count': len(rolling_anomalies),
            'zscore_dates': zscore_anomalies[self.date_col].dt.strftime('%Y-%m-%d').tolist() if not zscore_anomalies.empty else [],
            'anomalous_days_total': len(set(
                zscore_anomalies[self.date_col].tolist() +
                iqr_anomalies[self.date_col].tolist() +
                rolling_anomalies[self.date_col].tolist()
            )) if not (zscore_anomalies.empty and iqr_anomalies.empty and rolling_anomalies.empty) else 0
        }
