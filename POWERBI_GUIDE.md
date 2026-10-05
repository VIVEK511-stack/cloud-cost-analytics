# Power BI Dashboard Build Guide

Complete step-by-step instructions to build all three dashboards.

---

## Setup: Import Data

1. Open **Power BI Desktop**
2. Click **Get Data** → **Text/CSV**
3. Import these files from `output/powerbi/`:
   - `daily_costs.csv`
   - `monthly_summary.csv`
   - `service_breakdown.csv`
   - `region_breakdown.csv`
4. Click **Load**

---

## Create DAX Measures

Go to **Modeling** → **New Measure**. Create each one:

### Core KPIs
```dax
Total Spend = SUM('daily_costs'[Daily Cost])
```

```dax
Avg Daily Cost = AVERAGE('daily_costs'[Daily Cost])
```

```dax
Total Days = DISTINCTCOUNT('daily_costs'[Date])
```

```dax
30-Day Forecast = SUMX('daily_costs', 'daily_costs'[Daily Cost] * 30 / COUNTROWS('daily_costs'))
```

```dax
Top Service Cost = MAX('service_breakdown'[Total Cost])
```

```dax
Top Service Name = MAXX(TOPN(1, 'service_breakdown', 'service_breakdown'[Total Cost], DESC), 'service_breakdown'[Service])
```

### Growth & Variance
```dax
MoM Growth % = 
VAR CurrentMonth = SUM('monthly_summary'[Total Cost])
VAR PrevMonth = CALCULATE(SUM('monthly_summary'[Total Cost]), DATEADD('monthly_summary'[Month], -1, MONTH))
RETURN
IF(ISBLANK(PrevMonth), BLANK(), (CurrentMonth - PrevMonth) / PrevMonth * 100)
```

```dax
Cumulative Cost = 
CALCULATE(
    SUM('daily_costs'[Daily Cost]),
    FILTER(ALL('daily_costs'[Date]), 'daily_costs'[Date] <= MAX('daily_costs'[Date]))
)
```

```dax
Cost per Day = DIVIDE([Total Spend], [Total Days], 0)
```

### Service Analytics
```dax
Service % of Total = 
DIVIDE(
    SUM('service_breakdown'[Total Cost]),
    CALCULATE(SUM('service_breakdown'[Total Cost]), ALL('service_breakdown'[Service]))
)
```

```dax
Service Rank = RANKX(ALL('service_breakdown'[Service]), SUM('service_breakdown'[Total Cost]), , DESC)
```

### Region Analytics
```dax
Top Region = MAXX('region_breakdown', 'region_breakdown'[Total Cost])
```

```dax
Region % of Total = 
DIVIDE(
    SUM('region_breakdown'[Total Cost]),
    CALCULATE(SUM('region_breakdown'[Total Cost]), ALL('region_breakdown'[Region]))
)
```

### Forecast & Anomaly
```dax
Daily Average = AVERAGE('daily_costs'[Daily Cost])
```

```dax
Anomaly Threshold = [Daily Average] + 2 * STDEV.P('daily_costs'[Daily Cost])
```

```dax
Projected Month-End = [Daily Average] * DAY(EOMONTH(TODAY(), 0))
```

---

## Dashboard 1: Executive Summary

### Page Setup
- **Page name:** Executive
- **Page size:** 16:9 (1920 x 1080)
- **Background:** #F5F5F5

### Visual 1 — KPI Cards (Top Row)
| Card | DAX Measure | Format |
|---|---|---|
| Card 1 | `Total Spend` | Currency, $ symbol |
| Card 2 | `Avg Daily Cost` | Currency, $ symbol |
| Card 3 | `30-Day Forecast` | Currency, $ symbol |
| Card 4 | `Total Days` | Whole number |

**How to create:**
1. Click **Card** visual
2. Drag `Total Spend` measure into the field
3. Repeat for each card
4. Format: Font size 36, bold, color #333333

### Visual 2 — Daily Cost Trend (Line Chart)
| Property | Value |
|---|---|
| X-axis | `daily_costs[Date]` |
| Y-axis | `daily_costs[Daily Cost]` |
| Line color | #2E86AB |
| Fill | Gradient, 30% opacity |

**How to create:**
1. Click **Line chart**
2. Drag `Date` to X-axis
3. Drag `Daily Cost` to Y-axis
4. Format: Line width 2px, smooth

### Visual 3 — Monthly Cost (Bar Chart)
| Property | Value |
|---|---|
| X-axis | `monthly_summary[Month]` |
| Y-axis | `monthly_summary[Total Cost]` |
| Bar color | #2E86AB |
| Data labels | On, position: Outside end |

### Visual 4 — Top Services (Pie Chart)
| Property | Value |
|---|---|
| Legend | `service_breakdown[Service]` |
| Values | `service_breakdown[Total Cost]` |
| Colors | #2E86AB, #A23B72, #F18F01, #C73E1D, #4CAF50, #9C27B0 |

### Visual 5 — Cost by Region (Bar Chart)
| Property | Value |
|---|---|
| Y-axis | `region_breakdown[Region]` |
| X-axis | `region_breakdown[Total Cost]` |
| Bar color | #A23B72 |
| Sort | Descending by Total Cost |

### Visual 6 — Cumulative Cost (Area Chart)
| Property | Value |
|---|---|
| X-axis | `daily_costs[Date]` |
| Y-axis | `[Cumulative Cost]` measure |
| Fill color | #C73E1D, 20% opacity |

