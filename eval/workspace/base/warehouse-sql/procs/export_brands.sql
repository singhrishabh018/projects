-- Nightly export for stock-sync: /data/exports/brands.csv
CREATE OR REPLACE PROCEDURE export_brands() AS $$
    COPY (SELECT brand_id, name, CASE WHEN is_searchable THEN 1 ELSE 0 END AS is_searchable,
                 fulfillment_type
          FROM brand)
    TO '/data/exports/brands.csv' WITH CSV HEADER;
$$ LANGUAGE sql;
