# Power BI Dashboard Guide (MySQL)

## Overview

This guide explains how to connect Power BI to the MySQL warehouse and build the three required dashboards.

## Data Source Connection

### Step 1: Connect to MySQL
1. Open Power BI Desktop
2. Click **Get Data** → **MySQL database**
3. Enter server: `localhost:3306`
4. Database: `cloud_cost_dw`
5. Select **Import** mode
6. Enter credentials when prompted

### Step 2: Import Views
Select these views:
- `v_daily_cost_summary`
- `v_monthly_kpi_summary`
- `v_cost_by_service`
- `v_cost_by_team`
- `v_cost_by_project`
- `v_cost_by_environment`
- `v_budget_variance`
- `v_anomaly_details`
- `v_forecast_summary`
- `v_mom_growth`

Also import dimension tables for filtering:
- `dim_date`
- `dim_service`
- `dim_team`
- `dim_project`
- `dim_environment`

## Dashboard 1: Executive Dashboard

### KPIs (Top Row)
| Visual | Field | Format |
|--------|-------|--------|
| Card | SUM(v_monthly_kpi_summary.monthly_cost) | Currency |
| Card | v_mom_growth.mom_growth_pct | Percentage |
| Card | v_budget_variance.utilization_pct | Percentage |
| Card | v_forecast_summary.forecast_amount | Currency |

### Charts
1. **Monthly Spend Trend** (Line Chart)
   - X-axis: year, month
   - Y-axis: monthly_cost

2. **Top 5 Services** (Bar Chart)
   - Y-axis: service_name
   - X-axis: total_cost
   - Top N: 5

3. **Top 5 Teams** (Bar Chart)
   - Y-axis: team_name
   - X-axis: total_cost
   - Top N: 5

4. **Budget vs Actual** (Clustered Bar)
   - X-axis: team_name
   - Y-axis: budget_amount, actual_spend

5. **Recent Anomalies** (Table)
   - Columns: anomaly_date, service_name, actual_cost, deviation_pct, severity

### Filters
- Date range (dim_date.full_date)
- Account (dim_account.account_name)
- Provider (dim_account.provider)

## Dashboard 2: FinOps Dashboard

### Visuals
1. **Cost by Service** (Matrix)
   - Rows: service_name
   - Columns: year, month
   - Values: total_cost

2. **Daily Cost Trend** (Line Chart)
   - X-axis: full_date
   - Y-axis: total_cost
   - Legend: service_name

3. **Anomaly Details** (Table)
   - Columns: anomaly_date, service_name, team_name, actual_cost, expected_cost, deviation_pct, severity, reason
   - Conditional formatting: severity (Red=Critical, Orange=High, Yellow=Medium)

4. **Budget Variance** (Stacked Bar)
   - X-axis: team_name
   - Y-axis: actual_spend, budget_variance

5. **Cost by Region** (Map)
   - Location: region_name
   - Value: total_cost

6. **Environment Allocation** (Donut Chart)
   - Legend: environment_name
   - Values: total_cost

## Dashboard 3: Engineering Dashboard

### Visuals
1. **Team Spend** (Stacked Bar)
   - X-axis: team_name
   - Y-axis: total_cost
   - Legend: project_name

2. **Prod vs Non-Prod** (Donut Chart)
   - Legend: environment_type
   - Values: total_cost

3. **Service Usage Trends** (Line Chart)
   - X-axis: full_date
   - Y-axis: total_usage
   - Legend: service_name

4. **Top MoM Increases** (Table)
   - Columns: service_name, prev_month_cost, monthly_cost, mom_growth_pct
   - Sort: mom_growth_pct descending
   - Top N: 10

5. **Environment Allocation** (Treemap)
   - Category: environment_name
   - Values: total_cost

6. **Project Cost Breakdown** (Stacked Column)
   - X-axis: project_name
   - Y-axis: total_cost
   - Legend: service_name

## Scheduled Refresh

1. In Power BI Service, go to **Settings** → **Datasets**
2. Select your dataset
3. Under **Scheduled refresh**, set frequency (e.g., Daily at 6:00 AM)
4. Configure credentials
5. Enable refresh notifications

## DAX Measures

```dax
Total Spend = SUM(v_daily_cost_summary[total_cost])

Avg Daily Cost = DIVIDE([Total Spend], DISTINCTCOUNT(v_daily_cost_summary[full_date]))

MoM Growth % =
VAR CurrentMonth = CALCULATE([Total Spend], LASTDATE(dim_date[full_date]))
VAR PrevMonth = CALCULATE([Total Spend], DATEADD(LASTDATE(dim_date[full_date]), -1, MONTH))
RETURN DIVIDE(CurrentMonth - PrevMonth, PrevMonth) * 100

Budget Utilization % = DIVIDE([Total Spend], SUM(v_budget_variance[budget_amount])) * 100

Budget Variance = SUM(v_budget_variance[budget_amount]) - [Total Spend]
```

## Color Scheme

| Element | Color |
|---------|-------|
| Primary | #2E86AB (Blue) |
| Secondary | #A23B72 (Magenta) |
| Success | #F18F01 (Orange) |
| Warning | #C73E1D (Red) |
| Background | #F5F5F5 (Light Gray) |
| Text | #333333 (Dark Gray) |
