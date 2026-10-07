# RailSearch — Data Architecture

## Analytical architecture

Customer session
      |
      v
Journey search
      |
      +----> Zero-result search
      |
      v
Journey results
      |
      v
Journey selected
      |
      v
Checkout
      |
      +----> Checkout error
      |
      +----> Payment failure
      |
      +----> Abandonment
      |
      v
Booking
      |
      v
Revenue

## Core fact-style datasets

### sessions
Digital customer-session context.

### searches
Journey-search behaviour and search-result availability.

### journey_results
Journey options, price, duration and customer selection.

### checkout
Checkout progression, payment attempts and failure modes.

### bookings
Completed transactions and commercial value.

## Reference dataset

### station_reference
Station-level metadata and public rail context.

## Storage strategy

Raw:
Original source or generated files with minimal modification.

Interim:
Validated, standardised and joined working datasets.

Processed:
Analysis-ready customer journey tables and ML feature datasets.

## Planned analytical marts

customer_funnel_daily
conversion_by_device
conversion_by_channel
conversion_by_route
zero_result_analysis
checkout_failure_analysis
commercial_impact
customer_session_features
