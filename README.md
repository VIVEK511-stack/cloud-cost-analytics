# Cloud Cost Analytics Platform (AI-Powered)

An **AI-powered data analytics** project that analyzes cloud billing data, detects anomalies, forecasts costs, generates NLP insights, and provides AI-driven cost optimization recommendations.

## Quick Start (3 Steps)

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the analysis
python run_analysis.py

# 3. Check results in output/
```

## What It Does

| Feature | Description |
|---|---|
| **KPI Calculation** | Total spend, daily average, MoM growth, top services/regions |
| **Visualizations** | 11 charts saved as PNG files |
| **Anomaly Detection** | 3 methods (Z-Score, IQR, Rolling Mean) |
| **Forecasting** | 30-day cost projection with 3 methods |
| **AI/ML Models** | Random Forest classifier + Gradient Boosting regressor |
| **NLP Insights** | Natural language summaries and trend narratives |
| **AI Recommendations** | Cost optimization suggestions with savings estimates |
| **Feature Engineering** | ML-ready features (time, cost, categorical, interaction) |
| **Model Evaluation** | MAE, RMSE, R2, MAPE, Accuracy, F1 Score |
| **Power BI Export** | CSV files ready to import |

## Project Structure

```
cloud-cost-analytics/
├── run_analysis.py              # Main analytics script
├── download_data.py             # Data download helper
├── analytics/
│   ├── kpis.py                  # KPI calculations
│   ├── visualizations.py        # Chart generation
│   ├── anomaly.py               # Anomaly detection
│   ├── forecast.py              # Cost forecasting
│   ├── ai_features.py           # AI/ML models (Random Forest, Gradient Boosting)
│   ├── nlp_insights.py          # NLP-style natural language insights
│   ├── feature_engineering.py   # ML feature engineering
│   ├── model_evaluation.py      # Model performance metrics
│   └── export.py                # Power BI CSV exports
├── data/
│   └── cloud_billing.csv        # Raw billing data
└── output/
    ├── charts/                  # Generated PNG charts
    ├── powerbi/                 # CSV files for Power BI
    └── nlp_report.txt           # Natural language report
```

## AI/ML Models Used

| Model | Purpose | Library |
|---|---|---|
| Random Forest Classifier | Anomaly classification (Normal/Warning/Critical) | Scikit-learn |
| Gradient Boosting Regressor | Cost prediction | Scikit-learn |
| Linear Regression | Trend forecasting | Scikit-learn |
| Exponential Smoothing | Cost forecasting | Custom |
| NLP Generator | Natural language insights | Custom |

## Data Source

Download a cloud billing dataset from Kaggle:
- Search: "cloud billing data" or "AWS cost usage"
- Recommended: any CSV with columns like `date`, `service`, `cost`, `region`
- Save as: `data/cloud_billing.csv`

## Power BI Dashboards

After running analysis, import these CSVs into Power BI:

| CSV File | Dashboard Use |
|---|---|
| `daily_costs.csv` | Executive trend line |
| `monthly_summary.csv` | Monthly bar chart |
| `service_breakdown.csv` | Service pie/bar chart |
| `region_breakdown.csv` | Region map |
| `anomalies.csv` | Anomaly table |
| `forecasts.csv` | Forecast line chart |
| `kpi_summary.json` | KPI cards |
| `ai_insights.json` | AI recommendations |

### Power BI Setup
1. Open Power BI Desktop
2. **Get Data** → **Text/CSV** → select files from `output/powerbi/`
3. Build visuals using the fields
4. See `POWERBI_GUIDE.md` for dashboard layout specs

## Requirements

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
seaborn>=0.13
scipy>=1.11
scikit-learn>=1.3
tabulate>=0.9
```

Install: `pip install -r requirements.txt`

## Alignment with MathCo AI Analyst Role

| JD Requirement | Implementation |
|---|---|
| Business Problem Solving | Problem framing in KPI report |
| AI/ML Models | Random Forest, Gradient Boosting |
| NLP | Natural language insights generator |
| Feature Engineering | Time, cost, categorical, interaction features |
| Model Evaluation | MAE, RMSE, R2, Accuracy, F1 |
| End-to-End Delivery | From data ingestion to Power BI export |
| User-Facing Prototypes | Power BI dashboards + NLP reports |
