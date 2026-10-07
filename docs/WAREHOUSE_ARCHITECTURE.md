# RailSearch Analytical Warehouse

## Architecture

Raw synthetic event data
↓
DuckDB raw views
↓
Staging models
↓
Search-level customer funnel
↓
Product analytics marts
↓
Root-cause analysis
↓
Anomaly detection
↓
Power BI / Python / Machine Learning

## Schemas

### raw

External views over immutable Parquet source datasets.

### staging

Standardised and typed event tables with useful analytical fields.

### analytics

Reusable customer-journey and commercial data marts.

### product

Product-monitoring and investigation frameworks.

## Core marts

- search_funnel
- kpi_summary
- daily_funnel
- device_performance
- channel_performance
- route_performance
- zero_result_analysis
- checkout_failure_analysis
- commercial_impact
- daily_anomaly_alerts

## Commercial impact

Revenue-at-risk values are analytical estimates based on average
successful booking value.

They are not actual Trainline financial results.

## Data disclaimer

Customer journey data in RailSearch are synthetic.

The project does not contain proprietary Trainline customer data.
