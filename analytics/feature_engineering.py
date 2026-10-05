"""
Feature Engineering Module
Creates ML-ready features from raw cloud cost data.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Tuple, List


class FeatureEngineer:
    """Engineers features for ML models."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.encoders = {}
        self.scaler = StandardScaler()
        self.feature_cols = []
        self.target_col = None

    def create_time_features(self) -> 'FeatureEngineer':
        """Create time-based features."""
        date_cols = [c for c in self.df.columns if 'date' in c.lower()]
        if not date_cols:
            return self

        date_col = date_cols[0]
        self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')

        self.df['day_of_week'] = self.df[date_col].dt.dayofweek
        self.df['month'] = self.df[date_col].dt.month
        self.df['day_of_month'] = self.df[date_col].dt.day
        self.df['week_of_year'] = self.df[date_col].dt.isocalendar().week.astype(int)
        self.df['is_weekend'] = (self.df['day_of_week'] >= 5).astype(int)
        self.df['is_month_start'] = self.df[date_col].dt.is_month_start.astype(int)
        self.df['is_month_end'] = self.df[date_col].dt.is_month_end.astype(int)

        # Cyclical encoding
        self.df['day_of_week_sin'] = np.sin(2 * np.pi * self.df['day_of_week'] / 7)
        self.df['day_of_week_cos'] = np.cos(2 * np.pi * self.df['day_of_week'] / 7)
        self.df['month_sin'] = np.sin(2 * np.pi * self.df['month'] / 12)
        self.df['month_cos'] = np.cos(2 * np.pi * self.df['month'] / 12)

        return self

    def create_cost_features(self) -> 'FeatureEngineer':
        """Create cost-based features."""
        cost_cols = [c for c in self.df.columns if 'cost' in c.lower() or 'amount' in c.lower()]
        if not cost_cols:
            return self

        cost_col = cost_cols[0]
        self.target_col = cost_col

        # Log transform
        self.df['cost_log'] = np.log1p(self.df[cost_col])

        # Z-score
        self.df['cost_zscore'] = (self.df[cost_col] - self.df[cost_col].mean()) / self.df[cost_col].std()

        # Percentile
        self.df['cost_percentile'] = self.df[cost_col].rank(pct=True)

        # Rolling statistics
        self.df = self.df.sort_values(by=[c for c in self.df.columns if 'date' in c.lower()][0] if any('date' in c.lower() for c in self.df.columns) else self.df.columns[0])
        self.df['cost_7d_avg'] = self.df[cost_col].rolling(7, min_periods=1).mean()
        self.df['cost_7d_std'] = self.df[cost_col].rolling(7, min_periods=1).std().fillna(0)
        self.df['cost_7d_min'] = self.df[cost_col].rolling(7, min_periods=1).min()
        self.df['cost_7d_max'] = self.df[cost_col].rolling(7, min_periods=1).max()
        self.df['cost_diff_7d'] = self.df[cost_col] - self.df['cost_7d_avg']
        self.df['cost_pct_change'] = self.df[cost_col].pct_change().fillna(0)

        # Lag features
        self.df['cost_lag_1d'] = self.df[cost_col].shift(1).fillna(0)
        self.df['cost_lag_7d'] = self.df[cost_col].shift(7).fillna(0)

        return self

    def create_categorical_features(self) -> 'FeatureEngineer':
        """Encode categorical features."""
        date_cols = [c for c in self.df.columns if 'date' in c.lower()]
        date_col = date_cols[0] if date_cols else None

        cat_cols = []
        for c in self.df.columns:
            if self.df[c].dtype == 'object' and c != date_col:
                cat_cols.append(c)

        for col in cat_cols:
            if col in self.df.columns:
                le = LabelEncoder()
                self.df[f'{col}_encoded'] = le.fit_transform(self.df[col].astype(str))
                self.encoders[col] = le

        return self

    def create_interaction_features(self) -> 'FeatureEngineer':
        """Create interaction features between important columns."""
        service_cols = [c for c in self.df.columns if 'service' in c.lower() or 'product' in c.lower()]
        region_cols = [c for c in self.df.columns if 'region' in c.lower()]
        cost_cols = [c for c in self.df.columns if 'cost' in c.lower() or 'amount' in c.lower()]

        if service_cols and cost_cols:
            svc = service_cols[0]
            cost = cost_cols[0]
            # Average cost by service
            svc_avg = self.df.groupby(svc)[cost].transform('mean')
            self.df['cost_vs_svc_avg'] = self.df[cost] - svc_avg

        if region_cols and cost_cols:
            reg = region_cols[0]
            cost = cost_cols[0]
            # Average cost by region
            reg_avg = self.df.groupby(reg)[cost].transform('mean')
            self.df['cost_vs_reg_avg'] = self.df[cost] - reg_avg

        return self

    def get_feature_columns(self) -> List[str]:
        """Get list of feature columns for ML model."""
        exclude = [c for c in self.df.columns if 'date' in c.lower() or self.df[c].dtype == 'object']
        if self.target_col:
            exclude.append(self.target_col)
        self.feature_cols = [c for c in self.df.columns if c not in exclude]
        return self.feature_cols

    def prepare_ml_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare final X, y for ML model."""
        self.create_time_features()
        self.create_cost_features()
        self.create_categorical_features()
        self.create_interaction_features()

        feature_cols = self.get_feature_columns()
        X = self.df[feature_cols].fillna(0)
        y = self.df[self.target_col] if self.target_col else None

        return X, y

    def get_feature_importance_names(self) -> List[str]:
        """Get human-readable feature names."""
        feature_names = {
            'day_of_week': 'Day of Week',
            'month': 'Month',
            'is_weekend': 'Is Weekend',
            'cost_7d_avg': '7-Day Average Cost',
            'cost_7d_std': '7-Day Cost Volatility',
            'cost_diff_7d': 'Cost Deviation from 7-Day Avg',
            'cost_lag_1d': 'Previous Day Cost',
            'cost_lag_7d': 'Cost 7 Days Ago',
            'cost_zscore': 'Cost Z-Score',
            'cost_log': 'Log Cost',
        }
        return [feature_names.get(c, c) for c in self.feature_cols]
