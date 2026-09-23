# price-sync

Consumes `price.changed` events and pushes prices to the marketplace partner's price API.
Only brands that are eligible for the website are sent; the eligible list comes from the
nightly warehouse export `eligible_brands.csv` (see `warehouse-sql/procs/eligible_brands.sql`).

Run tests: `python -m unittest discover -s tests`