### Filters (Right Panel)
| Filter | Field |
|---|---|
| Date range | `daily_costs[Date]` |
| Service | `service_breakdown[Service]` |
| Region | `region_breakdown[Region]` |

---

## Dashboard 2: Anomaly & Forecast

### Page Setup
- **Page name:** Anomaly Forecast
- **Page size:** 16:9
- **Background:** #F5F5F5

### Visual 1 — Daily Cost with Anomaly Threshold (Line Chart)
| Property | Value |
|---|---|
| X-axis | `daily_costs[Date]` |
| Y-axis | `daily_costs[Daily Cost]` |
| Constant line | `[Anomaly Threshold]` |
| Anomaly points | Red color, size 8 |

### Visual 2 — Cost Distribution (Histogram)
| Property | Value |
|---|---|
| X-axis | `daily_costs[Daily Cost]` (binned) |
| Y-axis | Count of records |
| Bar color | #2E86AB |
| Mean line | Dashed red |
| Median line | Dashed orange |

### Visual 3 — 30-Day Forecast (Line Chart)
| Property | Value |
|---|---|
| X-axis | Date (historical + forecast) |
| Y-axis | `Daily Cost` |
| Forecast line | Dashed, color #C73E1D |
| Confidence band | 90% opacity fill |

### Visual 4 — Anomaly Table
| Column | Field |
|---|---|
| Date | `daily_costs[Date]` |
| Daily Cost | `daily_costs[Daily Cost]` |
| Threshold | `[Anomaly Threshold]` |
| Status | Conditional: "Anomaly" if cost > threshold |

**Conditional formatting:**
- If Daily Cost > Threshold → Background #FFCDD2, Text #C73E1D
- Else → Background #C8E6C9, Text #2E7D32

### Visual 5 — Forecast Summary (Card)
| Card | Value |
|---|---|
| Projected Month-End | `[Projected Month-End]` |
| Current Daily Avg | `[Daily Average]` |
| Confidence | 90% |

---

## Dashboard 3: Service Deep Dive

### Page Setup
- **Page name:** Service Analysis
- **Page size:** 16:9
- **Background:** #F5F5F5

### Visual 1 — Service Cost Breakdown (Treemap)
| Property | Value |
|---|---|
| Category | `service_breakdown[Service]` |
| Values | `service_breakdown[Total Cost]` |
| Data labels | On |
| Colors | Multi-color |

### Visual 2 — Service % of Total (Donut Chart)
| Property | Value |
|---|---|
| Legend | `service_breakdown[Service]` |
| Values | `[Service % of Total]` |
| Inner radius | 60% |

### Visual 3 — Service Comparison (Matrix)
| Row | `service_breakdown[Service]` |
|---|---|
| Column | `region_breakdown[Region]` |
| Values | `service_breakdown[Total Cost]` |
| Conditional formatting | Background scale: white → #2E86AB |

### Visual 4 — Top 10 Services (Stacked Bar)
| Property | Value |
|---|---|
| Y-axis | `service_breakdown[Service]` |
| X-axis | `service_breakdown[Total Cost]` |
| Legend | `service_breakdown[Service]` |
| Top N | 10 |

### Visual 5 — Service Trend Over Time (Line Chart)
| Property | Value |
|---|---|
| X-axis | `daily_costs[Date]` |
| Y-axis | `daily_costs[Daily Cost]` |
| Legend | `service_breakdown[Service]` |
| Line width | 2px |

### Visual 6 — Cost per Unit by Service (Scatter Plot)
| Property | Value |
|---|---|
| X-axis | `service_breakdown[Total Cost]` |
| Y-axis | `daily_costs[Daily Cost]` |
| Size | `service_breakdown[Total Cost]` |
| Color | `service_breakdown[Service]` |

---

## Global Formatting

### Color Palette
| Element | Hex Code |
|---|---|
| Primary Blue | #2E86AB |
| Secondary Magenta | #A2B72 |
| Accent Orange | #F18F01 |
| Warning Red | #C73E1D |
| Success Green | #4CAF50 |
| Background | #F5F5F5 |
| Text Primary | #333333 |
| Text Secondary | #666666 |
| Grid Lines | #E0E0E0 |

### Font Settings
| Element | Font | Size | Weight |
|---|---|---|---|
| Title | Segoe UI | 18 | Bold |
| Subtitle | Segoe UI | 12 | Regular |
| KPI Value | Segoe UI | 36 | Bold |
| KPI Label | Segoe UI | 10 | Regular |
| Axis | Segoe UI | 10 | Regular |
| Data Labels | Segoe UI | 9 | Regular |

### Theme File (Save as `theme.json`)
```json
{
  "name": "CloudCostTheme",
  "dataColors": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#4CAF50", "#9C27B0", "#00BCD4", "#FF9800"],
  "background": "#F5F5F5",
  "foreground": "#333333",
  "tableAccent": "#2E86AB"
}
```

**Apply theme:** View → Themes → Browse for themes → select `theme.json`

---

## Publish to Power BI Service

1. Click **Publish** (top right)
2. Select your workspace
3. Configure scheduled refresh:
   - Go to dataset → Settings
   - Scheduled refresh → On
   - Frequency: Daily at 6:00 AM
4. Share dashboard with stakeholders

---

## Quick Reference: Field Mapping

| CSV File | Key Fields | Used In |
|---|---|---|
| `daily_costs.csv` | Date, Daily Cost | All dashboards |
| `monthly_summary.csv` | Month, Total Cost, Avg Daily Cost | Executive |
| `service_breakdown.csv` | Service, Total Cost | Executive, Service |
| `region_breakdown.csv` | Region, Total Cost | Executive, Service |
