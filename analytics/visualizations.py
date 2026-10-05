"""
Visualizations Module
Creates all charts and graphs for cloud cost analytics.
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional
import os

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


class CostVisualizer:
    """Generates cloud cost analytics visualizations."""

    def __init__(self, df: pd.DataFrame, output_dir: str = 'output/charts'):
        self.df = df.copy()
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Detect columns
        date_cols = [c for c in self.df.columns if 'date' in c.lower()]
        self.date_col = date_cols[0] if date_cols else None
        if self.date_col:
            self.df[self.date_col] = pd.to_datetime(self.df[self.date_col], errors='coerce')

        cost_cols = [c for c in self.df.columns if 'cost' in c.lower() or 'amount' in c.lower()]
        self.cost_col = cost_cols[0] if cost_cols else None

        service_cols = [c for c in self.df.columns if 'service' in c.lower() or 'product' in c.lower()]
        self.service_col = service_cols[0] if service_cols else None

        region_cols = [c for c in self.df.columns if 'region' in c.lower()]
        self.region_col = region_cols[0] if region_cols else None

    def save_chart(self, name: str):
        """Save current figure to file."""
        path = os.path.join(self.output_dir, f"{name}.png")
        plt.savefig(path, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def daily_cost_trend(self):
        """Daily cost over time."""
        if not self.date_col or not self.cost_col:
            return
        daily = self.df.groupby(self.date_col)[self.cost_col].sum().reset_index()
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(daily[self.date_col], daily[self.cost_col], linewidth=1, color='#2E86AB')
        ax.fill_between(daily[self.date_col], daily[self.cost_col], alpha=0.3, color='#2E86AB')
        ax.set_title('Daily Cloud Cost Trend', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Cost ($)')
        plt.xticks(rotation=45)
        self.save_chart('daily_cost_trend')

    def monthly_cost_bar(self):
        """Monthly cost bar chart."""
        if not self.date_col or not self.cost_col:
            return
        self.df['year_month'] = self.df[self.date_col].dt.to_period('M').astype(str)
        monthly = self.df.groupby('year_month')[self.cost_col].sum().reset_index()
        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(monthly['year_month'], monthly[self.cost_col], color='#2E86AB')
        ax.set_title('Monthly Cloud Cost', fontsize=14, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Cost ($)')
        plt.xticks(rotation=45)
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'${height:,.0f}', ha='center', va='bottom', fontsize=8)
        self.save_chart('monthly_cost_bar')

    def top_services_pie(self, top_n: int = 8):
        """Pie chart of top services by cost."""
        if not self.service_col or not self.cost_col:
            return
        svc = self.df.groupby(self.service_col)[self.cost_col].sum().nlargest(top_n)
        other = self.df[self.cost_col].sum() - svc.sum()
        if other > 0:
            svc['Other'] = other
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette('Set2', len(svc))
        ax.pie(svc.values, labels=svc.index, autopct='%1.1f%%', colors=colors, startangle=90)
        ax.set_title(f'Top {top_n} Cloud Services by Cost', fontsize=14, fontweight='bold')
        self.save_chart('top_services_pie')

    def cost_by_region_bar(self):
        """Horizontal bar chart of cost by region."""
        if not self.region_col or not self.cost_col:
            return
        region = self.df.groupby(self.region_col)[self.cost_col].sum().sort_values()
        fig, ax = plt.subplots(figsize=(10, 6))
        region.plot(kind='barh', ax=ax, color='#A23B72')
        ax.set_title('Cloud Cost by Region', fontsize=14, fontweight='bold')
        ax.set_xlabel('Cost ($)')
        ax.set_ylabel('Region')
        self.save_chart('cost_by_region_bar')

    def service_cost_vs_usage(self):
        """Scatter plot: cost vs usage by service."""
        usage_cols = [c for c in self.df.columns if 'usage' in c.lower() or 'quantity' in c.lower()]
        if not usage_cols or not self.service_col or not self.cost_col:
            return
        usage = usage_cols[0]
        svc_cost = self.df.groupby(self.service_col).agg({self.cost_col: 'sum', usage: 'sum'}).reset_index()
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.scatterplot(data=svc_cost, x=usage, y=self.cost_col, s=200, ax=ax, color='#F18F01')
        for _, row in svc_cost.iterrows():
            ax.annotate(row[self.service_col], (row[usage], row[self.cost_col]),
                       fontsize=8, ha='center')
        ax.set_title('Cost vs Usage by Service', fontsize=14, fontweight='bold')
        ax.set_xlabel('Usage')
        ax.set_ylabel('Cost ($)')
        self.save_chart('service_cost_vs_usage')

    def day_of_week_heatmap(self):
        """Heatmap: cost by day of week and hour (if hour available)."""
        if not self.date_col or not self.cost_col:
            return
        self.df['day_of_week'] = self.df[self.date_col].dt.day_name()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot = self.df.pivot_table(values=self.cost_col, index='day_of_week', aggfunc='sum')
        pivot = pivot.reindex(day_order)
        fig, ax = plt.subplots(figsize=(12, 4))
        sns.heatmap(pivot.values.reshape(1, -1), annot=True, fmt='.0f',
                   xticklabels=day_order, yticklabels=['Cost'], cmap='YlOrRd', ax=ax)
        ax.set_title('Cost by Day of Week', fontsize=14, fontweight='bold')
        self.save_chart('day_of_week_heatmap')

    def cumulative_cost(self):
        """Cumulative cost over time."""
        if not self.date_col or not self.cost_col:
            return
        daily = self.df.groupby(self.date_col)[self.cost_col].sum().reset_index()
        daily = daily.sort_values(self.date_col)
        daily['Cumulative'] = daily[self.cost_col].cumsum()
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.plot(daily[self.date_col], daily['Cumulative'], color='#C73E1D', linewidth=2)
        ax.fill_between(daily[self.date_col], daily['Cumulative'], alpha=0.2, color='#C73E1D')
        ax.set_title('Cumulative Cloud Cost', fontsize=14, fontweight='bold')
        ax.set_xlabel('Date')
        ax.set_ylabel('Cumulative Cost ($)')
        plt.xticks(rotation=45)
        self.save_chart('cumulative_cost')

    def cost_distribution(self):
        """Distribution of daily costs."""
        if not self.date_col or not self.cost_col:
            return
        daily = self.df.groupby(self.date_col)[self.cost_col].sum()
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(daily, bins=30, color='#2E86AB', edgecolor='white', alpha=0.7)
        ax.axvline(daily.mean(), color='red', linestyle='--', label=f'Mean: ${daily.mean():.0f}')
        ax.axvline(daily.median(), color='orange', linestyle='--', label=f'Median: ${daily.median():.0f}')
        ax.set_title('Distribution of Daily Cloud Costs', fontsize=14, fontweight='bold')
        ax.set_xlabel('Daily Cost ($)')
        ax.set_ylabel('Frequency')
        ax.legend()
        self.save_chart('cost_distribution')

    def generate_all(self):
        """Generate all visualizations."""
        print("\nGenerating visualizations...")
        self.daily_cost_trend()
        self.monthly_cost_bar()
        self.top_services_pie()
        self.cost_by_region_bar()
        self.service_cost_vs_usage()
        self.day_of_week_heatmap()
        self.cumulative_cost()
        self.cost_distribution()
        print(f"\nAll charts saved to: {self.output_dir}/")
