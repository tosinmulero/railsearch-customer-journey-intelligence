# RailSearch — Stage 4 Predictive Conversion Modelling

## Objective

Predict whether a rail search will ultimately result in a booking.

The prediction point is immediately after search results are returned and before the customer selects a journey.

This prevents leakage from downstream events such as journey selection, checkout errors, payment failures, checkout completion and revenue.

## Dataset

- Training observations: 172,612
- Validation observations: 44,760
- Locked test observations: 43,352
- Prediction features: 18
- Target: eventual booking
- Split strategy: temporal

Training covers January–April 2026, validation covers May 2026, and the locked test set covers June 2026.

## Champion model

Selected model: **Logistic Regression**

Validation PR-AUC: 0.3715

Validation ROC-AUC: 0.6014

The model was selected using validation performance only. The test period remained locked until model selection was complete.

## Locked test performance

- ROC-AUC: 0.6011
- PR-AUC: 0.3687
- Log loss: 0.5834
- Brier score: 0.2017
- Accuracy at 0.50: 0.7010
- Precision at 0.50: 0.0000
- Recall at 0.50: 0.0000
- F1 at 0.50: 0.0000

## Ranking value

- Overall test booking rate: 29.90%
- Top predicted decile booking rate: 41.43%
- Top-decile lift: 1.386x

This demonstrates whether the model can meaningfully rank customer searches by likelihood to convert.

## Most influential features

- railcard_used: 0.04421
- zero_results_flag: 0.02274
- customer_type: 0.00630
- is_logged_in: 0.00306
- device_type: 0.00262
- operating_system: 0.00181
- destination_station: 0.00129
- acquisition_channel: 0.00030
- results_count: 0.00018
- search_latency_ms: 0.00007

Permutation importance is calculated against PR-AUC on a held-out test sample.

## Product interpretation

The model is designed as a reusable decision-support component rather than an automated customer decision system.

Potential product applications include:

1. identifying search contexts with unusually low conversion propensity;
2. prioritising customer-journey investigations;
3. comparing predicted versus observed conversion by route or device;
4. supporting experimentation and intervention targeting;
5. detecting changing customer behaviour through model monitoring.

## Leakage controls

The model excludes downstream variables including:

- journey selected flag;
- checkout started flag;
- checkout error flag;
- payment failure flag;
- checkout completion flag;
- checkout abandonment flag;
- booking revenue.

Search-result availability is retained because the prediction point occurs after search results are returned.

## Limitations

RailSearch uses synthetic customer-journey data created for portfolio demonstration.

The model therefore demonstrates methodology, engineering discipline and product-science workflow. Its performance must not be interpreted as Trainline production performance or actual commercial behaviour.
