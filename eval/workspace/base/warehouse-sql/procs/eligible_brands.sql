-- Nightly export for price-sync: /data/exports/eligible_brands.csv
-- The website-eligibility rule. Keep in sync with the storefront.
CREATE OR REPLACE PROCEDURE export_eligible_brands() AS $$
    COPY (SELECT brand_id FROM brand
          WHERE web_eligible AND status = 'active')
    TO '/data/exports/eligible_brands.csv' WITH CSV HEADER;
$$ LANGUAGE sql;
