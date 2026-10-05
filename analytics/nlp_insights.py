"""
NLP-Style Insights Module
Generates natural language summaries of cloud cost data.
Uses simple text generation (no external API needed).
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime


class NLPInsightsGenerator:
    """Generates natural language insights from cloud cost data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.date_col = [c for c in self.df.columns if 'date' in c.lower()][0] if any('date' in c.lower() for c in self.df.columns) else None
        self.cost_col = [c for c in self.df.columns if 'cost' in c.lower() or 'amount' in c.lower()][0] if any('cost' in c.lower() or 'amount' in c.lower() for c in self.df.columns) else None
        self.service_col = [c for c in self.df.columns if 'service' in c.lower() or 'product' in c.lower()][0] if any('service' in c.lower() or 'product' in c.lower() for c in self.df.columns) else None
        self.region_col = [c for c in self.df.columns if 'region' in c.lower()][0] if any('region' in c.lower() for c in self.df.columns) else None

    def generate_executive_summary(self) -> str:
        """Generate a natural language executive summary."""
        if not self.cost_col:
            return "No cost data available."

        total = self.df[self.cost_col].sum()
        avg_daily = total / len(self.df[self.date_col].unique()) if self.date_col else total

        summary = f"Cloud Cost Executive Summary\n"
        summary += f"{'=' * 40}\n\n"
        summary += f"Total cloud spend: ${total:,.2f}\n"
        summary += f"Average daily cost: ${avg_daily:,.2f}\n"
        summary += f"Analysis period: {len(self.df)} records\n"

        if self.service_col:
            top_svc = self.df.groupby(self.service_col)[self.cost_col].sum().nlargest(3)
            summary += f"\nTop 3 services by cost:\n"
            for i, (svc, cost) in enumerate(top_svc.items(), 1):
                pct = cost / total * 100
                summary += f"  {i}. {svc}: ${cost:,.2f} ({pct:.1f}%)\n"

        return summary

    def generate_anomaly_explanation(self, date: str, cost: float, avg: float) -> str:
        """Generate natural language explanation for an anomaly."""
        deviation = ((cost - avg) / avg) * 100
        if deviation > 100:
            severity = "critically high"
        elif deviation > 50:
            severity = "significantly high"
        elif deviation > 20:
            severity = "moderately high"
        else:
            severity = "slightly high"

        explanation = f"On {date}, cloud costs were {severity} at ${cost:,.2f}, "
        explanation += f"which is {deviation:.1f}% above the average of ${avg:,.2f}. "
        explanation += f"This may indicate unexpected usage, a misconfiguration, or a potential cost optimization opportunity."

        return explanation

    def generate_trend_narrative(self) -> str:
        """Generate natural language description of cost trends."""
        if not self.date_col or not self.cost_col:
            return "Insufficient data for trend analysis."

        daily = self.df.groupby(self.date_col)[self.cost_col].sum().sort_index()
        if len(daily) < 2:
            return "Insufficient data for trend analysis."

        # Calculate trend
        x = np.arange(len(daily))
        slope = np.polyfit(x, daily.values, 1)[0]

        narrative = "Cost Trend Analysis\n"
        narrative += f"{'=' * 40}\n\n"

        if slope > 100:
            narrative += f"Cloud costs are trending UPWARD with an increase of ${slope:.2f} per day. "
            narrative += f"At this rate, monthly costs could increase by ${slope * 30:,.2f}. "
            narrative += f"Immediate action is recommended to control costs."
        elif slope < -100:
            narrative += f"Cloud costs are trending DOWNWARD with a decrease of ${abs(slope):.2f} per day. "
            narrative += f"This represents good cost management. "
            narrative += f"Projected monthly savings: ${abs(slope) * 30:,.2f}."
        else:
            narrative += f"Cloud costs are relatively STABLE with minimal daily variation. "
            narrative += f"Current spending patterns are consistent."

        return narrative

    def generate_service_story(self) -> str:
        """Generate natural language story about service costs."""
        if not self.service_col or not self.cost_col:
            return "No service data available."

        svc_costs = self.df.groupby(self.service_col)[self.cost_col].sum().sort_values(ascending=False)
        total = svc_costs.sum()

        story = "Service Cost Breakdown\n"
        story += f"{'=' * 40}\n\n"

        for svc, cost in svc_costs.items():
            pct = cost / total * 100
            if pct > 30:
                story += f"{svc} dominates cloud spending at ${cost:,.2f} ({pct:.1f}% of total). "
                story += f"This is the primary driver of cloud costs and should be the focus of optimization efforts.\n"
            elif pct > 10:
                story += f"{svc} is a significant cost contributor at ${cost:,.2f} ({pct:.1f}% of total). "
                story += f"Regular review of this service is recommended.\n"
            else:
                story += f"{svc} accounts for ${cost:,.2f} ({pct:.1f}% of total).\n"

        return story

    def generate_full_report(self) -> str:
        """Generate complete natural language report."""
        report = []
        report.append(self.generate_executive_summary())
        report.append("\n" + "=" * 60 + "\n")
        report.append(self.generate_trend_narrative())
        report.append("\n" + "=" * 60 + "\n")
        report.append(self.generate_service_story())

        return "\n".join(report)
