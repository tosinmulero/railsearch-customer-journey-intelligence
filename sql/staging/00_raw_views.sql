CREATE OR REPLACE VIEW raw.sessions AS
SELECT *
FROM read_parquet('C:/Users/OLUWATOSIN OLUWASEUN/Downloads/railsearch-customer-journey-intelligence/data/raw/sessions.parquet');

CREATE OR REPLACE VIEW raw.searches AS
SELECT *
FROM read_parquet('C:/Users/OLUWATOSIN OLUWASEUN/Downloads/railsearch-customer-journey-intelligence/data/raw/searches.parquet');

CREATE OR REPLACE VIEW raw.journey_results AS
SELECT *
FROM read_parquet('C:/Users/OLUWATOSIN OLUWASEUN/Downloads/railsearch-customer-journey-intelligence/data/raw/journey_results.parquet');

CREATE OR REPLACE VIEW raw.checkout AS
SELECT *
FROM read_parquet('C:/Users/OLUWATOSIN OLUWASEUN/Downloads/railsearch-customer-journey-intelligence/data/raw/checkout.parquet');

CREATE OR REPLACE VIEW raw.bookings AS
SELECT *
FROM read_parquet('C:/Users/OLUWATOSIN OLUWASEUN/Downloads/railsearch-customer-journey-intelligence/data/raw/bookings.parquet');

CREATE OR REPLACE VIEW raw.station_reference AS
SELECT *
FROM read_parquet('C:/Users/OLUWATOSIN OLUWASEUN/Downloads/railsearch-customer-journey-intelligence/data/raw/station_reference.parquet');
