-- Hourly: load items stock-sync published to the stock.sent topic.
CREATE OR REPLACE PROCEDURE load_stock_sent() AS $$
    INSERT INTO stock_sent (sku, qty, sent_at, raw)
    SELECT m.value->>'sku',
           (m.value->>'qty')::INTEGER,
           (m.value->>'updated_at')::TIMESTAMP,
           m.value
    FROM staging_stock_sent m;
$$ LANGUAGE sql;
