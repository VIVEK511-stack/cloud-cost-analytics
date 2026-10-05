"""
Anomaly Detection Module (MySQL)
Flags unusual cloud spending patterns using configurable thresholds and statistical methods.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from scipy import stats
from warehouse.connection import WarehouseConnection

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    """Stores a single anomaly detection result."""
    date_id: int
    full_date: str
    account_name: str
    service_name: str
    region_name: str
    team_name: str
    project_name: str
    actual_cost: float
    expected_cost: float
    deviation_pct: float
    severity: str
    detection_method: str
    reason: str


class AnomalyDetector:
    """
    Detects anomalous cloud spending using multiple methods.

    Supported methods:
    - rolling_mean: Deviation from rolling mean by threshold multiplier
    - zscore: Z-score based detection
    - iqr: Interquartile range based detection
    """

    def __init__(self, warehouse: WarehouseConnection,
                 method: str = 'rolling_mean',
                 threshold_std: float = 2.0,
                 threshold_multiplier: float = 1.5,
                 rolling_window_days: int = 30,
                 min_history_days: int = 7):
        self.warehouse = warehouse
        self.method = method
        self.threshold_std = threshold_std
        self.threshold_multiplier = threshold_multiplier
        self.rolling_window_days = rolling_window_days
        self.min_history_days = min_history_days

    def fetch_daily_costs(self, days_back: int = 90) -> pd.DataFrame:
        """Fetch daily cost aggregated data from the warehouse."""
        query = f"""
            SELECT
                d.date_id,
                d.full_date,
                a.account_name,
                s.service_name,
                r.region_name,
                t.team_name,
                p.project_name,
                SUM(fc.cost) AS daily_cost
            FROM fact_cloud_cost fc
            JOIN dim_date d ON fc.date_id = d.date_id
            JOIN dim_account a ON fc.account_id = a.account_id
            JOIN dim_service s ON fc.service_id = s.service_id
            JOIN dim_region r ON fc.region_id = r.region_id
            JOIN dim_team t ON fc.team_id = t.team_id
            JOIN dim_project p ON fc.project_id = p.project_id
            WHERE d.full_date >= DATE_SUB(CURDATE(), INTERVAL {days_back} DAY)
            GROUP BY d.date_id, d.full_date, a.account_name, s.service_name,
                     r.region_name, t.team_name, p.project_name
            ORDER BY d.full_date
        """
        rows = self.warehouse.fetch_all(query)
        return pd.DataFrame(rows)

    def detect_rolling_mean(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """
        Detect anomalies using rolling mean deviation.
        """
        anomalies = []

        grouped = df.groupby(['service_name', 'team_name'])

        for (service, team), group in grouped:
            group = group.sort_values('full_date').copy()

            if len(group) < self.min_history_days:
                continue

            group['rolling_mean'] = group['daily_cost'].rolling(
                window=self.rolling_window_days, min_periods=self.min_history_days
            ).mean()
            group['rolling_std'] = group['daily_cost'].rolling(
                window=self.rolling_window_days, min_periods=self.min_history_days
            ).std()

            for idx, row in group.iterrows():
                if pd.isna(row['rolling_mean']) or pd.isna(row['rolling_std']):
                    continue

                threshold = row['rolling_mean'] + (self.threshold_multiplier * row['rolling_std'])

                if row['daily_cost'] > threshold and row['daily_cost'] > 0:
                    deviation_pct = ((row['daily_cost'] - row['rolling_mean'])
                                    / row['rolling_mean'] * 100) if row['rolling_mean'] > 0 else 0

                    severity = self._classify_severity(deviation_pct)

                    anomalies.append(AnomalyResult(
                        date_id=row['date_id'],
                        full_date=str(row['full_date']),
                        account_name=row['account_name'],
                        service_name=service,
                        region_name=row['region_name'],
                        team_name=team,
                        project_name=row['project_name'],
                        actual_cost=round(row['daily_cost'], 2),
                        expected_cost=round(row['rolling_mean'], 2),
                        deviation_pct=round(deviation_pct, 2),
                        severity=severity,
                        detection_method='rolling_mean',
                        reason=(f"Cost ${row['daily_cost']:.2f} exceeds rolling mean "
                               f"${row['rolling_mean']:.2f} by {deviation_pct:.1f}% "
                               f"(threshold: {self.threshold_multiplier}x std)")
                    ))

        return anomalies

    def detect_zscore(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies using Z-score method."""
        anomalies = []

        grouped = df.groupby(['service_name', 'team_name'])

        for (service, team), group in grouped:
            group = group.sort_values('full_date').copy()

            if len(group) < self.min_history_days:
                continue

            mean = group['daily_cost'].mean()
            std = group['daily_cost'].std()

            if std == 0:
                continue

            group['zscore'] = np.abs(stats.zscore(group['daily_cost']))

            for idx, row in group.iterrows():
                if row['zscore'] > self.threshold_std:
                    deviation_pct = ((row['daily_cost'] - mean) / mean * 100) if mean > 0 else 0
                    severity = self._classify_severity(deviation_pct)

                    anomalies.append(AnomalyResult(
                        date_id=row['date_id'],
                        full_date=str(row['full_date']),
                        account_name=row['account_name'],
                        service_name=service,
                        region_name=row['region_name'],
                        team_name=team,
                        project_name=row['project_name'],
                        actual_cost=round(row['daily_cost'], 2),
                        expected_cost=round(mean, 2),
                        deviation_pct=round(deviation_pct, 2),
                        severity=severity,
                        detection_method='zscore',
                        reason=(f"Z-score {row['zscore']:.2f} exceeds threshold "
                               f"{self.threshold_std}. Cost ${row['daily_cost']:.2f} "
                               f"vs mean ${mean:.2f}")
                    ))

        return anomalies

    def detect_iqr(self, df: pd.DataFrame) -> List[AnomalyResult]:
        """Detect anomalies using Interquartile Range (IQR) method."""
        anomalies = []

        grouped = df.groupby(['service_name', 'team_name'])

        for (service, team), group in grouped:
            group = group.sort_values('full_date').copy()

            if len(group) < self.min_history_days:
                continue

            q1 = group['daily_cost'].quantile(0.25)
            q3 = group['daily_cost'].quantile(0.75)
            iqr = q3 - q1
            upper_bound = q3 + (1.5 * iqr)

            for idx, row in group.iterrows():
                if row['daily_cost'] > upper_bound:
                    deviation_pct = ((row['daily_cost'] - q3) / q3 * 100) if q3 > 0 else 0
                    severity = self._classify_severity(deviation_pct)

                    anomalies.append(AnomalyResult(
                        date_id=row['date_id'],
                        full_date=str(row['full_date']),
                        account_name=row['account_name'],
                        service_name=service,
                        region_name=row['region_name'],
                        team_name=team,
                        project_name=row['project_name'],
                        actual_cost=round(row['daily_cost'], 2),
                        expected_cost=round(q3, 2),
                        deviation_pct=round(deviation_pct, 2),
                        severity=severity,
                        detection_method='iqr',
                        reason=(f"Cost ${row['daily_cost']:.2f} exceeds IQR upper bound "
                               f"${upper_bound:.2f} (Q3: ${q3:.2f})")
                    ))

        return anomalies

    def _classify_severity(self, deviation_pct: float) -> str:
        """Classify anomaly severity based on deviation percentage."""
        abs_dev = abs(deviation_pct)
        if abs_dev >= 100:
            return 'Critical'
        elif abs_dev >= 50:
            return 'High'
        elif abs_dev >= 25:
            return 'Medium'
        else:
            return 'Low'

    def run_detection(self, days_back: int = 90) -> List[AnomalyResult]:
        """Run anomaly detection using the configured method."""
        logger.info(f"Running anomaly detection: method={self.method}, days_back={days_back}")

        df = self.fetch_daily_costs(days_back)
        if df.empty:
            logger.warning("No data available for anomaly detection")
            return []

        if self.method == 'rolling_mean':
            anomalies = self.detect_rolling_mean(df)
        elif self.method == 'zscore':
            anomalies = self.detect_zscore(df)
        elif self.method == 'iqr':
            anomalies = self.detect_iqr(df)
        else:
            logger.error(f"Unknown detection method: {self.method}")
            return []

        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        anomalies.sort(key=lambda a: (severity_order.get(a.severity, 99), -abs(a.deviation_pct)))

        logger.info(f"Detected {len(anomalies)} anomalies using {self.method}")
        return anomalies

    def save_anomalies(self, anomalies: List[AnomalyResult],
                       batch_size: int = 500) -> int:
        """Save detected anomalies to the warehouse."""
        if not anomalies:
            return 0

        rows = []
        for a in anomalies:
            rows.append((
                datetime.now(), a.date_id, None, None, None, None, None,
                a.actual_cost, a.expected_cost, a.deviation_pct,
                a.severity, a.detection_method, a.reason, False
            ))

        query = """
            INSERT INTO fact_anomalies
            (detection_date, date_id, account_id, service_id, region_id,
             team_id, project_id, actual_cost, expected_cost, deviation_pct,
             severity, detection_method, reason, is_acknowledged)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        total_saved = 0
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            total_saved += self.warehouse.execute_many(query, batch)

        logger.info(f"Saved {total_saved} anomalies to warehouse")
        return total_saved

    def get_anomaly_summary(self, anomalies: List[AnomalyResult]) -> Dict[str, Any]:
        """Generate a summary of detected anomalies."""
        if not anomalies:
            return {'total': 0, 'by_severity': {}, 'by_service': {}, 'by_team': {}}

        severity_counts = {}
        service_counts = {}
        team_counts = {}

        for a in anomalies:
            severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1
            service_counts[a.service_name] = service_counts.get(a.service_name, 0) + 1
            team_counts[a.team_name] = team_counts.get(a.team_name, 0) + 1

        return {
            'total': len(anomalies),
            'by_severity': severity_counts,
            'by_service': dict(sorted(service_counts.items(), key=lambda x: -x[1])[:10]),
            'by_team': dict(sorted(team_counts.items(), key=lambda x: -x[1])[:10]),
            'max_deviation_pct': max(abs(a.deviation_pct) for a in anomalies),
            'total_excess_cost': sum(a.actual_cost - a.expected_cost for a in anomalies
                                    if a.actual_cost > a.expected_cost),
            'detection_method': self.method,
            'detection_timestamp': datetime.now().isoformat()
        }
