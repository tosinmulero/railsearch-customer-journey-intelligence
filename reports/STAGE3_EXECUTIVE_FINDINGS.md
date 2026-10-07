# RailSearch — Senior Data Scientist Investigation

## Executive summary

RailSearch analysed 260,724 synthetic journey searches across the digital rail booking funnel.

Overall search-to-book conversion was 29.82% and the simulated platform generated £5,119,154.52 in booking revenue.

The automated monitoring framework detected 9 anomalous days requiring investigation.

## Finding 1 — Search supply incident

For searches involving London Euston or Manchester Piccadilly during 9–15 March 2026:

- Baseline zero-result rate: 5.83%
- Incident zero-result rate: 20.21%
- Change: +14.38 percentage points
- Baseline conversion: 30.28%
- Incident conversion: 24.20%
- Conversion change: -6.08 percentage points
- Estimated lost bookings versus baseline: 79.5
- Estimated revenue impact: £5,066.14
- Statistical significance: Yes
- Two-proportion p-value: 0.00000000

### Interpretation

The evidence indicates a material deterioration in search-result availability for the affected station scope during the incident period.

The appropriate operational response is to alert Supply and Search teams when zero-result rates exceed expected route-level baselines and prioritise high-volume affected routes.

## Finding 2 — Mobile checkout incident

For Mobile Web and Android App checkout activity during 13–19 April 2026:

- Baseline checkout error rate: 5.69%
- Incident checkout error rate: 20.66%
- Change: +14.97 percentage points
- Baseline checkout-to-booking conversion: 63.50%
- Incident checkout-to-booking conversion: 54.32%
- Conversion change: -9.18 percentage points
- Estimated lost bookings versus baseline: 187.9
- Estimated revenue impact: £12,557.72
- Statistical significance: Yes
- Two-proportion p-value: 0.00000000

### Interpretation

The checkout deterioration is concentrated in mobile channels rather than representing a platform-wide movement.

This supports prioritising mobile checkout reliability, technical-error instrumentation and automated device-level monitoring.

## Recommended product actions

1. Deploy route-level zero-result monitoring with rolling statistical baselines.
2. Trigger incident investigation when zero-result or checkout-error z-scores exceed defined thresholds.
3. Prioritise mobile checkout technical errors using device, payment method and error-type segmentation.
4. Track commercial impact using counterfactual conversion baselines rather than raw affected-session counts.
5. Maintain reusable investigation marts so analysts can diagnose recurring customer-journey problems quickly.

## Methodology

Customer journey events in RailSearch are synthetic and are not Trainline proprietary data.

Commercial impact estimates are counterfactual analytical estimates based on observed baseline conversion and average booking value. They should not be interpreted as actual Trainline financial results.
