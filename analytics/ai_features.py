"""
AI-Powered Analytics Module
Adds ML classification, NLP insights, and AI recommendations.
Not too complex - uses simple, interpretable models.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Dict, Any, List
import warnings
warnings.filterwarnings('ignore')


class AICostAnalyzer:
    """
    AI-powered cloud cost analyzer.
    Uses simple, interpretable ML models for:
    1. Cost anomaly classification
    2. Cost prediction
    3. AI-generated insights
    4. Cost optimization recommendations
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.models = {}
        self.encoders = {}
        self.scaler = StandardScaler()
        self._prepare_features()

    def _prepare_features(self):
        """Feature engineering for ML models."""
        # Detect columns
        date_cols = [c for c in self.df.columns if 'date' in c.lower()]
        cost_cols = [c for c in self.df.columns if 'cost' in c.lower() or 'amount' in c.lower()]
        service_cols = [c for c in self.df.columns if 'service' in c.lower() or 'product' in c.lower()]
        region_cols = [c for c in self.df.columns if 'region' in c.lower()]
        usage_cols = [c for c in self.df.columns if 'usage' in c.lower() or 'quantity' in c.lower()]

        self.date_col = date_cols[0] if date_cols else None
        self.cost_col = cost_cols[0] if cost_cols else None
        self.service_col = service_cols[0] if service_cols else None
        self.region_col = region_cols[0] if region_cols else None
        self.usage_col = usage_cols[0] if usage_cols else None

        # Create time-based features
        if self.date_col:
            self.df[self.date_col] = pd.to_datetime(self.df[self.date_col], errors='coerce')
            self.df['day_of_week'] = self.df[self.date_col].dt.dayofweek
            self.df['month'] = self.df[self.date_col].dt.month
            self.df['is_weekend'] = (self.df['day_of_week'] >= 5).astype(int)
            self.df['day_of_month'] = self.df[self.date_col].dt.day

        # Encode categorical features
        for col in [self.service_col, self.region_col]:
            if col:
                le = LabelEncoder()
                self.df[f'{col}_encoded'] = le.fit_transform(self.df[col].astype(str))
                self.encoders[col] = le

        # Cost-based features
        if self.cost_col:
            self.df['cost_log'] = np.log1p(self.df[self.cost_col])
            self.df['cost_zscore'] = (self.df[self.cost_col] - self.df[self.cost_col].mean()) / self.df[self.cost_col].std()

        # Rolling features
        if self.cost_col and self.date_col:
            self.df = self.df.sort_values(self.date_col)
            self.df['cost_7d_avg'] = self.df[self.cost_col].rolling(7, min_periods=1).mean()
            self.df['cost_7d_std'] = self.df[self.cost_col].rolling(7, min_periods=1).std().fillna(0)
            self.df['cost_diff_7d'] = self.df[self.cost_col] - self.df['cost_7d_avg']

    def train_anomaly_classifier(self) -> Dict[str, Any]:
        """
        Train a Random Forest classifier to detect cost anomalies.
        Classifies each record as: Normal, Warning, Critical
        """
        if not self.cost_col:
            return {'error': 'No cost column found'}

        # Create anomaly labels based on z-score
        self.df['anomaly_label'] = pd.cut(
            self.df['cost_zscore'],
            bins=[-np.inf, -2, -1, 1, 2, np.inf],
            labels=['Very Low', 'Low', 'Normal', 'High', 'Critical']
        )

        # Features for classification
        feature_cols = []
        for col in [f'{self.service_col}_encoded', f'{self.region_col}_encoded',
                    'day_of_week', 'month', 'is_weekend', 'cost_7d_avg', 'cost_7d_std', 'cost_diff_7d']:
            if col in self.df.columns:
                feature_cols.append(col)

        if not feature_cols:
            return {'error': 'No features available'}

        X = self.df[feature_cols].fillna(0)
        y = self.df['anomaly_label']

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

        # Train Random Forest
        rf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        rf.fit(X_train, y_train)

        # Predictions
        y_pred = rf.predict(X_test)

        # Feature importance
        importance = dict(zip(feature_cols, rf.feature_importances_.tolist()))

        self.models['anomaly_classifier'] = rf

        return {
            'model_type': 'Random Forest Classifier',
            'classes': rf.classes_.tolist(),
            'feature_importance': importance,
            'train_accuracy': rf.score(X_train, y_train),
            'test_accuracy': rf.score(X_test, y_test),
            'classification_report': classification_report(y_test, y_pred, output_dict=True)
        }

    def train_cost_predictor(self) -> Dict[str, Any]:
        """
        Train a Gradient Boosting regressor to predict future costs.
        """
        if not self.cost_col:
            return {'error': 'No cost column found'}

        feature_cols = []
        for col in [f'{self.service_col}_encoded', f'{self.region_col}_encoded',
                    'day_of_week', 'month', 'is_weekend', 'cost_7d_avg', 'cost_7d_std']:
            if col in self.df.columns:
                feature_cols.append(col)

        if not feature_cols:
            return {'error': 'No features available'}

        X = self.df[feature_cols].fillna(0)
        y = self.df[self.cost_col]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

        gbr = GradientBoostingRegressor(n_estimators=50, max_depth=3, learning_rate=0.1, random_state=42)
        gbr.fit(X_train, y_train)

        y_pred = gbr.predict(X_test)

        self.models['cost_predictor'] = gbr

        return {
            'model_type': 'Gradient Boosting Regressor',
            'mae': round(mean_absolute_error(y_test, y_pred), 2),
            'r2_score': round(r2_score(y_test, y_pred), 4),
            'feature_importance': dict(zip(feature_cols, gbr.feature_importances_.tolist()))
        }

    def generate_ai_insights(self) -> List[Dict[str, str]]:
        """
        Generate AI-powered insights from the data.
        Uses rule-based logic enhanced with ML predictions.
        """
        insights = []

        if not self.cost_col:
            return insights

        # Insight 1: Cost trend
        if self.date_col:
            daily = self.df.groupby(self.date_col)[self.cost_col].sum()
            if len(daily) > 1:
                trend = np.polyfit(range(len(daily)), daily.values, 1)[0]
                if trend > 0:
                    insights.append({
                        'category': 'Trend',
                        'severity': 'Warning',
                        'title': 'Increasing Cost Trend',
                        'description': f'Costs are increasing by ${trend:.2f} per day. Consider reviewing resource usage.'
                    })
                else:
                    insights.append({
                        'category': 'Trend',
                        'severity': 'Positive',
                        'title': 'Decreasing Cost Trend',
                        'description': f'Costs are decreasing by ${abs(trend):.2f} per day. Good cost management!'
                    })

        # Insight 2: Weekend vs Weekday
        if 'is_weekend' in self.df.columns:
            weekend_avg = self.df[self.df['is_weekend'] == 1][self.cost_col].mean()
            weekday_avg = self.df[self.df['is_weekend'] == 0][self.cost_col].mean()
            if weekend_avg > weekday_avg * 1.2:
                insights.append({
                    'category': 'Pattern',
                    'severity': 'Warning',
                    'title': 'Higher Weekend Costs',
                    'description': f'Weekend costs are {((weekend_avg/weekday_avg)-1)*100:.1f}% higher than weekdays. Consider scaling down non-prod resources on weekends.'
                })

        # Insight 3: Service concentration
        if self.service_col:
            svc_costs = self.df.groupby(self.service_col)[self.cost_col].sum().sort_values(ascending=False)
            top_svc_pct = svc_costs.iloc[0] / svc_costs.sum() * 100
            if top_svc_pct > 50:
                insights.append({
                    'category': 'Concentration',
                    'severity': 'Warning',
                    'title': 'High Service Concentration',
                    'description': f'{svc_costs.index[0]} accounts for {top_svc_pct:.1f}% of total costs. Consider diversifying or optimizing this service.'
                })

        # Insight 4: Anomaly detection
        if 'cost_zscore' in self.df.columns:
            anomalies = self.df[self.df['cost_zscore'] > 2]
            if len(anomalies) > 0:
                insights.append({
                    'category': 'Anomaly',
                    'severity': 'Critical',
                    'title': f'{len(anomalies)} Cost Anomalies Detected',
                    'description': f'Found {len(anomalies)} records with unusually high costs. Review these for potential waste or errors.'
                })

        # Insight 5: Cost per unit efficiency
        if self.usage_col and self.usage_col in self.df.columns:
            self.df['cost_per_unit'] = self.df[self.cost_col] / self.df[self.usage_col].replace(0, np.nan)
            cpu = self.df.groupby(self.service_col)['cost_per_unit'].mean().sort_values(ascending=False)
            if len(cpu) > 0:
                insights.append({
                    'category': 'Efficiency',
                    'severity': 'Info',
                    'title': 'Cost per Unit Analysis',
                    'description': f'Highest cost per unit: {cpu.index[0]} at ${cpu.iloc[0]:.4f}/unit. Consider rightsizing.'
                })

        # Insight 6: Regional cost distribution
        if self.region_col:
            region_costs = self.df.groupby(self.region_col)[self.cost_col].sum().sort_values(ascending=False)
            if len(region_costs) > 1:
                top_region_pct = region_costs.iloc[0] / region_costs.sum() * 100
                insights.append({
                    'category': 'Distribution',
                    'severity': 'Info',
                    'title': 'Regional Cost Distribution',
                    'description': f'{region_costs.index[0]} accounts for {top_region_pct:.1f}% of costs. Consider multi-region optimization.'
                })

        return insights

    def generate_recommendations(self) -> List[Dict[str, str]]:
        """
        Generate AI-powered cost optimization recommendations.
        """
        recommendations = []

        if not self.cost_col:
            return recommendations

        # Recommendation 1: Rightsizing
        if self.service_col and self.usage_col in self.df.columns:
            self.df['cost_per_unit'] = self.df[self.cost_col] / self.df[self.usage_col].replace(0, np.nan)
            high_cpu = self.df.groupby(self.service_col)['cost_per_unit'].mean().nlargest(3)
            for svc, cpu in high_cpu.items():
                recommendations.append({
                    'priority': 'High',
                    'category': 'Rightsizing',
                    'action': f'Review {svc} instance sizes',
                    'potential_saving': f'${cpu * 0.3:.2f}/unit (30% reduction)',
                    'effort': 'Medium'
                })

        # Recommendation 2: Reserved Instances
        if self.service_col:
            svc_costs = self.df.groupby(self.service_col)[self.cost_col].sum().sort_values(ascending=False)
            top_svc = svc_costs.index[0]
            recommendations.append({
                'priority': 'High',
                'category': 'Pricing Model',
                'action': f'Purchase Reserved Instances for {top_svc}',
                'potential_saving': f'${svc_costs.iloc[0] * 0.4:.2f} (40% RI discount)',
                'effort': 'Low'
            })

        # Recommendation 3: Weekend scheduling
        if 'is_weekend' in self.df.columns:
            weekend_cost = self.df[self.df['is_weekend'] == 1][self.cost_col].sum()
            if weekend_cost > 0:
                recommendations.append({
                    'priority': 'Medium',
                    'category': 'Scheduling',
                    'action': 'Schedule non-prod resources to stop on weekends',
                    'potential_saving': f'${weekend_cost * 0.7:.2f} (70% weekend reduction)',
                    'effort': 'Low'
                })

        # Recommendation 4: Storage optimization
        if self.service_col:
            storage_svcs = [s for s in self.df[self.service_col].unique() if 's3' in str(s).lower() or 'storage' in str(s).lower() or 'ebs' in str(s).lower()]
            if storage_svcs:
                storage_cost = self.df[self.df[self.service_col].isin(storage_svcs)][self.cost_col].sum()
                recommendations.append({
                    'priority': 'Medium',
                    'category': 'Storage',
                    'action': 'Implement S3 lifecycle policies and EBS snapshot cleanup',
                    'potential_saving': f'${storage_cost * 0.25:.2f} (25% storage reduction)',
                    'effort': 'Low'
                })

        # Recommendation 5: Tagging governance
        recommendations.append({
            'priority': 'High',
            'category': 'Governance',
            'action': 'Implement mandatory cost allocation tags',
            'potential_saving': 'Improved cost visibility and accountability',
            'effort': 'Medium'
        })

        return recommendations

    def run_full_ai_analysis(self) -> Dict[str, Any]:
        """Run complete AI analysis pipeline."""
        print("\n" + "=" * 60)
        print("AI-POWERED COST ANALYSIS")
        print("=" * 60)

        # Train models
        print("\n[1/4] Training anomaly classifier...")
        anomaly_results = self.train_anomaly_classifier()
        print(f"  Model accuracy: {anomaly_results.get('test_accuracy', 'N/A')}")

        print("\n[2/4] Training cost predictor...")
        predictor_results = self.train_cost_predictor()
        print(f"  R2 Score: {predictor_results.get('r2_score', 'N/A')}")

        # Generate insights
        print("\n[3/4] Generating AI insights...")
        insights = self.generate_ai_insights()
        for insight in insights:
            print(f"  [{insight['severity']}] {insight['title']}")

        # Generate recommendations
        print("\n[4/4] Generating recommendations...")
        recommendations = self.generate_recommendations()
        for rec in recommendations:
            print(f"  [{rec['priority']}] {rec['action']}")

        return {
            'anomaly_model': anomaly_results,
            'cost_predictor': predictor_results,
            'insights': insights,
            'recommendations': recommendations,
            'total_insights': len(insights),
            'total_recommendations': len(recommendations)
        }
